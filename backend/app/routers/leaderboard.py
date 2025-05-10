from fastapi import APIRouter, HTTPException
from models.user import User
from models.trade import Trade
from blockchain.utils import get_trades_from_chain

router = APIRouter()

@router.get("/", response_model=list)
async def get_leaderboard():
    users = await User.find_all().to_list()
    leaderboard = []

    for user in users:
        if not user.wallet_address:
            continue

        total_profit = 0.0

        trades = await Trade.find(Trade.user_id == user.id).to_list()
        for t in trades:
            if t.trade_type == "buy":
                total_profit -= t.execution_price * t.quantity + t.commission
            elif t.trade_type == "sell":
                total_profit += t.execution_price * t.quantity - t.commission

      
        try:
            onchain_trades = get_trades_from_chain(user.wallet_address)
            total_profit += len(onchain_trades) * 0.1  # doar simbolic
        except Exception:
            pass  

        leaderboard.append({
            "username": user.username,
            "email": user.email,
            "wallet_address": user.wallet_address,
            "total_profit": round(total_profit, 2)
        })


    leaderboard.sort(key=lambda x: x["total_profit"], reverse=True)

    return leaderboard
