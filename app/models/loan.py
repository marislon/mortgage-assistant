
from datetime import date
from decimal import Decimal

from sqlalchemy import BigInteger, Date, Integer, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class Loan(Base):
    __tablename__ = "loans"

    id: Mapped[int] = mapped_column(
        Integer, primary_key=True
    )

    borrower_name: Mapped[str] = mapped_column(
        String(200), nullable=False
    )

    principal_kopecks: Mapped[int] = mapped_column(
        BigInteger, nullable=False
    )

    annual_rate: Mapped[Decimal] = mapped_column(
        Numeric(7, 4), nullable=False
    )

    term_months: Mapped[int] = mapped_column(
        Integer, nullable=False
    )

    start_date: Mapped[date] = mapped_column(
        Date, nullable=False
    )
