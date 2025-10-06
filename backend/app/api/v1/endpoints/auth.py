from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.db.base import get_db
from app.models.admin import Admin
from app.schemas.auth import LoginRequest, Token
from app.schemas.admin import AdminResponse
from app.core.security import verify_password, create_access_token, create_refresh_token
from app.api.deps import get_current_admin

router = APIRouter()


@router.post("/login", response_model=Token)
async def login(
    login_data: LoginRequest,
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Admin).where(Admin.username == login_data.username))
    admin = result.scalar_one_or_none()
    
    if not admin or not verify_password(login_data.password, admin.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
        )
    
    if not admin.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin account is disabled",
        )
    
    admin.last_login_at = datetime.utcnow()
    await db.commit()
    
    access_token = create_access_token(admin.id)
    refresh_token = create_refresh_token(admin.id)
    
    return Token(
        access_token=access_token,
        refresh_token=refresh_token,
    )


@router.get("/me", response_model=AdminResponse)
async def get_me(
    current_admin: Admin = Depends(get_current_admin),
):
    return current_admin


@router.post("/logout")
async def logout(
    current_admin: Admin = Depends(get_current_admin),
):
    return {"message": "Successfully logged out"}
