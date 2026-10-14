
import asyncio

from sqlalchemy import text

from app.core.db import engine


async def main():
    async with engine.connect() as connection:
        result = await connection.execute(text("SELECT 1"))
        print("Ответ PostgreSQL:", result.scalar_one())

    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())
