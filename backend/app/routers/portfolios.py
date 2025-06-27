from fastapi import APIRouter, HTTPException
from models.portfolio import Portfolio
from models.user import User  # asigură-te că ai acest import!
from bson import ObjectId
import yfinance as yf
from datetime import datetime
from pydantic import BaseModel

router = APIRouter()

class PortfolioCreate(BaseModel):
    user_id: str
    cash: float = 100000.0  # Default starting cash

# Add this endpoint to create a portfolio
@router.post("/", response_model=dict)
async def create_portfolio(portfolio_data: PortfolioCreate):
    try:
        user_oid = ObjectId(portfolio_data.user_id)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid user ID format")
    
    # Check if portfolio already exists
    existing = await Portfolio.find_one(Portfolio.user_id == user_oid)
    if existing:
        return {
            "status": "exists",
            "portfolio_id": str(existing.id),
            "message": "Portfolio already exists for this user"
        }
    
    # Create new portfolio
    new_portfolio = Portfolio(
        user_id=user_oid,
        cash=portfolio_data.cash,
        holdings=[],
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    
    await new_portfolio.save()
    
    return {
        "status": "created",
        "portfolio_id": str(new_portfolio.id),
        "cash": portfolio_data.cash,
        "message": "Portfolio created successfully"
    }


@router.get("/{user_id}", response_model=dict)
async def get_portfolio(user_id: str):
    try:
        user_oid = ObjectId(user_id)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid user ID format")

    portfolio = await Portfolio.find_one(Portfolio.user_id == user_oid)
    if not portfolio:
        raise HTTPException(status_code=404, detail="Portfolio not found")

    # Caută userul asociat portofoliului
    user = await User.find_one(User.id == user_oid)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # Log pentru debugging
    print(f"Portfolio for {user_id}: {len(portfolio.holdings)} holdings")

    if not portfolio.holdings:
        return {
            "cash": round(portfolio.cash, 2),
            "holdings": [],
            "wallet_address": user.wallet_address,
            "total_invested": 0.0,
            "total_value": round(portfolio.cash, 2),
            "total_profit": 0.0,
            "updated": False
        }

    # Actualizează prețurile curente
    price_update_count = 0
    for holding in portfolio.holdings:
        try:
            print(f"Fetching current price for {holding.symbol}...")
            ticker = yf.Ticker(holding.symbol)
            price = ticker.info.get("regularMarketPrice", 0.0)
            print(f"Symbol: {holding.symbol}, Price from API: {price}")
            
            if price and price > 0:
                holding.current_price = price
                holding.market_value = round(price * holding.quantity, 2)
                price_update_count += 1
            else:
                print(f"Warning: Got zero price for {holding.symbol}")
                # Încercăm o metodă alternativă pentru a obține prețul
                try:
                    hist = ticker.history(period="1d")
                    if not hist.empty:
                        last_price = hist['Close'].iloc[-1]
                        print(f"Got historical price: {last_price}")
                        holding.current_price = last_price
                        holding.market_value = round(last_price * holding.quantity, 2)
                        price_update_count += 1
                except Exception as e:
                    print(f"Failed to get historical price: {str(e)}")
            
            holding.last_updated = datetime.utcnow()
        except Exception as e:
            print(f"Error updating price for {holding.symbol}: {str(e)}")
            # Nu modificăm prețul dacă există eroare, păstrăm valoarea existentă

    print(f"Updated prices for {price_update_count} out of {len(portfolio.holdings)} holdings")

    # Forțăm salvarea actualizărilor
    try:
        await portfolio.save()
        print(f"Portfolio saved successfully")
    except Exception as e:
        print(f"Error saving portfolio: {str(e)}")

    # Verificăm dacă prețurile au fost actualizate corect
    for holding in portfolio.holdings:
        print(f"After save - Symbol: {holding.symbol}, Current price: {holding.current_price}")

    # Construim răspunsul
    return {
        "cash": round(portfolio.cash, 2),
        "holdings": [
            {
                "symbol": h.symbol,
                "quantity": h.quantity,
                "avg_buy_price": h.avg_buy_price,
                "current_price": h.current_price,
                "market_value": h.market_value,
                "invested_value": round(h.avg_buy_price * h.quantity, 2),
                "profit_loss": round((h.current_price - h.avg_buy_price) * h.quantity, 2),
                "profit_loss_percent": round(((h.current_price / h.avg_buy_price) - 1) * 100, 2) if h.avg_buy_price > 0 else 0,
                "last_updated": h.last_updated
            } 
            for h in portfolio.holdings
        ],
        "wallet_address": user.wallet_address,
        "total_invested": round(sum(h.avg_buy_price * h.quantity for h in portfolio.holdings), 2),
        "total_value": round(portfolio.cash + sum(h.market_value for h in portfolio.holdings), 2),
        "total_profit": round(sum((h.current_price - h.avg_buy_price) * h.quantity for h in portfolio.holdings), 2),
        "updated": True
    }