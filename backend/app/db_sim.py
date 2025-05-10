from motor.motor_asyncio import AsyncIOMotorClient
from beanie import init_beanie
from models.user import User
from models.portfolio import Portfolio
from models.trade import Trade

async def init_main_db():
    client = AsyncIOMotorClient("mongodb://localhost:27017")
    db = client.wallstreet_sim
    await init_beanie(database=db, document_models=[User, Portfolio, Trade])
