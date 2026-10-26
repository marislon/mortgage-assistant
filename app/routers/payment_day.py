from typing import Literal

from fastapi import APIRouter, Header, HTTPException
from pydantic import BaseModel, Field
from temporalio.client import Client

from app.core import db
from app.services.payment_day_applications import create_payment_day_application

router = APIRouter(
    tags=["Payment Day"],
)

class PaymentDayApplicationRequest(BaseModel):
    loan_id: int = Field(gt=0)
    new_day: int = Field(ge=1, le=28)


class PaymentDayDecisionRequest(BaseModel):
    decision: Literal["approved", "rejected"]

def get_current_payment_day(loan_id: int) -> int | None:
    with db.connection() as conn:
        cursor = conn.execute(
            """
            SELECT payment_day
            FROM loans
            WHERE id = %s
            """,
            (loan_id,),
        )

        row = cursor.fetchone()

    return row[0] if row is not None else None

def get_application_status(job_id: int) -> str | None:
    with db.connection() as conn:
        cursor = conn.execute(
            """
            SELECT status
            FROM jobs
            WHERE id = %s
            """,
            (job_id,),
        )

        row = cursor.fetchone()

    return row[0] if row is not None else None

@router.post("/applications/payment-day", status_code=201)
async def create_application(
    request: PaymentDayApplicationRequest,
    idempotency_key: str = Header(alias="Idempotency-Key"),
):
    try:
        return await create_payment_day_application(
            loan_id=request.loan_id,
            new_day=request.new_day,
            idempotency_key=idempotency_key,
        )
    except LookupError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ValueError as exc:
        status_code = (
            409
            if "Ключ идемпотентности" in str(exc)
            else 400
        )
        raise HTTPException(
            status_code=status_code,
            detail=str(exc),
        ) from exc
def get_job_by_idempotency_key(key: str):
    with db.connection() as conn:
        cursor = conn.execute(
            """
            SELECT id, loan_id, job_type, payload
            FROM jobs
            WHERE idempotency_key = %s
            """,
            (key,),
        )

        return cursor.fetchone()

@router.get("/jobs/{application_id}")
def read_application(application_id: int):
    with db.connection() as conn:
        cursor = conn.execute(
            """
            SELECT id, loan_id, status, payload, result
            FROM jobs
            WHERE id = %s
              AND job_type = 'payment_day_change'
            """,
            (application_id,),
        )
        row = cursor.fetchone()

    if row is None:
        raise HTTPException(
            status_code=404,
            detail="Заявление не найдено",
        )

    job_id, loan_id, status, payload, result = row

    return {
        "application_id": job_id,
        "loan_id": loan_id,
        "status": status,
        "new_day": payload.get("new_day"),
        "result": result,
    }
@router.post("/applications/{application_id}/decision")
async def submit_application_decision(
    application_id: int,
    request: PaymentDayDecisionRequest,
):
    status = get_application_status(application_id)

    if status is None:
        raise HTTPException(
            status_code=404,
            detail="Заявление не найдено",
        )

    if status != "waiting_employee":
        raise HTTPException(
            status_code=409,
            detail="Заявление не ожидает решения сотрудника",
        )

    client = await Client.connect("localhost:7233")

    handle = client.get_workflow_handle(
        f"payment-day-{application_id}"
    )

    await handle.execute_update(
        "submit_decision",
        request.decision,
    )

    return {
        "application_id": application_id,
        "decision": request.decision,
        "message": "Решение передано в Temporal",
    }
