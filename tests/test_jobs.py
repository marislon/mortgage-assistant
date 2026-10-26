from app.core import db
from app.services.jobs import create_job


def test_create_job_idempotency():
    key = "test-idempotency-001"

    try:
        first_id = create_job(
            loan_id=1,
            idempotency_key=key,
            job_type="change_payment_day",
            payload={"new_day": 15},
        )

        second_id = create_job(
            loan_id=1,
            idempotency_key=key,
            job_type="change_payment_day",
            payload={"new_day": 20},
        )

        assert first_id == second_id
        with db.connection() as conn:
            cursor = conn.execute(
                "SELECT COUNT(*) FROM jobs WHERE idempotency_key = %s",
                (key,),
            )
            count = cursor.fetchone()[0]

        assert count == 1

        with db.connection() as conn:
            cursor = conn.execute(
                "SELECT payload FROM jobs WHERE idempotency_key = %s",
                (key,),
            )
            saved_payload = cursor.fetchone()[0]

        assert saved_payload == {"new_day": 15}
    finally:
        with db.connection() as conn:
            conn.execute(
                "DELETE FROM jobs WHERE idempotency_key = %s",
                (key,),
            )
