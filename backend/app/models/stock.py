from beanie import Document
from pydantic import BaseModel

class Stock(Document):
    symbol: str
    name: str
    sector: str = ""
    market_cap: float = 0.0
    last_price: float = 0.0

    class Settings:
        name = "stocks"