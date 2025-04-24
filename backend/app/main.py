from fastapi import FastAPI
from app.db import init_db


from app.routers import users, trades, portfolios, leaderboard, auth

app = FastAPI(title="Wall Street Academy API")


@app.on_event("startup")
async def app_startup():
    await init_db()


app.include_router(users.router, prefix="/users", tags=["Users"])
app.include_router(trades.router, prefix="/trades", tags=["Trades"])
app.include_router(portfolios.router, prefix="/portfolios", tags=["Portfolios"])
app.include_router(leaderboard.router, prefix="/leaderboard", tags=["Leaderboard"])
app.include_router(auth.router, prefix="/login", tags=["Auth"])


@app.get("/")
def read_root():
    return {"message": "Wall Street Academy backend is running!"}
