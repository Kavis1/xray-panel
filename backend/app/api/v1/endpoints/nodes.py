from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from app.db.base import get_db
from app.models.admin import Admin
from app.models.node import Node
from app.models.user import User
from app.models.inbound import Inbound
from app.schemas.node import NodeCreate, NodeUpdate, NodeResponse
from app.api.deps import get_current_admin
from app.services.node.grpc_client import NodeGRPCClient
from app.services.xray.config_builder import XrayConfigBuilder
from app.services.ssl.certificate_manager import CertificateManager
import logging

logger = logging.getLogger(__name__)

router = APIRouter()
cert_manager = CertificateManager()


@router.get("/", response_model=List[NodeResponse])
async def list_nodes(
    db: AsyncSession = Depends(get_db),
    current_admin: Admin = Depends(get_current_admin),
    skip: int = 0,
    limit: int = 100,
    online_only: bool = False,
):
    query = select(Node).order_by(Node.view_position)
    
    if online_only:
        query = query.where(Node.is_connected == True)
    
    result = await db.execute(query.offset(skip).limit(limit))
    nodes = result.scalars().all()
    return nodes


@router.post("/generate-ssl")
async def generate_ssl_certificate(
    node_name: str,
    node_address: str,
    current_admin: Admin = Depends(get_current_admin),
):
    """Generate SSL certificate for node BEFORE creating it"""
    try:
        import ipaddress
        # Validate if address is IP
        try:
            ipaddress.ip_address(node_address)
            node_ip = node_address
        except ValueError:
            # It's a domain, use as-is
            node_ip = node_address
        
        # Generate with temporary ID (will be replaced when node is created)
        import time
        temp_id = int(time.time())
        
        certs = cert_manager.generate_node_certificate(
            node_id=temp_id,
            node_name=node_name,
            node_address=node_ip
        )
        
        logger.info(f"Generated SSL certificate for pre-creation: {node_name}")
        
        return {
            "success": True,
            "name": node_name,
            "address": node_address,
            "ca_certificate": certs["ca_certificate"],
            "client_certificate": certs["certificate"],
            "client_key": certs["private_key"],
        }
        
    except Exception as e:
        logger.error(f"Failed to generate SSL certificate: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate SSL certificate: {str(e)}",
        )


@router.post("/", response_model=NodeResponse, status_code=status.HTTP_201_CREATED)
async def create_node(
    node_data: NodeCreate,
    db: AsyncSession = Depends(get_db),
    current_admin: Admin = Depends(get_current_admin),
):
    result = await db.execute(select(Node).where(Node.name == node_data.name))
    existing_node = result.scalar_one_or_none()
    
    if existing_node:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Node name already exists",
        )
    
    new_node = Node(
        name=node_data.name,
        address=node_data.address,
        api_port=node_data.api_port,
        api_protocol=node_data.api_protocol,
        api_key=node_data.api_key,
        usage_ratio=node_data.usage_ratio,
        traffic_limit_bytes=node_data.traffic_limit_bytes,
        traffic_notify_percent=node_data.traffic_notify_percent,
        country_code=node_data.country_code,
        view_position=node_data.view_position,
        add_host_to_inbounds=node_data.add_host_to_inbounds,
    )
    
    db.add(new_node)
    await db.commit()
    await db.refresh(new_node)
    
    # AUTOMATICALLY generate SSL certificates for the node
    try:
        import ipaddress
        # Validate if address is IP
        try:
            ipaddress.ip_address(node_data.address)
            node_ip = node_data.address
        except ValueError:
            # It's a domain, use as-is
            node_ip = node_data.address
        
        certs = cert_manager.generate_node_certificate(
            node_id=new_node.id,
            node_name=new_node.name,
            node_address=node_ip
        )
        
        # Save SSL paths to database
        new_node.ssl_cert = certs["cert_file"]
        new_node.ssl_key = certs["key_file"]
        new_node.ssl_ca = str(cert_manager.CA_CERT_FILE)
        
        await db.commit()
        await db.refresh(new_node)
        
        logger.info(f"Created node {new_node.id} ({new_node.name}) with SSL")
    except Exception as e:
        logger.warning(f"Failed to generate SSL for node {new_node.id}: {e}")
        logger.info(f"Created node {new_node.id} ({new_node.name}) WITHOUT SSL")
    
    return new_node


@router.get("/{node_id}", response_model=NodeResponse)
async def get_node(
    node_id: int,
    db: AsyncSession = Depends(get_db),
    current_admin: Admin = Depends(get_current_admin),
):
    result = await db.execute(select(Node).where(Node.id == node_id))
    node = result.scalar_one_or_none()
    
    if not node:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Node not found",
        )
    
    return node


@router.patch("/{node_id}", response_model=NodeResponse)
async def update_node(
    node_id: int,
    node_data: NodeUpdate,
    db: AsyncSession = Depends(get_db),
    current_admin: Admin = Depends(get_current_admin),
):
    result = await db.execute(select(Node).where(Node.id == node_id))
    node = result.scalar_one_or_none()
    
    if not node:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Node not found",
        )
    
    update_data = node_data.model_dump(exclude_unset=True)
    
    for field, value in update_data.items():
        setattr(node, field, value)
    
    await db.commit()
    await db.refresh(node)
    
    return node


@router.delete("/{node_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_node(
    node_id: int,
    db: AsyncSession = Depends(get_db),
    current_admin: Admin = Depends(get_current_admin),
):
    result = await db.execute(select(Node).where(Node.id == node_id))
    node = result.scalar_one_or_none()
    
    if not node:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Node not found",
        )
    
    await db.delete(node)
    await db.commit()


@router.post("/{node_id}/connect")
async def connect_node(
    node_id: int,
    db: AsyncSession = Depends(get_db),
    current_admin: Admin = Depends(get_current_admin),
):
    result = await db.execute(select(Node).where(Node.id == node_id))
    node = result.scalar_one_or_none()
    
    if not node:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Node not found",
        )
    
    # Try to connect to node via gRPC
    try:
        client = NodeGRPCClient(node)
        info = await client.get_info()
        
        # Update node with connection info
        node.is_connected = True
        node.xray_running = info["running"]
        node.xray_version = info.get("xray_version")
        node.node_version = info.get("version")
        node.core_type = info.get("core_type", "xray")
        await db.commit()
        
        return {
            "success": True,
            "message": "Node connected successfully",
            "xray_running": info["running"],
            "xray_version": info.get("xray_version"),
            "node_version": info.get("version")
        }
        
    except Exception as e:
        logger.error(f"Failed to connect to node {node_id}: {e}")
        node.is_connected = False
        node.xray_running = False
        await db.commit()
        
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to connect to node: {str(e)}",
        )


@router.post("/{node_id}/disconnect")
async def disconnect_node(
    node_id: int,
    db: AsyncSession = Depends(get_db),
    current_admin: Admin = Depends(get_current_admin),
):
    result = await db.execute(select(Node).where(Node.id == node_id))
    node = result.scalar_one_or_none()
    
    if not node:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Node not found",
        )
    
    # Try to stop Xray on node before disconnecting
    try:
        client = NodeGRPCClient(node)
        await client.stop_xray()
        logger.info(f"Stopped Xray on node {node_id} before disconnect")
    except Exception as e:
        logger.warning(f"Failed to stop Xray on node {node_id}: {e}")
    
    node.is_connected = False
    node.xray_running = False
    await db.commit()
    
    return {"success": True, "message": "Node disconnected"}


@router.post("/{node_id}/sync")
async def sync_node_config(
    node_id: int,
    db: AsyncSession = Depends(get_db),
    current_admin: Admin = Depends(get_current_admin),
):
    """Synchronize Xray configuration to node and start/restart Xray"""
    # 1. Get node
    result = await db.execute(select(Node).where(Node.id == node_id))
    node = result.scalar_one_or_none()
    
    if not node:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Node not found",
        )
    
    if not node.is_connected:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Node is not connected",
        )
    
    try:
        # 2. Get all enabled inbounds
        result = await db.execute(
            select(Inbound).where(Inbound.is_enabled == True)
        )
        inbounds = result.scalars().all()
        
        if not inbounds:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No enabled inbounds found",
            )
        
        # 3. Get all active users with their proxies and inbounds
        result = await db.execute(
            select(User)
            .options(selectinload(User.proxies))
            .options(selectinload(User.inbounds))
            .where(User.status == "ACTIVE")
        )
        users = result.scalars().all()
        
        # 4. Build Xray configuration
        builder = XrayConfigBuilder()
        builder.add_api_inbound(port=10085)
        
        for inbound in inbounds:
            # Get users assigned to this inbound
            inbound_users = [
                user for user in users
                if any(ui.inbound_tag == inbound.tag for ui in user.inbounds)
            ]
            
            if inbound_users:
                builder.add_inbound(inbound, inbound_users)
        
        config_json = builder.build()
        
        # 5. Send configuration to node via gRPC
        client = NodeGRPCClient(node)
        result = await client.start_xray(config_json, users)
        
        # 6. Update node status
        node.xray_running = result["running"]
        node.xray_version = result["xray_version"]
        await db.commit()
        await db.refresh(node)
        
        return {
            "success": True,
            "message": "Configuration synced successfully",
            "xray_running": result["running"],
            "xray_version": result["xray_version"],
            "inbounds_count": len(inbounds),
            "users_count": len(users)
        }
        
    except Exception as e:
        logger.error(f"Failed to sync node {node_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to sync configuration: {str(e)}",
        )


@router.get("/{node_id}/status")
async def get_node_status(
    node_id: int,
    db: AsyncSession = Depends(get_db),
    current_admin: Admin = Depends(get_current_admin),
):
    """Get node status from gRPC"""
    result = await db.execute(select(Node).where(Node.id == node_id))
    node = result.scalar_one_or_none()
    
    if not node:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Node not found",
        )
    
    try:
        client = NodeGRPCClient(node)
        info = await client.get_info()
        
        # Update node status
        node.xray_running = info["running"]
        node.xray_version = info["xray_version"]
        await db.commit()
        
        return info
        
    except Exception as e:
        logger.error(f"Failed to get node {node_id} status: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get node status: {str(e)}",
        )
