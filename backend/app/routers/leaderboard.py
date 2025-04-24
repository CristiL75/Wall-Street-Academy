from fastapi import APIRouter
from app.models.portfolio import Portfolio
from app.models.user import User
from bson import ObjectId
import yfinance as yf

router = APIRouter()

@router.get("/", response_model=list)
async def get_leaderboard():
    portfolios = await Portfolio.find_all().to_list()
    leaderboard = []

    for p in portfolios:
        total_holdings_value = 0.0
        for h in p.holdings:
            price = yf.Ticker(h.symbol).info.get("regularMarketPrice", 0.0)
            total_holdings_value += price * h.quantity

        total_value = p.cash + total_holdings_value

      
        user = await User.get(p.user_id)
        username = user.username if user else "Unknown"

        leaderboard.append({
            "username": username,
            "total_value": round(total_value, 2),
            "cash": round(p.cash, 2),
            "holdings_value": round(total_holdings_value, 2)
        })


    sorted_board = sorted(leaderboard, key=lambda x: x["total_value"], reverse=True)
    return sorted_board[:10]
