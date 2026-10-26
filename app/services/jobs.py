from psycopg.types.json import Jsonb

from app.core import db


def create_job(
    loan_id: int,
    idempotency_key: str,
    job_type: str,
    payload: dict,
) -> int:
    with db.connection() as conn:
        cursor = conn.execute(
            """
            INSERT INTO jobs (loan_id, idempotency_key, job_type, payload)
            VALUES (%s, %s, %s, %s)
            ON CONFLICT (idempotency_key) DO NOTHING
            RETURNING id
            """,
            (loan_id, idempotency_key, job_type, Jsonb(payload)),
        )
        row = cursor.fetchone()
        if row is not None:
            return row[0]
        cursor = conn.execute(
            """
            SELECT id
            FROM jobs
            WHERE idempotency_key = %s
            """,
            (idempotency_key,),
        )
        row = cursor.fetchone()

        if row is None:
            raise RuntimeError("Не удалось найти созданную операцию")

        return row[0]

def claim_job(job_id: int) -> bool:
    with db.connection() as conn:
        cursor = conn.execute(
            """
            UPDATE jobs
            SET status = 'running',
                started_at = NOW()
            WHERE id = %s
              AND status = 'pending'
            RETURNING id
            """,
            (job_id,),
        )

        return cursor.fetchone() is not None
