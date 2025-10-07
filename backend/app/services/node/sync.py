"""Node synchronization service"""
import logging
from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.models.node import Node
from app.models.user import User
from app.models.inbound import Inbound
from app.services.node.grpc_client import NodeGRPCClient
from app.services.xray.config_builder import XrayConfigBuilder
from app.db.base import async_session_maker

logger = logging.getLogger(__name__)


async def sync_all_nodes_background() -> None:
    """
    Background task wrapper for sync_all_nodes
    Creates its own database session
    """
    async with async_session_maker() as db:
        try:
            result = await sync_all_nodes(db, background=True)
            logger.info(f"Background sync completed: {result}")
        except Exception as e:
            logger.error(f"Background sync failed: {e}")


async def sync_all_nodes(db: AsyncSession, background: bool = False) -> dict:
    """
    Synchronize configuration to all enabled nodes
    
    Args:
        db: Database session
        background: If True, run in background and catch errors silently
    
    Returns:
        Dictionary with sync results
    """
    # Get all enabled and connected nodes
    result = await db.execute(
        select(Node).where(
            Node.is_enabled == True,
            Node.is_connected == True
        )
    )
    nodes = result.scalars().all()
    
    if not nodes:
        logger.warning("No enabled and connected nodes found for sync")
        return {"synced": 0, "failed": 0, "message": "No nodes to sync"}
    
    # Get all enabled inbounds
    result = await db.execute(
        select(Inbound).where(Inbound.is_enabled == True)
    )
    inbounds = result.scalars().all()
    
    if not inbounds:
        logger.warning("No enabled inbounds found")
        return {"synced": 0, "failed": 0, "message": "No inbounds to sync"}
    
    # Get all active users with their proxies and inbounds
    result = await db.execute(
        select(User)
        .options(selectinload(User.proxies))
        .options(selectinload(User.inbounds))
        .where(User.status == "ACTIVE")
    )
    users = result.scalars().all()
    
    # Build Xray configuration
    builder = XrayConfigBuilder()
    builder.add_api_inbound(port=10085)
    
    # Collect inbounds with torrent blocking
    blocked_inbound_tags = []
    
    for inbound in inbounds:
        # Get users assigned to this inbound
        inbound_users = [
            user for user in users
            if any(ui.inbound_tag == inbound.tag for ui in user.inbounds)
        ]
        
        if inbound_users:
            builder.add_inbound(inbound, inbound_users)
        
        # Track inbounds that block torrents
        if inbound.block_torrents:
            blocked_inbound_tags.append(inbound.tag)
    
    # Add torrent blocking rules if needed
    if blocked_inbound_tags:
        builder.add_torrent_blocking_rules(blocked_inbound_tags)
    
    config_json = builder.build()
    
    # Sync to all nodes
    synced = 0
    failed = 0
    errors = []
    
    for node in nodes:
        try:
            client = NodeGRPCClient(node)
            # Use restart_xray to ensure Xray picks up new config
            result = await client.restart_xray(config_json, users)
            
            # Update node status
            node.xray_running = result["running"]
            node.xray_version = result["xray_version"]
            await db.commit()
            
            synced += 1
            logger.info(f"Successfully synced and restarted Xray on node {node.id} ({node.name})")
            
        except Exception as e:
            error_str = str(e)
            
            # "xray is already running" is not a critical error - config was updated
            if "already running" in error_str.lower():
                synced += 1
                logger.info(f"Node {node.id} ({node.name}): Config updated, Xray already running")
            else:
                failed += 1
                error_msg = f"Node {node.id} ({node.name}): {error_str}"
                errors.append(error_msg)
                logger.error(f"Failed to sync node {node.id}: {e}")
                
                if not background:
                    # Update node status to show it failed
                    node.xray_running = False
                    await db.commit()
    
    await db.commit()
    
    return {
        "synced": synced,
        "failed": failed,
        "total_nodes": len(nodes),
        "total_inbounds": len(inbounds),
        "total_users": len(users),
        "errors": errors if errors else None
    }


async def sync_single_node(db: AsyncSession, node_id: int) -> dict:
    """
    Synchronize configuration to a single node
    
    Args:
        db: Database session
        node_id: Node ID to sync
    
    Returns:
        Dictionary with sync result
    """
    result = await db.execute(select(Node).where(Node.id == node_id))
    node = result.scalar_one_or_none()
    
    if not node:
        raise ValueError(f"Node {node_id} not found")
    
    if not node.is_connected:
        raise ValueError(f"Node {node_id} is not connected")
    
    # Get all enabled inbounds
    result = await db.execute(
        select(Inbound).where(Inbound.is_enabled == True)
    )
    inbounds = result.scalars().all()
    
    if not inbounds:
        raise ValueError("No enabled inbounds found")
    
    # Get all active users
    result = await db.execute(
        select(User)
        .options(selectinload(User.proxies))
        .options(selectinload(User.inbounds))
        .where(User.status == "ACTIVE")
    )
    users = result.scalars().all()
    
    # Build configuration
    builder = XrayConfigBuilder()
    builder.add_api_inbound(port=10085)
    
    # Collect inbounds with torrent blocking
    blocked_inbound_tags = []
    
    for inbound in inbounds:
        inbound_users = [
            user for user in users
            if any(ui.inbound_tag == inbound.tag for ui in user.inbounds)
        ]
        
        if inbound_users:
            builder.add_inbound(inbound, inbound_users)
        
        # Track inbounds that block torrents
        if inbound.block_torrents:
            blocked_inbound_tags.append(inbound.tag)
    
    # Add torrent blocking rules if needed
    if blocked_inbound_tags:
        builder.add_torrent_blocking_rules(blocked_inbound_tags)
    
    config_json = builder.build()
    
    # Sync to node with restart
    client = NodeGRPCClient(node)
    result = await client.restart_xray(config_json, users)
    
    # Update node status
    node.xray_running = result["running"]
    node.xray_version = result["xray_version"]
    await db.commit()
    
    return {
        "success": True,
        "xray_running": result["running"],
        "xray_version": result["xray_version"],
        "inbounds_count": len(inbounds),
        "users_count": len(users)
    }
