from fastapi import APIRouter
from models.stock import Stock

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