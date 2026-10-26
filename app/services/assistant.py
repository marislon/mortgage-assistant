from agents import MaxTurnsExceeded, ModelBehaviorError
from pydantic import ValidationError

from app.agents.prompts import assistant_agent
from app.agents.tools import ClientContext
from app.core.config import settings
from app.llm.client import run_agent
from app.schemas.assistant import AssistantAnswer
from app.services import loans
from app.services.json_utils import extract_json
from app.services.money_guard import validate_money

HANDOFF = AssistantAnswer(
    intent="other",
    answer="Не смог разобраться с вопросом, передаю его сотруднику банка.",
    needs_human=True,
    confidence=0,
)

MAX_REPAIR_ATTEMPTS = 2

def get_tool_outputs(result) -> list[str]:
    outputs = []

    for item in result.new_items:
        if item.type == "tool_call_output_item":
            outputs.append(str(item.output))

    return outputs

async def ask(loan_id: int, question: str) -> AssistantAnswer | None:
    if loans.get_loan(loan_id) is None:
        return None

    history = question
    tool_outputs = []

    for attempt in range(MAX_REPAIR_ATTEMPTS + 1):
        try:
            result = await run_agent(
                assistant_agent,
                history,
                ClientContext(loan_id),
            )
        except (MaxTurnsExceeded, ModelBehaviorError):
            return HANDOFF

        tool_outputs.extend(get_tool_outputs(result))

        try:
            answer = AssistantAnswer.model_validate_json(
                extract_json(result.final_output)
            )

            if not validate_money(
                    answer=answer.answer,
                    question=question,
                    tool_outputs=tool_outputs,
            ):
                raise ValueError(
                    "В ответе обнаружены денежные суммы, "
                    "не подтверждённые вопросом клиента "
                    "или результатами инструментов"
                )
            if answer.confidence < settings.agent_confidence_threshold:
                return HANDOFF

            return answer

        except (ValueError, ValidationError) as error:
            if attempt == MAX_REPAIR_ATTEMPTS:
                return HANDOFF

            history = result.to_input_list()
            history.append({
                "role": "user",
                "content": (
                    "Предыдущий ответ не соответствует требуемому формату. "
                    f"Ошибка: {error}. "
                    "Исправь ответ и верни только корректный JSON "
                    "по заданной схеме."
                ),
            })

    return HANDOFF

