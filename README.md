Box office

Apis created:
1. Create Event - /events
   - Creates event by taking event name and total_seats
   - Returns unique event_id
2. Create Holds - /holds
   - Creates of hold of min(quantity, available_seats) for event
   - returns unique hold_id and payment_token
3. Book Hold - /book
   - books hold if hold and payment_token is valid and hold is not expired or not already booked
   - returns unique book_id
4. Get Event Details - /events/{event_id}
   - returns details of the event
5. Get Metrics - /metrics
   - return aggregated details of all events

Steps to set up:
1. Clone the project from git
   git clone https://github.com/Raghavendra3369/box_office.git
2. Run docker in box_office directory
   docker compose up

Note: Storing everything in In-Memory instead of database so data will be lost if docker is restarted.