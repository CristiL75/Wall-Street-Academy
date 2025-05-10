from fastapi import APIRouter, HTTPException
from models.trade import Trade
from models.portfolio import Portfolio
from pydantic import BaseModel
from bson import ObjectId
from datetime import datetime

from blockchain.utils import register_trade_on_chain

router = APIRouter()

class TradeRequest(BaseModel):
    user_id: str
    symbol: str
    quantity: float
    trade_type: str  # "buy" / "sell"
    order_type: str  # "market" / "limit"
    execution_price: float
    commission: float = 0.0

@router.post("/", response_model=dict)
async def create_trade(trade: TradeRequest):
    try:
        user_oid = ObjectId(trade.user_id)
    except:
        raise HTTPException(status_code=400, detail="Invalid user_id format")

    portfolio = await Portfolio.find_one(Portfolio.user_id == user_oid)
    if not portfolio:
        raise HTTPException(status_code=404, detail="Portfolio not found")

    cost = trade.execution_price * trade.quantity + trade.commission

    if trade.trade_type == "buy" and portfolio.cash < cost:
        raise HTTPException(status_code=400, detail="Insufficient funds")


    new_trade = Trade(
        user_id=user_oid,
        symbol=trade.symbol,
        trade_type=trade.trade_type,
        order_type=trade.order_type,
        quantity=trade.quantity,
        execution_price=trade.execution_price,
        commission=trade.commission,
        status="completed",
        timestamp=datetime.utcnow(),
    )
    await new_trade.insert()

  
    if trade.trade_type == "buy":
        portfolio.cash -= cost
    else:
        portfolio.cash += (trade.execution_price * trade.quantity - trade.commission)
    await portfolio.save()

    try:
        tx_hash = register_trade_on_chain(
            user_addr=str(user_oid),
            symbol=trade.symbol,
            amount=int(trade.quantity),
            is_buy=(trade.trade_type == "buy")
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Blockchain error: {str(e)}")

    return {
        "message": "Trade completed",
        "trade_id": str(new_trade.id),
        "tx_hash": tx_hash
    }
    
from blockchain.utils import get_trades_from_chain

@router.get("/onchain/{user_address}", response_model=list)
def get_onchain_trades(user_address: str):
    try:
        trades = get_trades_from_chain(user_address)
        return trades
    except Exception as e:
        import traceback
        print("❌ Blockchain read error:")
        traceback.print_exc() 
        raise HTTPException(status_code=500, detail=f"Blockchain read error: {str(e)}")
