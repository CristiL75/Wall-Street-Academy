from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from app.models.user import User
from app.auth.security import verify_password
from app.auth.auth import create_access_token

router = APIRouter()

class LoginRequest(BaseModel):
    email: str
    password: str

@router.post("/", response_model=dict)
async def login_user(data: LoginRequest):
    user = await User.find_one(User.email == data.email)
    if not user or not verify_password(data.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    token = create_access_token({"sub": str(user.id)})
    return {"access_token": token, "token_type": "bearer"}
