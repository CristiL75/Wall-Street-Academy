from fastapi import APIRouter
from app.models.user import User
from pydantic import BaseModel, EmailStr
from passlib.context import CryptContext

router = APIRouter()
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

class UserCreate(BaseModel):
    username: str
    email: EmailStr
    password: str

@router.post("/", response_model=dict)
async def create_user(user: UserCreate):
    password_hash = pwd_context.hash(user.password)
    new_user = User(username=user.username, email=user.email, password_hash=password_hash)
    await new_user.insert()
    return {"message": "User created successfully", "id": str(new_user.id)}

def get_trades_from_chain(user_addr: str):
    trades = CONTRACT.functions.getUserTrades(Web3.to_checksum_address(user_addr)).call()
    
    result = []
    for trade in trades:
        result.append({
            "symbol": trade[0],
            "amount": trade[1],
            "is_buy": trade[2],
            "timestamp": trade[3],
        })
    return result
