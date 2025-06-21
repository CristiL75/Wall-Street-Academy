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

    if trade.trade_type == "sell":
        # Verifică dacă utilizatorul deține acțiunile
        symbol_exists = False
        enough_quantity = False
        
        for holding in portfolio.holdings:
            if holding.symbol == trade.symbol:
                symbol_exists = True
                if holding.quantity >= trade.quantity:
                    enough_quantity = True
                break
                
        if not symbol_exists:
            raise HTTPException(status_code=400, detail=f"Nu dețineți acțiuni {trade.symbol}")
        
        if not enough_quantity:
            raise HTTPException(status_code=400, detail="Cantitate insuficientă pentru vânzare")
    

    if trade.trade_type == "buy" and portfolio.cash < cost:
        raise HTTPException(status_code=400, detail="Insufficient funds")



    # Create new trade record
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

    # Update portfolio cash
    if trade.trade_type == "buy":
        portfolio.cash -= cost
        
        # Update or add holding
        found = False
        if not portfolio.holdings:
            portfolio.holdings = []
            
        # Check if holding already exists
        for holding in portfolio.holdings:
            if holding.symbol == trade.symbol:
                # Calculate new average buy price
                total_value = (holding.quantity * holding.avg_buy_price) + (trade.quantity * trade.execution_price)
                new_quantity = holding.quantity + trade.quantity
                
                # Update holding
                holding.quantity = new_quantity
                holding.avg_buy_price = total_value / new_quantity if new_quantity > 0 else 0
                holding.current_price = trade.execution_price  # Update current price
                holding.market_value = holding.quantity * holding.current_price
                holding.last_updated = datetime.utcnow()
                found = True
                break
                
        # Add new holding if not found
        if not found:
            from models.portfolio import Holding  # Import Holding model
            new_holding = Holding(
                symbol=trade.symbol,
                quantity=trade.quantity,
                avg_buy_price=trade.execution_price,
                current_price=trade.execution_price,
                market_value=trade.quantity * trade.execution_price,
                last_updated=datetime.utcnow()
            )
            portfolio.holdings.append(new_holding)
    else:
        # Handle sell transaction
        portfolio.cash += (trade.execution_price * trade.quantity - trade.commission)
        
        # Update holdings for sell
        for holding in portfolio.holdings:
            if holding.symbol == trade.symbol:
                # Reduce quantity
                holding.quantity -= trade.quantity
                
                # Remove holding if quantity <= 0
                if holding.quantity <= 0:
                    portfolio.holdings = [h for h in portfolio.holdings if h.symbol != trade.symbol]
                else:
                    # Update market value
                    holding.current_price = trade.execution_price
                    holding.market_value = holding.quantity * holding.current_price
                    holding.last_updated = datetime.utcnow()
                break
    
    # Save updated portfolio
    await portfolio.save()

    # Blockchain registration (unchanged)
    try:
        blockchain_result = register_trade_on_chain({
            "user_id": user_oid,
            "symbol": trade.symbol,
            "quantity": trade.quantity,
            "execution_price": trade.execution_price
        })
        if hasattr(new_trade, "blockchain_tx"):
            new_trade.blockchain_tx = blockchain_result.get("tx_hash")
            await new_trade.save()
    except Exception as e:
        print(f"Blockchain registration failed: {str(e)}")
    
    # Return trade confirmation
    return {
        "trade_id": str(new_trade.id),
        "status": "completed",
        "message": "Trade executed successfully",
        "blockchain_tx": new_trade.blockchain_tx if hasattr(new_trade, "blockchain_tx") else None
    }
    
from blockchain.utils import get_trades_from_chain

# Adaugă acest endpoint nou la sfârșitul fișierului trades.py

@router.get("/user/{user_id}")
async def get_user_trades(user_id: str):
    try:
        user_oid = ObjectId(user_id)
    except:
        raise HTTPException(status_code=400, detail="Invalid user_id format")
    
    trades = await Trade.find(Trade.user_id == user_oid).sort(-Trade.timestamp).to_list()
    
    # Convertește ObjectId la string pentru a putea fi serializat în JSON
    return [
        {
            "id": str(trade.id),
            "user_id": str(trade.user_id),
            "symbol": trade.symbol,
            "quantity": trade.quantity,
            "trade_type": trade.trade_type,
            "order_type": trade.order_type,
            "execution_price": trade.execution_price,
            "commission": trade.commission,
            "status": trade.status,
            "timestamp": trade.timestamp,
            "blockchain_tx": getattr(trade, "blockchain_tx", None)
        }
        for trade in trades
    ]

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
