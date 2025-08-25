import datetime


class Event:
    def __init__(self, id: str, name: str, total_seats: int, created_at: datetime):
        self.id = id
        self.name = name
        self.total_seats = total_seats
        self.created_at = created_at
        self.held_seats = 0
        self.booked_seats = 0
        self.active_hold_ids = set()


class Hold:
    def __init__(
        self,
        hold_id: str,
        event_id: str,
        qty: int,
        expires_at: datetime,
        payment_token: str,
    ):
        self.hold_id = hold_id
        self.event_id = event_id
        self.qty = qty
        self.expires_at = expires_at
        self.payment_token = payment_token
        self.booked = False
        self.booking_id = None


class Booking:
    def __init__(self, booking_id: str, event_id: str, qty: int):
        self.booking_id = booking_id
        self.event_id = event_id
        self.qty = qty


events = {}  # type: dict[str, Event]
holds = {}  # type: dict[str, Hold]
bookings = {}  # type: dict[str, Booking]
metrics = {
    "total_events": 0,
    "total_holds": 0,
    "total_bookings": 0,
    "total_expiries": 0,
}
