from temporalio.client import Client
from temporalio.exceptions import WorkflowAlreadyStartedError

from app.core import db
from app.services.jobs import create_job
from app.services.payment_day import validate_payment_day_change
from app.workflows.payment_day import PaymentDayChangeWorkflow


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

async def create_payment_day_application(
    loan_id: int,
    new_day: int,
    idempotency_key: str,
) -> dict:
    existing_job = get_job_by_idempotency_key(idempotency_key)

    if existing_job is not None:
        job_id, existing_loan_id, job_type, payload = existing_job

        if (
            existing_loan_id != loan_id
            or job_type != "payment_day_change"
            or payload.get("new_day") != new_day
        ):
            raise ValueError(
                "Ключ идемпотентности уже использован с другими параметрами"
            )

        return {
            "application_id": job_id,
            "status": get_application_status(job_id),
        }

    current_day = get_current_payment_day(loan_id)

    if current_day is None:
        raise LookupError("Кредит не найден")

    validate_payment_day_change(
        loan_id=loan_id,
        new_day=new_day,
        current_day=current_day,
    )
    job_id = create_job(
        loan_id=loan_id,
        idempotency_key=idempotency_key,
        job_type="payment_day_change",
        payload={"new_day": new_day},
    )
    with db.connection() as conn:
        conn.execute(
            """
            UPDATE jobs
            SET status = 'waiting_employee',
                updated_at = NOW()
            WHERE id = %s
              AND status = 'pending'
            """,
            (job_id,),
        )
    client = await Client.connect("localhost:7233")

    try:
        await client.start_workflow(
            PaymentDayChangeWorkflow.run,
            job_id,
            id=f"payment-day-{job_id}",
            task_queue="payment-day",
        )
    except WorkflowAlreadyStartedError:
        pass

    return {
        "application_id": job_id,
        "status": get_application_status(job_id),
    }
