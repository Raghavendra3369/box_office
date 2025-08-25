import uuid
from datetime import datetime

from src.models import events, holds, metrics


def generate_request_context(
    request_id: uuid.UUID,
    event_id: uuid.UUID | None = None,
    hold_id: uuid.UUID | None = None,
) -> dict:
    return {"request_id": request_id, "event_id": event_id, "hold_id": hold_id}


def clean_expired_holds() -> None:
    now = datetime.now()
    for event in list(events.values()):
        to_remove = []
        for hold_id in event.active_hold_ids:
            hold = holds[hold_id]
            if now > hold.expires_at:
                to_remove.append(hold_id)
        for hold_id in to_remove:
            hold = holds[hold_id]
            event.held_seats -= hold.qty
            event.active_hold_ids.remove(hold_id)
            del holds[hold_id]
            metrics["total_expiries"] += 1
