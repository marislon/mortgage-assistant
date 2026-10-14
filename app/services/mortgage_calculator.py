import calendar
from datetime import date
from decimal import Decimal, ROUND_HALF_UP

def calculate_annuity_payment(
    principal_kopecks: int,
    annual_rate: Decimal,
    term_months: int,
) -> int:
    if principal_kopecks <= 0:
        raise ValueError("Сумма кредита должна быть положительной")

    if annual_rate < 0:
        raise ValueError("Процентная ставка не может быть отрицательной")

    if term_months <= 0:
        raise ValueError("Срок кредита должен быть положительным")

    if annual_rate == 0:
        payment = Decimal(principal_kopecks) / term_months
    else:
        monthly_rate = annual_rate / Decimal("1200")
        factor = (1 + monthly_rate) ** term_months

        payment = (
            Decimal(principal_kopecks)
            * monthly_rate
            * factor
            / (factor - 1)
        )

    return int(payment.quantize(Decimal("1"), rounding=ROUND_HALF_UP))

def calculate_payment_schedule(
    principal_kopecks: int,
    annual_rate: Decimal,
    term_months: int,
) -> list[dict]:
    payment = calculate_annuity_payment(
        principal_kopecks,
        annual_rate,
        term_months,
    )

    monthly_rate = annual_rate / Decimal("1200")
    balance = principal_kopecks
    schedule = []

    for month in range(1, term_months + 1):
        interest = int(
            (Decimal(balance) * monthly_rate).quantize(
                Decimal("1"),
                rounding=ROUND_HALF_UP,
            )
        )

        if month == term_months:
            principal_payment = balance
        else:
            principal_payment = min(payment - interest, balance)

        actual_payment = interest + principal_payment
        balance -= principal_payment

        schedule.append({
            "month": month,
            "payment_kopecks": actual_payment,
            "interest_kopecks": interest,
            "principal_kopecks": principal_payment,
            "balance_kopecks": balance,
        })

        if balance == 0:
            break

    return schedule

def validate_early_repayment(
    amount_kopecks: int,
    after_month: int,
    term_months: int,
) -> None:
    if amount_kopecks <= 0:
        raise ValueError(
            "Сумма досрочного погашения должна быть положительной"
        )

    if not 1 <= after_month < term_months:
        raise ValueError(
            "Месяц досрочного погашения должен быть "
            "от 1 до предпоследнего месяца кредита"
        )

def early_repayment_reduce_term(
        principal_kopecks: int,
        annual_rate: Decimal,
        term_months: int,
        after_month: int,
        amount_kopecks: int,
) -> list[dict]:
    validate_early_repayment(
        amount_kopecks, after_month, term_months
    )

    schedule = calculate_payment_schedule(
        principal_kopecks, annual_rate, term_months
    )

    if after_month > len(schedule):
        raise ValueError("Кредит уже погашен")

    result = schedule[:after_month]
    balance = result[-1]["balance_kopecks"]

    if balance == 0:
        raise ValueError("Кредит уже погашен")

    repayment = min(amount_kopecks, balance)
    balance -= repayment

    result[-1] = {
        **result[-1],
        "early_repayment_kopecks": repayment,
        "balance_kopecks": balance,
    }

    if balance == 0:
        return result

    payment = calculate_annuity_payment(
        principal_kopecks, annual_rate, term_months
    )
    monthly_rate = annual_rate / Decimal("1200")

    month = after_month

    while balance > 0:
        month += 1

        interest = int(
            (Decimal(balance) * monthly_rate).quantize(
                Decimal("1"), rounding=ROUND_HALF_UP
            )
        )

        principal_payment = min(
            payment - interest, balance
        )
        actual_payment = interest + principal_payment
        balance -= principal_payment

        result.append({
            "month": month,
            "payment_kopecks": actual_payment,
            "interest_kopecks": interest,
            "principal_kopecks": principal_payment,
            "early_repayment_kopecks": 0,
            "balance_kopecks": balance,
        })

    return result


def early_repayment_reduce_payment(
    principal_kopecks: int,
    annual_rate: Decimal,
    term_months: int,
    after_month: int,
    amount_kopecks: int,
) -> list[dict]:
    validate_early_repayment(
        amount_kopecks, after_month, term_months
    )

    original = calculate_payment_schedule(
        principal_kopecks, annual_rate, term_months
    )

    result = original[:after_month]
    balance = result[-1]["balance_kopecks"]

    if balance == 0:
        raise ValueError("Кредит уже погашен")

    repayment = min(amount_kopecks, balance)
    balance -= repayment

    result[-1] = {
        **result[-1],
        "early_repayment_kopecks": repayment,
        "balance_kopecks": balance,
    }

    if balance == 0:
        return result

    remaining_months = term_months - after_month

    new_schedule = calculate_payment_schedule(
        balance,
        annual_rate,
        remaining_months,
    )

    for row in new_schedule:
        result.append({
            **row,
            "month": row["month"] + after_month,
            "early_repayment_kopecks": 0,
        })

    return result


def change_payment_day(
    schedule: list[dict],
    start_date: date,
    payment_day: int,
) -> list[dict]:
    if not 1 <= payment_day <= 31:
        raise ValueError("День платежа должен быть от 1 до 31")

    result = []

    for row in schedule:
        month_index = start_date.month - 1 + row["month"]
        year = start_date.year + month_index // 12
        month = month_index % 12 + 1

        last_day = calendar.monthrange(year, month)[1]
        day = min(payment_day, last_day)

        result.append({
            **row,
            "payment_date": date(year, month, day),
        })

    return result
