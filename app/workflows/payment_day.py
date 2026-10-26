from datetime import timedelta

from temporalio import workflow


@workflow.defn
class PaymentDayChangeWorkflow:
    def __init__(self):
        self.decision = None

    @workflow.run
    async def run(self, application_id: int) -> str:
        await workflow.wait_condition(
            lambda: self.decision is not None
        )

        await workflow.execute_activity(
            "save_payment_day_decision",
            args=[application_id, self.decision],
            start_to_close_timeout=timedelta(seconds=30),
        )

        return self.decision

    @workflow.update
    def submit_decision(self, decision: str) -> None:
        self.decision = decision

    @submit_decision.validator
    def validate_decision(self, decision: str) -> None:
        if decision not in ("approved", "rejected"):
            raise ValueError(
                "Решение должно быть approved или rejected"
            )
