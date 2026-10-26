from temporalio import activity

from app.core import db


@activity.defn
def save_payment_day_decision(
    application_id: int,
    decision: str,
) -> None:
    if decision not in ("approved", "rejected"):
        raise ValueError(
            f"Недопустимое решение сотрудника: {decision}"
        )
    status = (
        "completed"
        if decision == "approved"
        else "failed"
    )

    with db.connection() as conn, conn.transaction():
        cursor = conn.execute(
            """
                SELECT loan_id, status, payload
                FROM jobs
                WHERE id = %s
                FOR UPDATE
                """,
            (application_id,),
        )
        job = cursor.fetchone()
        if job is None:
            raise ValueError(
                f"Заявление {application_id} не найдено"
            )

        loan_id, current_status, payload = job

        # Если заявление уже обработано, ничего не делаем
        if current_status in ("completed", "failed"):
            return

        # Проверяем, что заявление ожидает решения сотрудника
        if current_status != "waiting_employee":
            raise ValueError(
                f"Нельзя обработать заявление {application_id}: "
                f"текущий статус — {current_status}"
            )
        if decision == "rejected":
            conn.execute(
                """
                    UPDATE jobs
                    SET status = 'failed',
                        result = %s::jsonb,
                        updated_at = NOW()
                    WHERE id = %s
                    """,
                ('{"decision": "rejected"}', application_id),
            )
            return

        new_day = payload.get("new_day")

        if not isinstance(new_day, int) or isinstance(new_day, bool):
            raise TypeError(
                "В заявлении отсутствует корректный new_day"
            )

        if not 1 <= new_day <= 28:
            raise ValueError(
                "Новый день платежа должен быть от 1 до 28"
            )

        cursor = conn.execute(
            """
                SELECT payment_day
                FROM loans
                WHERE id = %s
                FOR UPDATE
                """,
            (loan_id,),
        )

        loan = cursor.fetchone()

        if loan is None:
            raise ValueError(
                f"Кредит {loan_id} не найден"
            )

        old_day = loan[0]
        if new_day == old_day:
            raise ValueError(
                f"Новый день платежа ({new_day}) "
                f"совпадает с текущим ({old_day})"
            )
        cursor = conn.execute(
            """
                SELECT EXISTS (
                    SELECT 1
                    FROM payment_day_changes
                    WHERE loan_id = %s
                      AND changed_at > NOW() - INTERVAL '12 months'
                )
                """,
            (loan_id,),
        )

        has_recent_change = cursor.fetchone()[0]

        if has_recent_change:
            raise ValueError(
                f"По кредиту {loan_id} день платежа "
                "уже изменялся за последние 12 месяцев"
            )
        if decision == "approved":
            conn.execute(
                """
                    UPDATE loans
                    SET payment_day = %s
                    WHERE id = %s
                    """,
                (new_day, loan_id),
            )
            conn.execute(
                """
                    INSERT INTO payment_day_changes (
                        loan_id,
                        old_day,
                        new_day
                    )
                    VALUES (%s, %s, %s)
                    """,
                (loan_id, old_day, new_day),
            )

        conn.execute(
            """
                UPDATE jobs
                SET status = %s,
                    result = %s::jsonb,
                    updated_at = NOW()
                WHERE id = %s
                """,
            (
                status,
                '{"decision": "' + decision + '"}',
                application_id,
            ),
        )
