from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.core import db
from app.core.logging import setup_logging
from app.routers import assistant, health, loans, payment_day


@asynccontextmanager
async def lifespan(app: FastAPI):
    setup_logging()
    yield
    db.close_pool()


app = FastAPI(title="mortgage-assistant", lifespan=lifespan)
app.include_router(health.router)
app.include_router(loans.router)
app.include_router(assistant.router)
app.include_router(payment_day.router)