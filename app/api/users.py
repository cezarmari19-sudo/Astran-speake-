from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel, field_validator
from ..core.database import get_db
from ..core.security import validate_full_id
from ..models.user import User

router = APIRouter(prefix="/users", tags=["users"])


class RegisterRequest(BaseModel):
    full_id: str
    public_key: str
    username: str = "Anonim"

    @field_validator("full_id")
    @classmethod
    def validate_id(cls, v: str) -> str:
        if not validate_full_id(v):
            raise ValueError("full_id invalid: 20 caractere alfanumerice")
        return v

    @field_validator("username")
    @classmethod
    def validate_username(cls, v: str) -> str:
        v = v.strip()
        if len(v) < 1 or len(v) > 10:
            raise ValueError("Username între 1 și 10 caractere")
        return v


class UserResponse(BaseModel):
    display_id: str
    username: str
    public_key: str


@router.post("/register", status_code=201)
async def register(req: RegisterRequest, db: AsyncSession = Depends(get_db)):
    existing = await db.get(User, req.full_id)
    if existing:
        raise HTTPException(status_code=409, detail="ID deja înregistrat")

    user = User(
        full_id=req.full_id,
        display_id=req.full_id[:7],
        username=req.username,
        public_key=req.public_key,
    )
    db.add(user)
    await db.commit()
    return {
        "status": "registered",
        "display_id": user.display_id,
        "username": user.username,
    }


@router.get("/{display_id}", response_model=UserResponse)
async def find_by_display_id(display_id: str, db: AsyncSession = Depends(get_db)):
    if len(display_id) != 7:
        raise HTTPException(status_code=400, detail="display_id trebuie să aibă 7 caractere")

    result = await db.execute(select(User).where(User.display_id == display_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User negăsit")

    return UserResponse(
        display_id=user.display_id,
        username=user.username,
        public_key=user.public_key,
    )