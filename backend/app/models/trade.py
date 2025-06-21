from beanie import Document
from pydantic import Field
from bson import ObjectId
from datetime import datetime
from enum import Enum
from typing import Optional

class TradeType(str, Enum):
    buy = "buy"
    sell = "sell"


class OrderType(str, Enum):
    market = "market"
    limit = "limit"


class TradeStatus(str, Enum):
    pending = "pending"
    completed = "completed"
    failed = "failed"


class Trade(Document):
    user_id: ObjectId
    symbol: str
    trade_type: str       # buy / sell
    order_type: str       # market / limit
    quantity: float
    limit_price: float = 0.0
    execution_price: float = 0.0
    commission: float = 0.0
    status: str = "pending"
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    blockchain_tx: Optional[str] = None  # Add this field

    class Settings:
        name = "trades"

    model_config = {
        "arbitrary_types_allowed": True
    }
