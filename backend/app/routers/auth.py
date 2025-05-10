from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from models.user import User
from auth.security import verify_password
from auth.auth import create_access_token

router = APIRouter()

class LoginRequest(BaseModel):
    email: str
    password: str

class SignupRequest(BaseModel):
    username: str
    email: str
    password: str

@router.post("/login", response_model=dict)
async def login_user(data: LoginRequest):
    user = await User.find_one(User.email == data.email)
    if not user or not verify_password(data.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    token = create_access_token({"sub": str(user.id)})
    return {"access_token": token, "token_type": "bearer"}

@router.post("/signup", response_model=dict)
async def signup_user(data: SignupRequest):
    existing_user = await User.find_one(User.email == data.email)
    if existing_user:
        raise HTTPException(status_code=400, detail="Email already registered")

    from eth_account import Account
    from passlib.context import CryptContext

    pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
    hashed_password = pwd_context.hash(data.password)

    eth_account = Account.create()
    wallet_address = eth_account.address
    private_key = eth_account.key.hex()

    user = User(
        username=data.username,
        email=data.email,
        password_hash=hashed_password,
        wallet_address=wallet_address,
        wallet_private_key=private_key,
    )
    await user.insert()

    return {"message": "User created successfully", "wallet_address": wallet_address}
