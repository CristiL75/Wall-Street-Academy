import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
from beanie import init_beanie
from models.stock import Stock
import yfinance as yf
import pandas as pd

# Poți folosi un fișier CSV cu simboluri sau un set cunoscut
def get_sp500_symbols():
    url = "https://en.wikipedia.org/wiki/List_of_S%26P_500_companies"
    table = pd.read_html(url)[0]
    return table["Symbol"].tolist()

async def populate():
    client = AsyncIOMotorClient("mongodb://localhost:27017")
    await init_beanie(database=client.wallstreet, document_models=[Stock])

    symbols = get_sp500_symbols()

    for symbol in symbols:
        try:
            ticker = yf.Ticker(symbol)
            info = ticker.info

            stock = Stock(
                symbol=symbol,
                name=info.get("shortName", symbol),
                sector=info.get("sector", "Unknown"),
                market_cap=info.get("marketCap", 0),
                last_price=info.get("regularMarketPrice", 0),
            )
            existing = await Stock.find_one(Stock.symbol == symbol)
            if existing:
                await existing.set(stock.dict(exclude={"id"}))
            else:
                await stock.insert()

            print(f"✅ {symbol} added.")
        except Exception as e:
            print(f"⚠️ Failed to fetch {symbol}: {e}")

asyncio.run(populate())
