from motor.motor_asyncio import AsyncIOMotorClient
from beanie import init_beanie
from models.user import User
from models.portfolio import Portfolio
from models.trade import Trade
from routers.achievements import UserAchievement  # Import UserAchievement

async def init_main_db(additional_models=None):
    client = AsyncIOMotorClient("mongodb://localhost:27017")
    db = client.wallstreet_sim
    
    # Lista de bază de modele
    models = [User, Portfolio, Trade, UserAchievement]
    
    # Dacă există modele suplimentare, adaugă-le
    if additional_models:
        for model in additional_models:
            if model not in models:
                models.append(model)
    
    await init_beanie(database=db, document_models=models)