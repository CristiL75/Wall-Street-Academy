from fastapi import APIRouter, HTTPException
from models.stock import Stock
from typing import List

router = APIRouter()

@router.get("/")
async def get_stocks():
    stocks = await Stock.find_all().to_list()
    return [
        {
            "symbol": stock.symbol,
            "name": stock.name,
            "price": stock.last_price,
            "sector": stock.sector,
            "market_cap": stock.market_cap,
            "last_price": stock.last_price,
        }
        for stock in stocks
    ]

# Add this new endpoint to get a single stock by symbol
@router.get("/{symbol}")
async def get_stock_by_symbol(symbol: str):
    stock = await Stock.find_one(Stock.symbol == symbol)
    if not stock:
        raise HTTPException(status_code=404, detail=f"Stock with symbol {symbol} not found")
    
    return {
        "symbol": stock.symbol,
        "name": stock.name,
        "price": stock.last_price,
        "sector": stock.sector,
        "market_cap": stock.market_cap,
        "last_price": stock.last_price,
        "description": getattr(stock, "description", None),
    }

# Add this new endpoint to get just the price for a symbol
@router.get("/price/{symbol}")
async def get_stock_price(symbol: str):
    stock = await Stock.find_one(Stock.symbol == symbol)
    if not stock:
        raise HTTPException(status_code=404, detail=f"Stock with symbol {symbol} not found")
    
    return {"price": stock.last_price}