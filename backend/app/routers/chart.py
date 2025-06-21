# app/routers/chart.py

from fastapi import APIRouter, HTTPException
from models.stock import Stock
from datetime import datetime, timedelta

router = APIRouter()

@router.get("/{symbol}")
async def get_chart(symbol: str):
    stock = await Stock.find_one(Stock.symbol == symbol)

    if not stock:
        raise HTTPException(status_code=404, detail="Stock not found")

    if not hasattr(stock, "price_history") or not stock.price_history:
        raise HTTPException(status_code=400, detail="No price history available")

    # Etichetele (ultimele zile)
    labels = [(datetime.now() - timedelta(days=i)).strftime("%Y-%m-%d") for i in reversed(range(len(stock.price_history)))]
    values = stock.price_history

    return {
        "labels": labels,
        "values": values
    }
