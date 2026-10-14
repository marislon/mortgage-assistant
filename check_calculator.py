
from datetime import date
from decimal import Decimal

from app.services.mortgage_calculator import (
    calculate_payment_schedule,
    change_payment_day,
)

schedule = calculate_payment_schedule(
    principal_kopecks=15_000_000,
    annual_rate=Decimal("12.5"),
    term_months=240,
)

updated = change_payment_day(
    schedule=schedule,
    start_date=date(2026, 1, 15),
    payment_day=31,
)

print("Первые четыре даты платежей:")
for row in updated[:4]:
    print(row["month"], row["payment_date"])

print("\nКоличество платежей:", len(updated))
print("Остаток долга:", updated[-1]["balance_kopecks"])
