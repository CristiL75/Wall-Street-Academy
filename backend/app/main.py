from fastapi import FastAPI


from routers import users, trades, portfolios, leaderboard, auth, recommendations, stocks, chart  

from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="Wall Street Academy API")


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # sau lista frontend-urilor tale, ex: ["http://localhost:5173"]
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


from db_sim import init_main_db
from db_stocks import init_stock_db

@app.on_event("startup")
async def app_startup():
    await init_main_db()
    await init_stock_db()




app.include_router(users.router, prefix="/users", tags=["Users"])
app.include_router(trades.router, prefix="/trades", tags=["Trades"])
app.include_router(portfolios.router, prefix="/portfolios", tags=["Portfolios"])
app.include_router(leaderboard.router, prefix="/leaderboard", tags=["Leaderboard"])
app.include_router(auth.router, prefix="/auth", tags=["Auth"]) 
app.include_router(recommendations.router, prefix="/recommendations", tags=["AI"])  
app.include_router(stocks.router, prefix="/stocks", tags=["Stocks"])
app.include_router(chart.router) 


@app.get("/")
def read_root():
    return {"message": "Wall Street Academy backend is running!"}
