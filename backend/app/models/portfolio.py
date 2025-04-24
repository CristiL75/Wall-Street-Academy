from beanie import Document
from pydantic import Field, BaseModel
from bson import ObjectId
from typing import List
from datetime import datetime

class Holding(BaseModel):
    symbol: str
    quantity: float
    avg_buy_price: float
    current_price: float = 0.0
    market_value: float = 0.0
    last_updated: datetime = Field(default_factory=datetime.utcnow)

class Portfolio(Document):
    user_id: ObjectId
    cash: float = Field(default=10000.0)
    holdings: List[Holding] = Field(default_factory=list)

    class Settings:
        name = "portfolios"

    model_config = {
        "arbitrary_types_allowed": True
    }
