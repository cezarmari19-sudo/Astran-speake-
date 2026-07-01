"""
Grupuri cu control granular al permisiunilor.

Aceleași reguli ca la contacte individuale — cerința ta "la fel și cu grup":
crearea/alăturarea cer (id, username) verificat pentru inițiator, iar
alăturarea cere (display_id de grup, nume de grup exact), nu doar 7 caractere.
"""
from fastapi import APIRouter, HTTPException, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError
from sqlalchemy import select, insert
from pydantic import BaseModel, field_validator
from ..core.database import get_db
from ..core.security import validate_full_id
from ..services.identity import verify_owner
from ..models.group import Group, group_members
import secrets
import string

router = APIRouter(prefix="/groups", tags=["groups"])

# Același alfabet ca full_id-urile de utilizator. Înainte, group_id venea din
# secrets.token_urlsafe(), care poate include '-' și '_' — inconsistent cu
# regula "20 caractere alfanumerice" aplicată peste tot în rest.
_ID_ALPHABET = string.ascii_letters + string.digits


def _generate_group_id() -> str:
    return "".join(secrets.choice(_ID_ALPHABET) for _ in range(20))


class CreateGroupRequest(BaseModel):
    admin_id: str
    admin_username: str
    name: str
    only_admin_can_send: bool = False

    @field_validator("admin_id")
    @classmethod
    def validate_admin(cls, v: str) -> str:
        if not validate_full_id(v):
            raise ValueError("admin_id invalid")
        return v

    @field_validator("admin_username")
    @classmethod
    def validate_admin_username(cls, v: str) -> str:
        v = v.strip()
        if len(v) < 1 or len(v) > 10:
            raise ValueError("admin_username invalid")
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
    user_username: str
    group_display_id: str
    group_name: str

    @field_validator("user_id")
    @classmethod
    def validate_user(cls, v: str) -> str:
        if not validate_full_id(v):
            raise ValueError("user_id invalid")
        return v

    @field_validator("user_username")
    @classmethod
    def validate_user_username(cls, v: str) -> str:
        v = v.strip()
        if len(v) < 1 or len(v) > 10:
            raise ValueError("user_username invalid")
        return v

    @field_validator("group_display_id")
    @classmethod
    def validate_group_display_id(cls, v: str) -> str:
        if len(v) != 7 or not v.isalnum():
            raise ValueError("group_display_id invalid")
        return v


@router.post("/create", status_code=status.HTTP_201_CREATED)
async def create_group(req: CreateGroupRequest, db: AsyncSession = Depends(get_db)):
    """Creează un grup nou. Admin-ul devine automat primul membru."""
    admin = await verify_owner(db, req.admin_id, req.admin_username)
    if admin is None:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, detail="ADMIN_NOT_VERIFIED")

    group_id = _generate_group_id()
    group = Group(
        group_id=group_id,
        display_id=group_id[:7],
        name=req.name,
        admin_id=req.admin_id,
        only_admin_can_send=req.only_admin_can_send,
    )
    db.add(group)
    await db.flush()  # necesar: group_members are FK către groups.group_id

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
    """Alătură-te unui grup cunoscând display_id-ul (7 caractere) ȘI numele
    exact al grupului — aceeași protecție împotriva coliziunilor de prefix
    ca la adăugarea unui contact individual."""
    user = await verify_owner(db, req.user_id, req.user_username)
    if user is None:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, detail="USER_NOT_VERIFIED")

    result = await db.execute(select(Group).where(Group.display_id == req.group_display_id))
    candidates = result.scalars().all()
    group = next((g for g in candidates if g.name == req.group_name.strip()), None)
    if group is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="GROUP_NOT_FOUND")

    try:
        await db.execute(
            insert(group_members).values(
                group_id=group.group_id,
                user_id=req.user_id,
                is_admin="0",
                can_send="1" if not group.only_admin_can_send else "0",
            )
        )
    except IntegrityError:
        # Înainte: membru dublu sau user inexistent picau cu 500 netratat.
        await db.rollback()
        raise HTTPException(status.HTTP_409_CONFLICT, detail="ALREADY_MEMBER")

    return {"status": "joined", "group_id": group.group_id, "group_name": group.name}