import json

import pytest
from agents import RunContextWrapper
from agents.tool_context import ToolContext

from app.agents import tools as agent_tools
from app.agents.tools import (
    TOOLS,
    ClientContext,
    request_payment_day_change,
    simulate_early_repayment,
)


def test_model_cannot_choose_loan():
    for tool in TOOLS:
        assert "loan_id" not in json.dumps(tool.params_json_schema)


async def call(tool, loan_id, **args):
    ctx = ToolContext(
        context=ClientContext(loan_id), tool_name=tool.name, tool_call_id="call_1", tool_arguments=json.dumps(args)
    )
    return await tool.on_invoke_tool(ctx, json.dumps(args))


@pytest.mark.asyncio
async def test_simulate_uses_calculator():
    out = await call(simulate_early_repayment, 1, after_month=12, amount_rub=500_000, mode="payment")
    assert out["new_payment"] == "49 477,38 ₽"
    assert out["saved_on_interest"] == "771 538,25 ₽"


def test_context_wrapper_carries_loan():
    assert RunContextWrapper(ClientContext(7)).context.loan_id == 7

@pytest.mark.asyncio
async def test_request_payment_day_change(monkeypatch):
    calls = []

    async def fake_create_application(
        loan_id,
        new_day,
        idempotency_key,
    ):
        calls.append((loan_id, new_day, idempotency_key))
        return {
            "application_id": 100,
            "status": "waiting_employee",
        }

    monkeypatch.setattr(
        agent_tools,
        "create_payment_day_application",
        fake_create_application,
    )

    result = await call(
        request_payment_day_change,
        loan_id=4,
        new_day=25,
    )

    assert result["application_id"] == 100
    assert result["status"] == "waiting_employee"
    assert calls == [
        (4, 25, "agent-payment-day-4-25")
    ]
    result_again = await call(
        request_payment_day_change,
        loan_id=4,
        new_day=25,
    )

    assert result_again == result

    assert calls == [
        (4, 25, "agent-payment-day-4-25"),
        (4, 25, "agent-payment-day-4-25"),
    ]