from fastapi import APIRouter, Body
import httpx
from models.portfolio import Portfolio
from models.stock import Stock
from beanie import PydanticObjectId
from fastapi import HTTPException

router = APIRouter()
OLLAMA_URL = "http://localhost:11434/v1/chat/completions"

async def get_user_portfolio(user_id: str):
    if user_id == "guest":
        return "You are not logged in. Please log in to see your portfolio information."
    
    try:
        portfolio = await Portfolio.find_one({"user_id": PydanticObjectId(user_id)})
        if not portfolio or not portfolio.holdings:
            return "You don't have any stocks in your portfolio yet."
        
        lines = ["Your portfolio:"]
        for h in portfolio.holdings:
            lines.append(f"- {h.symbol}: {h.quantity} shares, avg buy price: {h.avg_buy_price}")
        return "\n".join(lines)
    except Exception as e:
        print(f"Error getting portfolio: {e}")
        return "Could not retrieve portfolio information."

@router.post("/chat")
async def chat_with_mistral(
    message: str = Body(...),
    user_id: str = Body(...)
):
    """
    Chatbot endpoint using local Mistral (Ollama).
    Responds in the same language the user asked the question in.
    Uses user's portfolio as context if user is logged in.
    """
    try:

        portfolio_context = await get_user_portfolio(user_id)
        
        system_prompt = (
            "You are a helpful assistant for the Wall Street Academy app. "
            "IMPORTANT: Always respond in the same language the user asks their question in. "
            "If they write in English, respond in English. "
            "If they write in Romanian, respond in Romanian. "
            "If they write in Spanish, respond in Spanish, etc. "
            "You have access to the user's portfolio information and can answer questions about it. "
            f"{portfolio_context}\n"
            "If the user asks about their stocks, use this information."
        )
        payload = {
            "model": "mistral",
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": message}
            ],
            "stream": False
        }
        async with httpx.AsyncClient() as client:
            response = await client.post(OLLAMA_URL, json=payload, timeout=60.0)
            data = response.json()
            return {"response": data["choices"][0]["message"]["content"]}
    except Exception as e:
        print(f"Chatbot error: {e}")
        raise HTTPException(status_code=500, detail=f"Error processing request: {str(e)}")