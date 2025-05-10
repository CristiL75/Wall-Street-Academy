
from fastapi import APIRouter, HTTPException
from models.user import User
from ai.recommender import build_user_trade_matrix, generate_recommendations

router = APIRouter()

@router.get("/{user_id}", response_model=list)
async def get_recommendations(user_id: str):
    user = await User.get(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    users = await User.find_all().to_list()
    matrix = build_user_trade_matrix(users)
    recs = generate_recommendations(user_id, matrix)
    return recs
