
from fastapi import FastAPI

app = FastAPI(title="Mortgage Assistant")


@app.get("/live")
async def live():
    return {"status": "alive"}

from fastapi import HTTPException
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

from app.core.db import engine


@app.get("/ready")
async def ready():
    try:
        async with engine.connect() as connection:
            await connection.execute(text("SELECT 1"))
    except SQLAlchemyError:
        raise HTTPException(
            status_code=503,
            detail="Database unavailable",
        )

    return {"status": "ready"}
