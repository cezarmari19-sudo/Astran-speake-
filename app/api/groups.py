from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, insert
from pydantic import BaseModel, field_validator
from ..core.database import get_db
from ..core.security import validate_full_id
from ..models.group import Group, group_members
from ..models.user import User
import secrets

router = APIRouter(prefix="/groups", tags=["groups"])


class CreateGroupRequest(BaseModel):
    admin_id: str
    name: str
    only_admin_can_send: bool = False

    @field_validator("admin_id")
    @classmethod
    def validate_admin(cls, v: str) -> str:
        if not validate_full_id(v):
            raise ValueError("admin_id invalid")
        return v

    @field_validator("name")
    @classmethod
    def validate_name(cls, v: str) -> str:
        v = v.strip()
        if len(v) < 3 or len(v) > 100:
            raise ValueError("Numele grupului trebuie să aibă între 3 și 100 de caractere")
        return v


class JoinGroupRequest(BaseModel):
    user_id: str
    group_display_id: str

    @field_validator("user_id")
    @classmethod
    def validate_user(cls, v: str) -> str:
        if not validate_full_id(v):
            raise ValueError("user_id invalid")
        return v


@router.post("/create", status_code=201)
async def create_group(req: CreateGroupRequest, db: AsyncSession = Depends(get_db)):
    """Creează un grup nou. Admin-ul devine automat primul membru."""
    admin = await db.get(User, req.admin_id)
    if not admin:
        raise HTTPException(status_code=404, detail="Admin negăsit")

    group_id = secrets.token_urlsafe(15)[:20]
    group = Group(
        group_id=group_id,
        display_id=group_id[:7],
        name=req.name,
        admin_id=req.admin_id,
        only_admin_can_send=req.only_admin_can_send,
    )
    db.add(group)
    await db.flush()

    await db.execute(
        insert(group_members).values(
            group_id=group_id,
            user_id=req.admin_id,
            is_admin="1",
            can_send="1",
        )
    )

    return {"group_id": group_id, "display_id": group_id[:7], "name": req.name}


@router.post("/join")
async def join_group(req: JoinGroupRequest, db: AsyncSession = Depends(get_db)):
    """Alătură-te unui grup cunoscând primele 7 caractere din group_id."""
    result = await db.execute(
        select(Group).where(Group.display_id == req.group_display_id)
    )
    group = result.scalar_one_or_none()
    if not group:
        raise HTTPException(status_code=404, detail="Grup negăsit")

    await db.execute(
        insert(group_members).values(
            group_id=group.group_id,
            user_id=req.user_id,
            is_admin="0",
            can_send="1" if not group.only_admin_can_send else "0",
        )
    )

    return {"status": "joined", "group_name": group.name}
