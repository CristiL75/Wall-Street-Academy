from beanie import Document
from pydantic import EmailStr, Field
from datetime import datetime

class User(Document):
    username: str
    email: EmailStr
    password_hash: str
    wallet_address: str = Field(default="")
    wallet_private_key: str = Field(default="")
    created_at: datetime = Field(default_factory=datetime.utcnow)  # ✅ adăugat

    class Settings:
        name = "users"
