from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.db.base import get_db
from app.models.admin import Admin
from app.schemas.admin import AdminCreate, AdminUpdate, AdminResponse
from app.core.security import get_password_hash
from app.api.deps import get_current_admin, get_current_sudo_admin

router = APIRouter()


@router.get("/", response_model=List[AdminResponse])
async def list_admins(
    db: AsyncSession = Depends(get_db),
    current_admin: Admin = Depends(get_current_sudo_admin),
    skip: int = 0,
    limit: int = 100,
):
    result = await db.execute(select(Admin).offset(skip).limit(limit))
    admins = result.scalars().all()
    return admins


@router.post("/", response_model=AdminResponse, status_code=status.HTTP_201_CREATED)
async def create_admin(
    admin_data: AdminCreate,
    db: AsyncSession = Depends(get_db),
    current_admin: Admin = Depends(get_current_sudo_admin),
):
    result = await db.execute(select(Admin).where(Admin.username == admin_data.username))
    existing_admin = result.scalar_one_or_none()
    
    if existing_admin:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already exists",
        )
    
    new_admin = Admin(
        username=admin_data.username,
        hashed_password=get_password_hash(admin_data.password),
        is_sudo=admin_data.is_sudo,
        roles=admin_data.roles or [],
    )
    
    db.add(new_admin)
    await db.commit()
    await db.refresh(new_admin)
    
    return new_admin


@router.get("/{admin_id}", response_model=AdminResponse)
async def get_admin(
    admin_id: int,
    db: AsyncSession = Depends(get_db),
    current_admin: Admin = Depends(get_current_sudo_admin),
):
    result = await db.execute(select(Admin).where(Admin.id == admin_id))
    admin = result.scalar_one_or_none()
    
    if not admin:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Admin not found",
        )
    
    return admin


@router.patch("/{admin_id}", response_model=AdminResponse)
async def update_admin(
    admin_id: int,
    admin_data: AdminUpdate,
    db: AsyncSession = Depends(get_db),
    current_admin: Admin = Depends(get_current_sudo_admin),
):
    result = await db.execute(select(Admin).where(Admin.id == admin_id))
    admin = result.scalar_one_or_none()
    
    if not admin:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Admin not found",
        )
    
    update_data = admin_data.model_dump(exclude_unset=True)
    
    if "password" in update_data:
        update_data["hashed_password"] = get_password_hash(update_data.pop("password"))
    
    for field, value in update_data.items():
        setattr(admin, field, value)
    
    await db.commit()
    await db.refresh(admin)
    
    return admin


@router.delete("/{admin_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_admin(
    admin_id: int,
    db: AsyncSession = Depends(get_db),
    current_admin: Admin = Depends(get_current_sudo_admin),
):
    if admin_id == current_admin.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete yourself",
        )
    
    result = await db.execute(select(Admin).where(Admin.id == admin_id))
    admin = result.scalar_one_or_none()
    
    if not admin:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Admin not found",
        )
    
    await db.delete(admin)
    await db.commit()
