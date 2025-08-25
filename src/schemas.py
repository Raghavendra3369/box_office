from pydantic import BaseModel, Field


class CreateEventRequest(BaseModel):
    name: str
    total_seats: int = Field(gt=0)


class HoldRequest(BaseModel):
    event_id: str
    qty: int = Field(gt=0)


class BookRequest(BaseModel):
    hold_id: str
    payment_token: str
