import uuid

from fastapi import FastAPI, Request
from src.apis import api_router

app = FastAPI()


@app.middleware("http")
async def add_request_id(request: Request, call_next):
    request_id = uuid.uuid4()
    request.state.request_id = request_id
    response = await call_next(request)
    return response


app.include_router(api_router)
