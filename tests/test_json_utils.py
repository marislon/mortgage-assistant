import pytest

from app.services.json_utils import extract_json


def test_plain_json():
    text = '{"answer": "Ваш платёж рассчитан"}'
    assert extract_json(text) == text


def test_json_in_code_block():
    text = '```json\n{"answer": "Готово"}\n```'
    assert extract_json(text) == '{"answer": "Готово"}'


def test_json_with_extra_text():
    text = 'Вот результат:\n{"answer": "Готово"}\nКонец ответа.'
    assert extract_json(text) == '{"answer": "Готово"}'


def test_invalid_json():
    with pytest.raises(ValueError, match="Не удалось извлечь"):
        extract_json("Это ответ без JSON")
