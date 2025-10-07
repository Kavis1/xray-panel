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
from app.services.node.firewall import FirewallManager
from app.services.xray.reality_keys import generate_reality_keypair
from app.models.node import Node
import logging

logger = logging.getLogger(__name__)
router = APIRouter()


def auto_generate_reality_keys_if_needed(inbound_data, security: str) -> dict:
    """
    Automatically generate Reality keys if:
    1. Security is 'reality'
    2. Keys are not provided or empty
    
    Returns the reality_settings dict (possibly with generated keys)
    """
    if security != "reality":
        return inbound_data
    
    # Get or create reality_settings
    reality_settings = inbound_data if isinstance(inbound_data, dict) else {}
    
    # Check if keys already exist and are valid (43 or 44 chars)
    has_private_key = reality_settings.get('privateKey') and len(reality_settings.get('privateKey', '')) in [43, 44]
    has_public_key = reality_settings.get('publicKey') and len(reality_settings.get('publicKey', '')) in [43, 44]
    
    if has_private_key and has_public_key:
        logger.info("Reality keys already present, skipping auto-generation")
        return reality_settings
    
    # Generate new keys
    try:
        keys = generate_reality_keypair()
        reality_settings['privateKey'] = keys['privateKey']
        reality_settings['publicKey'] = keys['publicKey']
        
        # Set defaults if not present
        if 'shortIds' not in reality_settings:
            reality_settings['shortIds'] = ['']
        if 'serverNames' not in reality_settings:
            reality_settings['serverNames'] = ['www.google.com']
        if 'dest' not in reality_settings:
            reality_settings['dest'] = 'www.google.com:443'
        
        logger.info(f"Auto-generated Reality keys: publicKey={keys['publicKey'][:15]}...")
        return reality_settings
        
    except Exception as e:
        logger.error(f"Failed to auto-generate Reality keys: {e}")
        # Return original settings on failure
        return reality_settings


async def open_inbound_ports_on_nodes(db: AsyncSession, port: int) -> None:
    """Open inbound port on all nodes and locally"""
    # Open port locally (on panel server)
    local_result = FirewallManager.open_local_port(port, "tcp")
    if local_result["success"]:
        logger.info(f"Opened port {port} locally: {local_result.get('message')}")
    else:
        logger.warning(f"Failed to open port {port} locally: {local_result.get('error')}")
    
    # Open port on all enabled remote nodes
    result = await db.execute(select(Node).where(Node.is_enabled == True))
    nodes = result.scalars().all()
    
    for node in nodes:
        # Skip local node (already handled above)
        if node.address in ['127.0.0.1', 'localhost', '::1']:
            continue
        
        try:
            node_result = await FirewallManager.open_port_on_node(node, port, "tcp")
            if node_result["success"]:
                logger.info(f"Opened port {port} on node {node.name}")
            else:
                logger.warning(f"Failed to open port {port} on node {node.name}: {node_result.get('error')}")
        except Exception as e:
            logger.error(f"Error opening port {port} on node {node.name}: {e}")


async def close_inbound_ports_on_nodes(db: AsyncSession, port: int) -> None:
    """Close inbound port on all nodes when deleting inbound"""
    # Close port locally (on panel server)
    local_result = FirewallManager.close_local_port(port, "tcp")
    if local_result["success"]:
        logger.info(f"Closed port {port} locally: {local_result.get('message')}")
    else:
        logger.warning(f"Failed to close port {port} locally: {local_result.get('error')}")
    
    # Close port on all enabled remote nodes
    result = await db.execute(select(Node).where(Node.is_enabled == True))
    nodes = result.scalars().all()
    
    for node in nodes:
        # Skip local node (already handled above)
        if node.address in ['127.0.0.1', 'localhost', '::1']:
            continue
        
        try:
            node_result = await FirewallManager.close_port_on_node(node, port, "tcp")
            if node_result["success"]:
                logger.info(f"Closed port {port} on node {node.name}")
            else:
                logger.warning(f"Failed to close port {port} on node {node.name}: {node_result.get('error')}")
        except Exception as e:
            logger.error(f"Error closing port {port} on node {node.name}: {e}")


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
    
    # Auto-generate Reality keys if needed
    reality_settings = inbound_data.reality_settings
    if inbound_data.security == "reality":
        reality_settings = auto_generate_reality_keys_if_needed(
            reality_settings,
            inbound_data.security
        )
        logger.info(f"Reality keys auto-generated for new inbound {inbound_data.tag}")
    
    new_inbound = Inbound(
        tag=inbound_data.tag,
        type=inbound_data.type,
        listen=inbound_data.listen,
        port=inbound_data.port,
        network=inbound_data.network,
        security=inbound_data.security,
        tls_settings=inbound_data.tls_settings,
        reality_settings=reality_settings,
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
    
    # Auto-open port on all nodes in background
    background_tasks.add_task(open_inbound_ports_on_nodes, db, new_inbound.port)
    
    # Auto-sync to all nodes in background
    background_tasks.add_task(sync_all_nodes_background)
    logger.info(f"Inbound {new_inbound.tag} created, queued port opening and sync to all nodes")
    
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
    
    # Check if security is being updated to 'reality' or already 'reality'
    new_security = update_data.get('security', inbound.security)
    
    if new_security == "reality":
        # Get current or new reality_settings
        if 'reality_settings' in update_data:
            reality_settings = update_data['reality_settings']
        else:
            reality_settings = inbound.reality_settings
        
        # Auto-generate keys if needed
        reality_settings = auto_generate_reality_keys_if_needed(
            reality_settings,
            new_security
        )
        update_data['reality_settings'] = reality_settings
        logger.info(f"Reality keys checked/generated for inbound {inbound.tag}")
    
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
    deleted_port = inbound.port
    
    await db.delete(inbound)
    await db.commit()
    
    # Auto-close port on all nodes in background
    background_tasks.add_task(close_inbound_ports_on_nodes, db, deleted_port)
    
    # Auto-sync to all nodes in background
    background_tasks.add_task(sync_all_nodes_background)
    logger.info(f"Inbound {inbound_tag} deleted, queued port closing and sync to all nodes")
    
    return None
