from fastapi import APIRouter, Depends, HTTPException
from datetime import datetime, timezone
import uuid

from services.database import db
from services.auth import hash_password, verify_password, create_token, get_current_user
from models.schemas import UserCreate, UserLogin, UserResponse

router = APIRouter()


@router.post("/auth/register", response_model=dict)
async def register(user: UserCreate):
    existing = await db.users.find_one({"email": user.email})
    if existing:
        raise HTTPException(status_code=400, detail="El email ya está registrado")
    user_id = str(uuid.uuid4())
    user_doc = {
        "id": user_id, "email": user.email,
        "password": hash_password(user.password),
        "name": user.name, "company": user.company,
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    await db.users.insert_one(user_doc)
    token = create_token(user_id)
    return {"token": token, "user": {"id": user_id, "email": user.email, "name": user.name, "company": user.company}}


@router.post("/auth/login", response_model=dict)
async def login(credentials: UserLogin):
    user = await db.users.find_one({"email": credentials.email})
    if not user or not verify_password(credentials.password, user["password"]):
        raise HTTPException(status_code=401, detail="Credenciales inválidas")
    token = create_token(user["id"])
    return {"token": token, "user": {"id": user["id"], "email": user["email"], "name": user["name"], "company": user.get("company")}}


@router.get("/auth/me", response_model=UserResponse)
async def get_me(user: dict = Depends(get_current_user)):
    return UserResponse(**user)
