

from beanie import Document
from pydantic import Field, BaseModel, computed_field
from bson import ObjectId
from typing import List
from datetime import datetime

class Holding(BaseModel):
    symbol: str
    quantity: float
    avg_buy_price: float  # Acesta este numele corect al atributului
    current_price: float = 0.0
    market_value: float = 0.0
    last_updated: datetime = Field(default_factory=datetime.utcnow)
    
    @property
    def invested_value(self) -> float:
        """Calculează valoarea investită (cantitate * preț mediu de cumpărare)"""
        return round(self.avg_buy_price * self.quantity, 2)
        
    @property
    def profit_loss(self) -> float:
        """Calculează profit/pierdere (valoarea de piață - valoarea investită)"""
        return round(self.market_value - self.invested_value, 2)
        
    @property
    def profit_loss_percent(self) -> float:
        """Calculează profit/pierdere în procente"""
        if self.invested_value == 0:
            return 0
        return round((self.profit_loss / self.invested_value) * 100, 2)

class Portfolio(Document):
    user_id: ObjectId
    cash: float = Field(default=10000.0)
    holdings: List[Holding] = Field(default_factory=list)

    class Settings:
        name = "portfolios"

    model_config = {
        "arbitrary_types_allowed": True
    }
    
    @property
    def total_invested(self) -> float:
        """Calculează valoarea totală investită în portofoliu"""
        if not self.holdings:
            return 0
        return round(sum(holding.invested_value for holding in self.holdings), 2)
        
    @property
    def total_value(self) -> float:
        """Calculează valoarea totală curentă a portofoliului (cash + market value)"""
        if not self.holdings:
            return self.cash
        return round(self.cash + sum(holding.market_value for holding in self.holdings), 2)
        
    @property
    def total_profit(self) -> float:
        """Calculează profitul/pierderea totală a portofoliului"""
        if not self.holdings:
            return 0
        return round(sum(holding.profit_loss for holding in self.holdings), 2)