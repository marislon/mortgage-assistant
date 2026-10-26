from types import SimpleNamespace

import pytest
from agents import MaxTurnsExceeded
from fastapi.testclient import TestClient

from app.main import app
from app.schemas.assistant import AssistantAnswer
from app.services import assistant

client = TestClient(app)

ANSWER = AssistantAnswer(intent="early_repayment", answer="Расчёт выполнен успешно", confidence=0.9)


@pytest.fixture
def fake_agent(monkeypatch):
    calls = []

    async def run(agent, prompt, context=None):
        calls.append(context)
        return SimpleNamespace(
            final_output=ANSWER.model_dump_json(),
            new_items=[],
        )

    monkeypatch.setattr(assistant, "run_agent", run)
    return calls


def test_ask_passes_loan_in_context(fake_agent):
    resp = client.post("/ask", json={"loan_id": 1, "question": "Какой будет платеж после досрочки?"})
    assert resp.status_code == 200
    assert resp.json()["answer"] == ANSWER.answer
    assert fake_agent[0].loan_id == 1


def test_ask_unknown_loan(fake_agent):
    assert client.post("/ask", json={"loan_id": 999999, "question": "?"}).status_code == 404
    assert fake_agent == []


def test_turn_budget_goes_to_human(monkeypatch):
    async def run(agent, prompt, context=None):
        raise MaxTurnsExceeded("6 ходов")

    monkeypatch.setattr(assistant, "run_agent", run)
    body = client.post("/ask", json={"loan_id": 1, "question": "..."}).json()
    assert body["needs_human"] is True


def test_answer_not_in_format(monkeypatch):
    calls = []

    async def run(agent, prompt, context=None):
        calls.append(prompt)

        return SimpleNamespace(
            final_output="Новый платеж составит **49 477,38 ₽**.",
            new_items=[],
            to_input_list=lambda: [
                {"role": "user", "content": "Первоначальный вопрос"},
                {
                    "role": "assistant",
                    "content": "Новый платеж составит **49 477,38 ₽**.",
                },
            ],
        )

    monkeypatch.setattr(assistant, "run_agent", run)

    response = client.post(
        "/ask",
        json={"loan_id": 1, "question": "..."},
    )

    assert response.status_code == 200
    assert response.json()["needs_human"] is True
    assert len(calls) == 3
    assert isinstance(calls[1], list)
    assert "Ошибка:" in calls[1][-1]["content"]


def test_fenced_answer_is_accepted(monkeypatch):
    async def run(agent, prompt, context=None):
        return SimpleNamespace(
            final_output="```json\n" + ANSWER.model_dump_json() + "\n```",
            new_items=[],
        )

    monkeypatch.setattr(assistant, "run_agent", run)
    assert client.post("/ask", json={"loan_id": 1, "question": "..."}).json()["answer"] == ANSWER.answer

def test_answer_repaired_on_second_attempt(monkeypatch):
    calls = []

    async def run(agent, prompt, context=None):
        calls.append(prompt)

        if len(calls) == 1:
            return SimpleNamespace(
                final_output="Ответ без JSON",
                new_items=[],
                to_input_list=lambda: [
                    {"role": "user", "content": "Вопрос клиента"},
                    {"role": "assistant", "content": "Ответ без JSON"},
                ],
            )

        return SimpleNamespace(
            final_output=ANSWER.model_dump_json(),
            new_items=[],
        )

    monkeypatch.setattr(assistant, "run_agent", run)

    response = client.post(
        "/ask",
        json={"loan_id": 1, "question": "Какой будет платёж?"},
    )

    assert response.status_code == 200
    assert response.json()["answer"] == ANSWER.answer
    assert response.json()["needs_human"] is False
    assert len(calls) == 2
    assert isinstance(calls[1], list)
    assert "Ошибка:" in calls[1][-1]["content"]

    def test_answer_repaired_on_second_attempt(monkeypatch):
        calls = []

        async def run(agent, prompt, context=None):
            calls.append(prompt)

            if len(calls) == 1:
                return SimpleNamespace(
                    final_output="Ответ без JSON",
                    new_items=[],
                    to_input_list=lambda: [
                        {"role": "user", "content": "Вопрос клиента"},
                        {"role": "assistant", "content": "Ответ без JSON"},
                    ],
                )

            return SimpleNamespace(
                final_output=ANSWER.model_dump_json(),
                new_items=[],
            )

        monkeypatch.setattr(assistant, "run_agent", run)

        response = client.post(
            "/ask",
            json={"loan_id": 1, "question": "Какой будет платёж?"},
        )

        assert response.status_code == 200
        assert response.json()["answer"] == ANSWER.answer
        assert response.json()["needs_human"] is False
        assert len(calls) == 2
        assert isinstance(calls[1], list)
        assert "Ошибка:" in calls[1][-1]["content"]

def test_pydantic_error_repaired(monkeypatch):
    calls = []

    invalid_answer = (
        '{"intent": "unknown", '
        '"answer": "Ваш платёж рассчитан", '
        '"confidence": 1.5}'
    )

    async def run(agent, prompt, context=None):
        calls.append(prompt)

        if len(calls) == 1:
            return SimpleNamespace(
                final_output=invalid_answer,
                new_items=[],
                to_input_list=lambda: [
                    {"role": "user", "content": "Вопрос клиента"},
                    {"role": "assistant", "content": invalid_answer},
                ],
            )

        return SimpleNamespace(
            final_output=ANSWER.model_dump_json(),
            new_items=[],
        )

    monkeypatch.setattr(assistant, "run_agent", run)

    response = client.post(
        "/ask",
        json={"loan_id": 1, "question": "Рассчитай платёж"},
    )

    assert response.status_code == 200
    assert response.json()["answer"] == ANSWER.answer
    assert response.json()["needs_human"] is False
    assert len(calls) == 2
    assert "Ошибка:" in calls[1][-1]["content"]

def test_invented_money_goes_to_human(monkeypatch):
    calls = []

    async def run(agent, prompt, context=None):
        calls.append(prompt)

        return SimpleNamespace(
            final_output=AssistantAnswer(
                intent="early_repayment",
                answer="Новый платёж составит 1 800 ₽",
                confidence=0.9,
            ).model_dump_json(),
            new_items=[
                SimpleNamespace(
                    type="tool_call_output_item",
                    output='{"new_payment": "1 500,00 ₽"}',
                )
            ],
            to_input_list=lambda: [
                {"role": "user", "content": "Какой будет платёж?"},
                {
                    "role": "assistant",
                    "content": "Новый платёж составит 1 800 ₽",
                },
            ],
        )

    monkeypatch.setattr(assistant, "run_agent", run)

    response = client.post(
        "/ask",
        json={"loan_id": 1, "question": "Какой будет платёж?"},
    )

    assert response.status_code == 200
    assert response.json()["needs_human"] is True
    assert len(calls) == 3
    assert "денежные суммы" in calls[1][-1]["content"]

def test_verified_money_is_accepted(monkeypatch):
    calls = []

    async def run(agent, prompt, context=None):
        calls.append(prompt)

        return SimpleNamespace(
            final_output=AssistantAnswer(
                intent="early_repayment",
                answer="Новый платёж составит 1 500 ₽",
                confidence=0.9,
            ).model_dump_json(),
            new_items=[
                SimpleNamespace(
                    type="tool_call_output_item",
                    output='{"new_payment": "1 500,00 ₽"}',
                )
            ],
        )

    monkeypatch.setattr(assistant, "run_agent", run)

    response = client.post(
        "/ask",
        json={
            "loan_id": 1,
            "question": "Какой будет платёж после досрочного погашения?",
        },
    )

    assert response.status_code == 200
    assert response.json()["needs_human"] is False
    assert response.json()["answer"] == "Новый платёж составит 1 500 ₽"
    assert len(calls) == 1

def test_low_confidence_goes_to_human(monkeypatch):
    calls = []

    async def run(agent, prompt, context=None):
        calls.append(prompt)

        return SimpleNamespace(
            final_output=AssistantAnswer(
                intent="schedule",
                answer="Ваш график платежей доступен",
                confidence=0.5,
            ).model_dump_json(),
            new_items=[],
        )

    monkeypatch.setattr(assistant, "run_agent", run)

    response = client.post(
        "/ask",
        json={
            "loan_id": 1,
            "question": "Где посмотреть график платежей?",
        },
    )

    assert response.status_code == 200
    assert response.json()["needs_human"] is True
    assert response.json()["confidence"] == 0
    assert len(calls) == 1

def test_confidence_equal_threshold_is_accepted(monkeypatch):
    calls = []

    async def run(agent, prompt, context=None):
        calls.append(prompt)

        return SimpleNamespace(
            final_output=AssistantAnswer(
                intent="schedule",
                answer="Ваш график платежей доступен",
                confidence=0.7,
            ).model_dump_json(),
            new_items=[],
        )

    monkeypatch.setattr(assistant, "run_agent", run)

    response = client.post(
        "/ask",
        json={
            "loan_id": 1,
            "question": "Где посмотреть график платежей?",
        },
    )

    assert response.status_code == 200
    assert response.json()["needs_human"] is False
    assert response.json()["confidence"] == 0.7
    assert len(calls) == 1
