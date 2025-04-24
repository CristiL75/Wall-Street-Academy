from motor.motor_asyncio import AsyncIOMotorClient
from beanie import init_beanie
from app.models.user import User
from app.models.portfolio import Portfolio
from app.models.trade import Trade

import asyncio

async def init_db():
    client = AsyncIOMotorClient("mongodb://localhost:27017")
    db = client.wallstreet_sim
    await init_beanie(database=db, document_models=[User, Portfolio, Trade])
