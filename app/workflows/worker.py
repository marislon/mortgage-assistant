import asyncio
from concurrent.futures import ThreadPoolExecutor

from temporalio.client import Client
from temporalio.worker import Worker

from app.workflows.activities import save_payment_day_decision
from app.workflows.payment_day import PaymentDayChangeWorkflow


async def main() -> None:
    client = await Client.connect("localhost:7233")

    worker = Worker(
        client,
        task_queue="payment-day",
        workflows=[PaymentDayChangeWorkflow],
        activities=[save_payment_day_decision],
        activity_executor=ThreadPoolExecutor(max_workers=4),
    )
    print("Temporal Worker запущен")
    await worker.run()


if __name__ == "__main__":
    asyncio.run(main())
