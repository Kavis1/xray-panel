"""Node synchronization service"""
import json
import logging
from typing import List, Optional, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.models.node import Node
from app.models.user import User
from app.models.inbound import Inbound
from app.services.node.grpc_client import NodeGRPCClient
from app.services.node.rest_client import NodeRestClient
from app.services.xray.config_builder import XrayConfigBuilder
from app.services.singbox.config_builder import SingBoxConfigBuilder
from app.db.base import async_session_maker
from app.utils.node_compatibility import is_node_compatible_with_inbound

logger = logging.getLogger(__name__)


def remove_tls_from_config(config_json: str, node_domain: str = None) -> str:
    """
    Filter inbounds for nodes based on TLS certificate availability.
    
    If node has domain (and certificates):
    - KEEP all protocols including TLS (Trojan, VLESS Reality, etc.)
    - Update certificate paths to use node's domain
    
    If node has NO domain:
    - KEEP only non-TLS protocols (VMess, Shadowsocks, VLESS without TLS)
    - REMOVE TLS-dependent protocols (Trojan, VLESS Reality, etc.)
    """
    config = json.loads(config_json)
    
    filtered_inbounds = []
    
    for inbound in config.get("inbounds", []):
        # Always keep API inbound
        if inbound.get("tag") == "api":
            filtered_inbounds.append(inbound)
            continue
        
        protocol = inbound.get("protocol", "")
        stream_settings = inbound.get("streamSettings", {})
        security = stream_settings.get("security", "none")
        
        # Skip Hysteria - handled by sing-box, not Xray
        if protocol in ["hysteria", "hysteria2"]:
            logger.info(f"Skipping {protocol} inbound {inbound.get('tag')} - handled by sing-box")
            continue
        
        # If node has domain - keep TLS protocols and update cert paths
        if node_domain:
            # Keep all protocols including TLS
            if protocol in ["vmess", "vless", "shadowsocks", "trojan"]:
                # Update TLS certificate paths to use node's domain
                if "streamSettings" in inbound and "tlsSettings" in inbound["streamSettings"]:
                    tls_settings = inbound["streamSettings"]["tlsSettings"]
                    if "certificates" in tls_settings:
                        for cert in tls_settings["certificates"]:
                            cert["certificateFile"] = f"/etc/letsencrypt/live/{node_domain}/fullchain.pem"
                            cert["keyFile"] = f"/etc/letsencrypt/live/{node_domain}/privkey.pem"
                
                filtered_inbounds.append(inbound)
                logger.info(f"Keeping {protocol} inbound {inbound.get('tag')} for node with domain {node_domain}")
        else:
            # Node has NO domain - remove TLS protocols
            if protocol == "trojan":
                logger.info(f"Skipping Trojan inbound {inbound.get('tag')} - node has no domain/certificates")
                continue
            
            if security in ["tls", "reality"]:
                logger.info(f"Skipping {protocol} inbound {inbound.get('tag')} - has {security} but node has no domain")
                continue
            
            # Keep non-TLS protocols
            if protocol in ["vmess", "vless", "shadowsocks"]:
                # Remove TLS settings
                if "streamSettings" in inbound:
                    inbound["streamSettings"]["security"] = "none"
                    inbound["streamSettings"].pop("tlsSettings", None)
                    inbound["streamSettings"].pop("realitySettings", None)
                
                filtered_inbounds.append(inbound)
                logger.info(f"Keeping {protocol} inbound {inbound.get('tag')} for node without domain")
    
    config["inbounds"] = filtered_inbounds
    
    return json.dumps(config, indent=2)


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
            # Filter config based on node's domain/certificates
            node_config = remove_tls_from_config(config_json, node.domain)
            
            # Use REST client for better reliability
            client = NodeRestClient(node)
            result = await client.restart_xray(node_config, users)
            
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
    
    # Filter config based on node's domain/certificates
    node_config = remove_tls_from_config(config_json, node.domain)
    
    # Sync to node with restart using REST API
    client = NodeRestClient(node)
    result = await client.restart_xray(node_config, users)
    
    # Update node status
    node.xray_running = result["running"]
    node.xray_version = result["xray_version"]
    await db.commit()
    
    # Sync Sing-box configuration for Hysteria2 (if node has domain)
    if node.domain:
        try:
            await sync_singbox_to_node(db, node, users)
            logger.info(f"Sing-box configuration synced to node {node.name}")
        except Exception as e:
            logger.error(f"Failed to sync Sing-box to node {node.name}: {e}")
    
    return {
        "success": True,
        "xray_running": result["running"],
        "xray_version": result["xray_version"],
        "inbounds_count": len(inbounds),
        "users_count": len(users)
    }


async def sync_singbox_to_node(db: AsyncSession, node: Node, users: List[User]) -> None:
    """
    Synchronize Sing-box configuration (Hysteria2) to node
    """
    # Get Hysteria2 inbounds
    result = await db.execute(
        select(Inbound).where(
            Inbound.is_enabled == True,
            Inbound.type == 'hysteria2'
        )
    )
    hysteria_inbounds = result.scalars().all()
    
    if not hysteria_inbounds:
        logger.info(f"No Hysteria2 inbounds to sync to node {node.name}")
        return
    
    # Build Sing-box configuration
    builder = SingBoxConfigBuilder()
    
    for inbound in hysteria_inbounds:
        # Get users for this inbound
        inbound_users = [
            user for user in users
            if any(ui.inbound_tag == inbound.tag for ui in user.inbounds)
        ]
        
        if inbound_users:
            builder.add_hysteria2_inbound(inbound, inbound_users, node.domain)
    
    config_json = builder.build()
    
    # Write config to node using gRPC ExecuteCommand (more reliable for file operations)
    try:
        import base64
        config_b64 = base64.b64encode(config_json.encode()).decode()
        command = f"echo '{config_b64}' | base64 -d > /opt/xray-panel-node/singbox_config.json && systemctl restart singbox-node"
        
        client = NodeGRPCClient(node)
        result = await client.execute_command(command)
        
        if result["success"]:
            logger.info(f"Sing-box config synced to node {node.name}, size: {len(config_json)} bytes")
        else:
            logger.error(f"Failed to sync Sing-box to node {node.name}: {result['stderr']}")
            raise Exception(f"Command failed: {result['stderr']}")
    except Exception as e:
        logger.error(f"Failed to sync Sing-box config to node {node.name}: {e}")
        raise
