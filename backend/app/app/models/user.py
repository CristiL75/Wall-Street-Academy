from beanie import Document
from pydantic import EmailStr, Field

class User(Document):
    username: str
    email: EmailStr
    password_hash: str = Field(repr=False)  # evită să apară în print()

    class Settings:
        name = "users"
