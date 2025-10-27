import asyncio
from sqlalchemy import insert
from backend.core.db import async_session_maker, Base, engine
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

async def create_database():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)

    # Add your INSERT statements here as per your sample data
    # Example (customize for your schema):
    # async with async_session_maker() as session:
    #     await session.execute(
    #         insert(Employee).values([
    #             {"name": "Alice", "department": "Engineering"}
    #         ])
    #     )
    #     await session.commit()

if __name__ == "__main__":
    asyncio.run(create_database())
