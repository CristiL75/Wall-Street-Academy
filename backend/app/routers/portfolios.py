from fastapi import APIRouter, HTTPException
from models.portfolio import Portfolio
from bson import ObjectId
import yfinance as yf
from datetime import datetime

router = APIRouter()

@router.get("/{user_id}", response_model=dict)
async def get_portfolio(user_id: str):
    try:
        user_oid = ObjectId(user_id)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid user ID format")

    portfolio = await Portfolio.find_one(Portfolio.user_id == user_oid)
    if not portfolio:
        raise HTTPException(status_code=404, detail="Portfolio not found")

    if not portfolio.holdings:
        return {
            "cash": round(portfolio.cash, 2),
            "holdings": [],
            "total_invested": 0.0,
            "total_value": round(portfolio.cash, 2),
            "total_profit": 0.0,
            "updated": False
        }

    total_invested = 0.0
    total_value = portfolio.cash

    for holding in portfolio.holdings:
        try:
            ticker = yf.Ticker(holding.symbol)
            price = ticker.info.get("regularMarketPrice", 0.0)
        except Exception:
            price = 0.0

        holding.current_price = price
        holding.market_value = round(price * holding.quantity, 2)
        holding.invested_value = round(holding.avg_price * holding.quantity, 2)
        holding.profit = round(holding.market_value - holding.invested_value, 2)
        holding.last_updated = datetime.utcnow()

        total_invested += holding.invested_value
        total_value += holding.market_value

    total_profit = round(total_value - (portfolio.cash + total_invested), 2)

    await portfolio.save()

    return {
        "cash": round(portfolio.cash, 2),
        "holdings": [h.dict() for h in portfolio.holdings],
        "total_invested": round(total_invested, 2),
        "total_value": round(total_value, 2),
        "total_profit": total_profit,
        "updated": True
    }
