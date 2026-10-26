from decimal import Decimal

from app.services.money_guard import extract_money


def test_formatted_rubles():
    assert extract_money("Платёж 1 500,00 ₽") == {
        Decimal("1500.00")
    }


def test_rubles_without_spaces():
    assert extract_money("Платёж 1500 рублей") == {
        Decimal("1500.00")
    }


def test_rubles_with_kopecks():
    assert extract_money("Экономия 1 800,50 руб.") == {
        Decimal("1800.50")
    }


def test_multiple_amounts():
    text = "Платёж 1 500 ₽, экономия 2 300 рублей"
    assert extract_money(text) == {
        Decimal("1500.00"),
        Decimal("2300.00"),
    }


def test_numbers_without_currency():
    text = "Срок 240 месяцев, ставка 12%, день платежа 15"
    assert extract_money(text) == set()

from app.services.money_guard import validate_money


def test_money_from_tool_is_allowed():
    assert validate_money(
        answer="Новый платёж составит 1 500 ₽",
        question="Какой будет новый платёж?",
        tool_outputs=['{"new_payment": "1 500,00 ₽"}'],
    ) is True


def test_invented_money_is_rejected():
    assert validate_money(
        answer="Новый платёж составит 1 800 ₽",
        question="Какой будет новый платёж?",
        tool_outputs=['{"new_payment": "1 500,00 ₽"}'],
    ) is False


def test_money_from_question_is_allowed():
    assert validate_money(
        answer="Вы хотите внести 20 000 рублей",
        question="Хочу досрочно погасить 20 000 ₽",
        tool_outputs=[],
    ) is True


def test_answer_without_money_is_allowed():
    assert validate_money(
        answer="Ваш график платежей подготовлен",
        question="Покажи график платежей",
        tool_outputs=[],
    ) is True
