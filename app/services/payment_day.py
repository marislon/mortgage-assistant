from app.core import db


def validate_payment_day(new_day: int, current_day: int) -> None:
    if not 1 <= new_day <= 28:
        raise ValueError(
            "Новый день платежа должен быть от 1 до 28"
        )

    if new_day == current_day:
        raise ValueError(
            "Новый день платежа совпадает с текущим"
        )
def has_recent_payment_day_change(loan_id: int) -> bool:
    with db.connection() as conn:
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
        return cursor.fetchone()[0]

def validate_payment_day_change(
        loan_id: int,
        new_day: int,
        current_day: int,
) -> None:
    validate_payment_day(new_day, current_day)

    if has_recent_payment_day_change(loan_id):
        raise ValueError(
            "Дата платежа уже изменялась за последние 12 месяцев"
        )
