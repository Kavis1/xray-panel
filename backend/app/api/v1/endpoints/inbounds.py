from typing import List
from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.db.base import get_db
from app.models.admin import Admin
from app.models.inbound import Inbound
from app.schemas.inbound import InboundCreate, InboundUpdate, InboundResponse
from app.api.deps import get_current_admin
from app.services.node.sync import sync_all_nodes_background
import logging

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/", response_model=List[InboundResponse])
async def list_inbounds(
    db: AsyncSession = Depends(get_db),
    current_admin: Admin = Depends(get_current_admin),
    skip: int = 0,
    limit: int = 100,
):
    result = await db.execute(select(Inbound).offset(skip).limit(limit))
    inbounds = result.scalars().all()
    return inbounds


@router.post("/", response_model=InboundResponse, status_code=status.HTTP_201_CREATED)
async def create_inbound(
    inbound_data: InboundCreate,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    current_admin: Admin = Depends(get_current_admin),
):
    result = await db.execute(select(Inbound).where(Inbound.tag == inbound_data.tag))
    existing_inbound = result.scalar_one_or_none()
    
    if existing_inbound:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Inbound tag already exists",
        )
    
    new_inbound = Inbound(
        tag=inbound_data.tag,
        type=inbound_data.type,
        listen=inbound_data.listen,
        port=inbound_data.port,
        network=inbound_data.network,
        security=inbound_data.security,
        tls_settings=inbound_data.tls_settings,
        reality_settings=inbound_data.reality_settings,
        stream_settings=inbound_data.stream_settings,
        sniffing_enabled=inbound_data.sniffing_enabled,
        sniffing_dest_override=inbound_data.sniffing_dest_override,
        domain_strategy=inbound_data.domain_strategy,
        fallbacks=inbound_data.fallbacks,
        remark=inbound_data.remark,
    )
    
    db.add(new_inbound)
    await db.commit()
    await db.refresh(new_inbound)
    
    # Auto-sync to all nodes in background
    background_tasks.add_task(sync_all_nodes_background)
    logger.info(f"Inbound {new_inbound.tag} created, queued sync to all nodes")
    
    return new_inbound


@router.get("/{inbound_id}", response_model=InboundResponse)
async def get_inbound(
    inbound_id: int,
    db: AsyncSession = Depends(get_db),
    current_admin: Admin = Depends(get_current_admin),
):
    result = await db.execute(select(Inbound).where(Inbound.id == inbound_id))
    inbound = result.scalar_one_or_none()
    
    if not inbound:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Inbound not found",
        )
    
    return inbound


@router.patch("/{inbound_id}", response_model=InboundResponse)
async def update_inbound(
    inbound_id: int,
    inbound_data: InboundUpdate,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    current_admin: Admin = Depends(get_current_admin),
):
    result = await db.execute(select(Inbound).where(Inbound.id == inbound_id))
    inbound = result.scalar_one_or_none()
    
    if not inbound:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Inbound not found",
        )
    
    update_data = inbound_data.model_dump(exclude_unset=True)
    
    for field, value in update_data.items():
        setattr(inbound, field, value)
    
    await db.commit()
    await db.refresh(inbound)
    
    # Auto-sync to all nodes in background
    background_tasks.add_task(sync_all_nodes_background)
    logger.info(f"Inbound {inbound.tag} updated, queued sync to all nodes")
    
    return inbound


@router.delete("/{inbound_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_inbound(
    inbound_id: int,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    current_admin: Admin = Depends(get_current_admin),
):
    result = await db.execute(select(Inbound).where(Inbound.id == inbound_id))
    inbound = result.scalar_one_or_none()
    
    if not inbound:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Inbound not found",
        )
    
    inbound_tag = inbound.tag
    await db.delete(inbound)
    await db.commit()
    
    # Auto-sync to all nodes in background
    background_tasks.add_task(sync_all_nodes_background)
    logger.info(f"Inbound {inbound_tag} deleted, queued sync to all nodes")
