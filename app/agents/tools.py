from dataclasses import dataclass
from typing import Annotated, Literal

from agents import RunContextWrapper, function_tool
from pydantic import Field

from app.services import loans
from app.services.payment_day import validate_payment_day_change
from app.services.payment_day_applications import create_payment_day_application


@dataclass
class ClientContext:
    loan_id: int


def _loan(ctx: RunContextWrapper[ClientContext]):
    loan = loans.get_loan(ctx.context.loan_id)
    if loan is None:
        raise ValueError("кредит не найден")
    return loan


@function_tool(description_override="Условия кредита клиента: сумма, ставка, срок, дата выдачи, день и размер платежа.")
def get_loan(ctx: RunContextWrapper[ClientContext]) -> dict:
    return loans.loan_terms(_loan(ctx))


@function_tool(description_override="Строки графика платежей: дата, платеж, проценты, тело долга, остаток после платежа.")
def get_schedule(
    ctx: RunContextWrapper[ClientContext],
    from_month: Annotated[int, Field(ge=1, description="номер первого платежа")] = 1,
    count: Annotated[int, Field(ge=1, le=12, description="сколько платежей показать")] = 3,
) -> list[dict]:
    return loans.schedule_slice(_loan(ctx), from_month, count)


@function_tool(
    description_override="Посчитать досрочное погашение: новый платеж или срок и экономию на процентах."
)
def simulate_early_repayment(
    ctx: RunContextWrapper[ClientContext],
    after_month: Annotated[int, Field(ge=1, description="номер платежа, после которого вносим деньги")],
    amount_rub: Annotated[int, Field(gt=0, description="сумма досрочного погашения в рублях")],
    mode: Annotated[Literal["term", "payment"], Field(description="term – сократить срок, payment – уменьшить платеж")],
) -> dict:
    return loans.simulate_early_repayment(_loan(ctx), after_month, amount_rub * 100, mode)

@function_tool(
    description_override=(
        "Проверить, может ли клиент изменить день платежа "
        "по ипотечному кредиту."
    )
)
def check_payment_day_change(
    ctx: RunContextWrapper[ClientContext],
    new_day: Annotated[
        int,
        Field(ge=1, le=28, description="Желаемый день платежа"),
    ],
) -> dict:
    loan = _loan(ctx)

    try:
        validate_payment_day_change(
            loan_id=ctx.context.loan_id,
            new_day=new_day,
            current_day=loan.payment_day,
        )
    except ValueError as exc:
        return {
            "eligible": False,
            "reason": str(exc),
        }

    return {
        "eligible": True,
        "reason": "Изменение дня платежа разрешено",
    }

@function_tool(
    description_override=(
        "Подать заявление на изменение дня платежа "
        "по ипотечному кредиту. "
        "Использовать только по явной просьбе клиента."
    )
)
async def request_payment_day_change(
    ctx: RunContextWrapper[ClientContext],
    new_day: Annotated[
        int,
        Field(ge=1, le=28, description="Желаемый день платежа"),
    ],
) -> dict:
    idempotency_key = (
        f"agent-payment-day-{ctx.context.loan_id}-{new_day}"
    )
    try:
        return await create_payment_day_application(
            loan_id=ctx.context.loan_id,
            new_day=new_day,
            idempotency_key=idempotency_key,
        )
    except (ValueError, LookupError) as exc:
        return {
            "success": False,
            "reason": str(exc),
        }

TOOLS = [
    get_loan,
    get_schedule,
    simulate_early_repayment,
    check_payment_day_change,
    request_payment_day_change,
]
