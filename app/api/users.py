"""
Înregistrare și rezolvare contact.

Endpoint-ul vechi GET /users/{display_id} returna full_id oricui știa doar
cele 7 caractere publice — anula complet modelul de securitate. Înlocuit cu
/users/resolve, care cere ȘI username-ul.
"""
from fastapi import APIRouter, HTTPException, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel, field_validator
from ..core.database import get_db
from ..core.security import validate_full_id
from ..services.identity import resolve_by_display_id
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

    @field_validator("public_key")
    @classmethod
    def validate_public_key(cls, v: str) -> str:
        if not v or len(v) > 4096:
            raise ValueError("public_key invalidă")
        return v


class RegisterResponse(BaseModel):
    status: str
    display_id: str
    username: str


class ResolveResponse(BaseModel):
    display_id: str
    full_id: str
    username: str
    public_key: str


@router.post("/register", status_code=status.HTTP_201_CREATED, response_model=RegisterResponse)
async def register(req: RegisterRequest, db: AsyncSession = Depends(get_db)) -> RegisterResponse:
    """Fără parolă — full_id-ul (20 caractere, generat aleator pe client)
    ȘI username-ul, păstrate doar pe dispozitiv, dovedesc proprietatea."""
    existing = await db.get(User, req.full_id)
    if existing:
        raise HTTPException(status.HTTP_409_CONFLICT, detail="ID_ALREADY_REGISTERED")

    user = User(
        full_id=req.full_id,
        display_id=req.full_id[:7],
        username=req.username,
        public_key=req.public_key,
    )
    db.add(user)
    # Commit automat, făcut de get_db() după ce handler-ul returnează —
    # nu mai e nevoie de commit/refresh explicit, fiindcă niciuna din
    # valorile returnate nu vine din server (autoincrement etc.).
    return RegisterResponse(status="registered", display_id=user.display_id, username=user.username)


@router.get("/resolve", response_model=ResolveResponse)
async def resolve_contact(
    display_id: str,
    username: str,
    db: AsyncSession = Depends(get_db),
) -> ResolveResponse:
    """Singurul mod în care full_id-ul cuiva poate fi obținut de altcineva —
    și doar dacă cel care întreabă cunoaște deja ambele informații publice.
    404 identic pentru 'display_id inexistent' și 'nume greșit', ca să nu
    existe niciun semnal care să dea de gol ce e înregistrat."""
    if len(display_id) != 7 or not display_id.isalnum():
        raise HTTPException(status.HTTP_400_BAD_REQUEST, detail="INVALID_DISPLAY_ID")

    clean_username = username.strip()
    if not (1 <= len(clean_username) <= 10):
        raise HTTPException(status.HTTP_400_BAD_REQUEST, detail="INVALID_USERNAME")

    match = await resolve_by_display_id(db, display_id, clean_username)
    if match is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="CONTACT_NOT_FOUND")

    return ResolveResponse(
        display_id=match.display_id,
        full_id=match.full_id,
        username=match.username,
        public_key=match.public_key,
    )