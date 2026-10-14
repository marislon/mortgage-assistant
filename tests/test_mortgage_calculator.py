import pytest
from datetime import date
from decimal import Decimal

from app.services.mortgage_calculator import (
    calculate_annuity_payment,
    calculate_payment_schedule,
    early_repayment_reduce_term,
    early_repayment_reduce_payment,
    change_payment_day,
)

def test_annuity_payment():
    payment = calculate_annuity_payment(
        principal_kopecks=15_000_000,
        annual_rate=Decimal("12.5"),
        term_months=240,
    )

    assert payment == 170_421


def test_payment_schedule():
    principal = 15_000_000

    schedule = calculate_payment_schedule(
        principal_kopecks=principal,
        annual_rate=Decimal("12.5"),
        term_months=240,
    )

    assert len(schedule) == 240
    assert schedule[-1]["balance_kopecks"] == 0

    total_principal = sum(
        row["principal_kopecks"] for row in schedule
    )

    assert total_principal == principal


def test_early_repayment_reduce_term():
    schedule = early_repayment_reduce_term(
        principal_kopecks=15_000_000,
        annual_rate=Decimal("12.5"),
        term_months=240,
        after_month=12,
        amount_kopecks=2_000_000,
    )

    assert len(schedule) == 160
    assert schedule[11]["early_repayment_kopecks"] == 2_000_000
    assert schedule[-1]["balance_kopecks"] == 0


def test_early_repayment_reduce_payment():
    schedule = early_repayment_reduce_payment(
        principal_kopecks=15_000_000,
        annual_rate=Decimal("12.5"),
        term_months=240,
        after_month=12,
        amount_kopecks=2_000_000,
    )

    assert len(schedule) == 240
    assert schedule[12]["payment_kopecks"] == 147_422
    assert schedule[-1]["balance_kopecks"] == 0

def test_change_payment_day():
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

    assert updated[0]["payment_date"] == date(2026, 2, 28)
    assert updated[1]["payment_date"] == date(2026, 3, 31)
    assert updated[2]["payment_date"] == date(2026, 4, 30)

    assert len(updated) == 240
    assert updated[-1]["balance_kopecks"] == 0

def test_invalid_loan_parameters():
    with pytest.raises(ValueError):
        calculate_annuity_payment(
            principal_kopecks=-100_000,
            annual_rate=Decimal("12.5"),
            term_months=240,
        )

    with pytest.raises(ValueError):
        calculate_annuity_payment(
            principal_kopecks=15_000_000,
            annual_rate=Decimal("-5"),
            term_months=240,
        )

    with pytest.raises(ValueError):
        calculate_annuity_payment(
            principal_kopecks=15_000_000,
            annual_rate=Decimal("12.5"),
            term_months=0,
        )
