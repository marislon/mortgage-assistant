import json
import re

FENCE = re.compile(r"```(?:json)?\s*(.*?)```", re.DOTALL)


def strip_fence(text: str) -> str:
    fenced = FENCE.search(text)
    return fenced.group(1).strip() if fenced else text.strip()


def extract_json(text: str) -> str:
    cleaned = strip_fence(text)

    try:
        json.loads(cleaned)
        return cleaned
    except json.JSONDecodeError:
        pass

    decoder = json.JSONDecoder()

    for position, char in enumerate(cleaned):
        if char not in "{[":
            continue

        try:
            _, end = decoder.raw_decode(cleaned[position:])
            return cleaned[position:position + end]
        except json.JSONDecodeError:
            continue

    raise ValueError(
        "Не удалось извлечь корректный JSON из ответа модели"
    )