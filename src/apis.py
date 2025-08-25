import uuid
from datetime import datetime, timedelta
import logging
from fastapi import HTTPException, Request, APIRouter
import asyncio

from src.utils import generate_request_context, clean_expired_holds
from src.schemas import CreateEventRequest, HoldRequest, BookRequest
from src.models import events, holds, metrics, bookings, Hold, Event, Booking

from src.settings import HOLD_TIMEOUT

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s request_id=%(request_id)s event_id=%(event_id)s hold_id=%(hold_id)s %(message)s",
    handlers=[logging.StreamHandler()],
)
logger = logging.getLogger(__name__)

api_router = APIRouter()

global_lock = asyncio.Lock()


@api_router.post("/events")
async def create_event(req: CreateEventRequest, request: Request):
    request_id = request.state.request_id
    async with global_lock:
        event_id = str(uuid.uuid4())
        created_at = datetime.now()
        event = Event(event_id, req.name, req.total_seats, created_at)
        events[event_id] = event
        metrics["total_events"] += 1
        logger.info(
            "Event created", extra=generate_request_context(request_id, event_id)
        )
        return {
            "event_id": event_id,
            "total_seats": req.total_seats,
            "created_at": created_at.isoformat(),
        }


@api_router.post("/holds")
async def create_hold(req: HoldRequest, request: Request):
    request_id = request.state.request_id
    event_id = req.event_id
    qty = req.qty
    async with global_lock:
        if event_id not in events:
            logger.error(
                "Event not found", extra=generate_request_context(request_id, event_id)
            )
            raise HTTPException(404, "Event not found")
        event = events[event_id]

        # Clean expired holds for all events
        clean_expired_holds()

        available = event.total_seats - event.held_seats - event.booked_seats
        if available == 0:
            logger.error(
                "No seats available",
                extra=generate_request_context(request_id, event_id),
            )
            raise HTTPException(400, "No seats available")
        qty_to_hold = min(qty, available)  # Partial fulfillment

        hold_id = str(uuid.uuid4())
        payment_token = str(uuid.uuid4())
        expires_at = datetime.now() + timedelta(seconds=HOLD_TIMEOUT)
        hold = Hold(hold_id, event_id, qty_to_hold, expires_at, payment_token)
        holds[hold_id] = hold
        event.held_seats += qty_to_hold
        event.active_hold_ids.add(hold_id)
        metrics["total_holds"] += 1

        logger.info(
            f"Hold created for {qty_to_hold} seats",
            extra=generate_request_context(request_id, event_id, hold_id),
        )
        return {
            "hold_id": hold_id,
            "expires_at": expires_at.isoformat(),
            "payment_token": payment_token,
            "qty_held": qty_to_hold,
        }


@api_router.post("/book")
async def book(req: BookRequest, request: Request):
    request_id = request.state.request_id
    hold_id = req.hold_id

    async with global_lock:
        if hold_id not in holds:
            logger.error(
                "Hold not found",
                extra=generate_request_context(request_id, hold_id=hold_id),
            )
            raise HTTPException(404, "Hold not found")
        hold = holds[hold_id]
        if hold.payment_token != req.payment_token:
            logger.error(
                "Invalid payment token",
                extra=generate_request_context(request_id, hold.event_id, hold_id),
            )
            raise HTTPException(400, "Invalid payment token")
        if datetime.now() > hold.expires_at:
            logger.error(
                "Hold expired",
                extra=generate_request_context(request_id, hold.event_id, hold_id),
            )
            raise HTTPException(400, "Hold expired")

        event = events[hold.event_id]
        clean_expired_holds()

        if hold_id not in event.active_hold_ids:
            logger.error(
                "Hold expired or invalid",
                extra=generate_request_context(request_id, hold.event_id, hold_id),
            )
            raise HTTPException(400, "Hold expired or invalid")
        if hold.booked:
            logger.info(
                "Booking already exists",
                extra=generate_request_context(request_id, hold.event_id, hold_id),
            )
            return {"booking_id": hold.booking_id}

        booking_id = str(uuid.uuid4())
        hold.booked = True
        hold.booking_id = booking_id
        booking = Booking(booking_id, hold.event_id, hold.qty)
        bookings[booking_id] = booking
        event.held_seats -= hold.qty
        event.booked_seats += hold.qty
        event.active_hold_ids.remove(hold_id)
        metrics["total_bookings"] += 1

        logger.info(
            "Booking confirmed",
            extra=generate_request_context(request_id, hold.event_id, hold_id),
        )
        return {"booking_id": booking_id}


@api_router.get("/events/{event_id}")
async def get_event(event_id: str, request: Request):
    request_id = request.state.request_id

    async with global_lock:
        if event_id not in events:
            logger.error(
                "Event not found", extra=generate_request_context(request_id, event_id)
            )
            raise HTTPException(404, "Event not found")
        event = events[event_id]
        clean_expired_holds()
        available = event.total_seats - event.held_seats - event.booked_seats
        logger.info(
            "Event snapshot retrieved",
            extra=generate_request_context(request_id, event_id),
        )
        return {
            "total": event.total_seats,
            "available": available,
            "held": event.held_seats,
            "booked": event.booked_seats,
        }


@api_router.get("/metrics")
async def get_metrics(request: Request):
    request_id = request.state.request_id

    async with global_lock:
        clean_expired_holds()
        logger.info("Metrics retrieved", extra=generate_request_context(request_id))
        return metrics
