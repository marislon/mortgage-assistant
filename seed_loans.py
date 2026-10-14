
import asyncio
from datetime import date
from decimal import Decimal

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import async_session_factory
from app.models.loan import Loan


async def main():
    loans = [
        Loan(
            borrower_name="Иван Петров",
            principal_kopecks=15_000_000,
            annual_rate=Decimal("12.5"),
            term_months=240,
            start_date=date(2025, 1, 15),
        ),
        Loan(
            borrower_name="Мария Иванова",
            principal_kopecks=25_000_000,
            annual_rate=Decimal("10.0"),
            term_months=180,
            start_date=date(2025, 3, 10),
        ),
        Loan(
            borrower_name="Алексей Смирнов",
            principal_kopecks=8_000_000,
            annual_rate=Decimal("14.0"),
            term_months=120,
            start_date=date(2025, 6, 5),
        ),
        Loan(
            borrower_name="Елена Кузнецова",
            principal_kopecks=35_000_000,
            annual_rate=Decimal("9.5"),
            term_months=300,
            start_date=date(2026, 1, 20),
        ),
        Loan(
            borrower_name="Дмитрий Соколов",
            principal_kopecks=12_000_000,
            annual_rate=Decimal("11.0"),
            term_months=240,
            start_date=date(2026, 4, 12),
        ),
    ]

    async with async_session_factory() as session:
        session.add_all(loans)
        await session.commit()

    print("Добавлено 5 учебных кредитов")


if __name__ == "__main__":
    asyncio.run(main())
