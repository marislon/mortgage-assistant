import re
from decimal import Decimal

MONEY_PATTERN = re.compile(
    r"(?<!\d)(\d[\d \u00a0\u202f]*)(?:[,.](\d{1,2}))?"
    r"\s*(?:₽|руб(?:лей|ля|ль|\.|я)?)",
    re.IGNORECASE,
)


def extract_money(text: str) -> set[Decimal]:
    amounts = set()

    for match in MONEY_PATTERN.finditer(text):
        rubles = match.group(1).replace(" ", "").replace("\u00a0", "").replace("\u202f", "")
        kopecks = (match.group(2) or "0").ljust(2, "0")

        amount = Decimal(rubles) + Decimal(kopecks) / 100
        amounts.add(amount)

    return amounts

def validate_money(
    answer: str,
    question: str,
    tool_outputs: list[str],
) -> bool:
    answer_amounts = extract_money(answer)

    allowed_amounts = extract_money(question)

    for output in tool_outputs:
        allowed_amounts.update(extract_money(output))

    return answer_amounts.issubset(allowed_amounts)
