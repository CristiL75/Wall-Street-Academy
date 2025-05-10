from motor.motor_asyncio import AsyncIOMotorClient
from models.stock import Stock
from beanie import init_beanie

# o variabilă globală pentru acces direct în alte fișiere
stocks_db = None

async def init_stock_db():
    global stocks_db
    client = AsyncIOMotorClient("mongodb://localhost:27017")
    stocks_db = client.wallstreet
    await init_beanie(database=stocks_db, document_models=[Stock])
