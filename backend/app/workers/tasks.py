from datetime import datetime, timedelta
from typing import List
from celery import Task
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.workers.celery_app import celery_app
from app.db.base import async_session_maker
from app.models.user import User, UserStatus, TrafficLimitStrategy
from app.models.node import Node
from app.models.webhook import WebhookQueue
from app.services.node.grpc_client import NodeGRPCClient
from app.services.webhook.sender import WebhookSender
import logging

logger = logging.getLogger(__name__)


class AsyncTask(Task):
    async def run_async(self, *args, **kwargs):
        raise NotImplementedError

    def __call__(self, *args, **kwargs):
        import asyncio
        return asyncio.run(self.run_async(*args, **kwargs))


async def collect_node_stats_async():
    """Collect statistics from all nodes using direct Xray check"""
    import subprocess
    import json as json_lib
    import requests
    
    async with async_session_maker() as session:
        result = await session.execute(
            select(Node).where(Node.is_enabled == True)
        )
        nodes = result.scalars().all()

        for node in nodes:
            try:
                # Check if this is local node or remote
                is_local = node.address in ['127.0.0.1', 'localhost', '::1']
                
                if is_local:
                    # For local node: use systemctl directly
                    xray_check = subprocess.run(
                        ['/usr/bin/systemctl', 'is-active', 'xray-panel.service'],
                        capture_output=True,
                        text=True,
                        timeout=2
                    )
                    xray_running = xray_check.returncode == 0
                    
                    # Get Xray version locally
                    if xray_running:
                        version_check = subprocess.run(
                            ['/usr/local/bin/xray', 'version'],
                            capture_output=True,
                            text=True,
                            timeout=2
                        )
                        xray_version = version_check.stdout.split('\n')[0] if version_check.returncode == 0 else "Unknown"
                    else:
                        xray_version = None
                else:
                    # For remote node: use gRPC to get status
                    from app.services.node.grpc_client import NodeGRPCClient
                    
                    try:
                        client = NodeGRPCClient(node)
                        
                        # Get node info via gRPC
                        node_info = await client.get_info()
                        
                        xray_running = node_info.get('running', False)
                        xray_version = node_info.get('xray_version', 'Unknown')
                        
                        # Update additional node info
                        node.core_type = node_info.get('core_type')
                        node.uptime_seconds = node_info.get('uptime')
                        
                    except Exception as grpc_error:
                        logger.warning(f"Failed to connect to remote node {node.name} via gRPC: {grpc_error}")
                        xray_running = False
                        xray_version = None
                        node.is_connected = False
                
                # Update node status
                node.xray_running = xray_running
                node.is_connected = True
                node.xray_version = xray_version
                
                # Collect node traffic - sum of users who use inbounds on this node
                # Node traffic = sum of user traffic for users using this node's inbounds
                if xray_running:
                    # Get all inbounds that belong to this node
                    from app.models.inbound import Inbound
                    inbounds_result = await session.execute(
                        select(Inbound).where(Inbound.node_ids.contains([node.id]))
                    )
                    node_inbounds = inbounds_result.scalars().all()
                    node_inbound_ids = [inbound.id for inbound in node_inbounds]
                    
                    if node_inbound_ids:
                        # Get users who have these inbounds
                        users_result = await session.execute(
                            select(User).where(User.status == UserStatus.ACTIVE.value)
                        )
                        all_users = users_result.scalars().all()
                        
                        # Filter users who have at least one inbound from this node
                        node_users = [
                            user for user in all_users
                            if user.inbounds and any(inbound.id in node_inbound_ids for inbound in user.inbounds)
                        ]
                        
                        # Sum traffic only for users on this node
                        node_total = sum(u.traffic_used_bytes for u in node_users if u.traffic_used_bytes)
                        node.traffic_used_bytes = node_total
                        
                        if node_total > 0:
                            logger.info(f"  Node traffic: {node_total:,} bytes ({node_total/1024/1024:.2f} MB) from {len(node_users)} users")
                    else:
                        node.traffic_used_bytes = 0
                        logger.info(f"  Node has no inbounds, traffic set to 0")
                
                logger.info(f"✅ Node {node.name}: Xray={xray_running}, Version={xray_version}")
                
            except Exception as e:
                node.is_connected = False
                node.xray_running = False
                logger.error(f"Failed to collect stats from node {node.name}: {e}")
        
        await session.commit()


async def collect_user_traffic_stats_async():
    """Collect traffic statistics using Xray CLI + sing-box stats"""
    import subprocess
    import json as json_lib
    import requests
    
    async with async_session_maker() as session:
        # Get active users
        result = await session.execute(
            select(User).where(User.status == UserStatus.ACTIVE.value)
        )
        users = result.scalars().all()
        
        for user in users:
            email = user.email or user.username
            total_bytes = 0
            
            # 1. Collect from Xray
            try:
                result = subprocess.run(
                    ['xray', 'api', 'statsquery',
                     '--server=127.0.0.1:10085',
                     '-reset=false',
                     f'-pattern=user>>>{email}'],
                    capture_output=True,
                    text=True,
                    timeout=5
                )
                
                if result.returncode == 0:
                    data = json_lib.loads(result.stdout)
                    stats = data.get('stat', [])
                    
                    xray_up = 0
                    xray_down = 0
                    
                    for stat in stats:
                        name = stat.get('name', '')
                        value = stat.get('value', 0)
                        
                        if 'uplink' in name:
                            xray_up += value
                        elif 'downlink' in name:
                            xray_down += value
                    
                    xray_total = xray_up + xray_down
                    total_bytes += xray_total
                    
                    if xray_total > 0:
                        logger.info(f"  Xray {user.username}: {xray_total:,} bytes")
                    
            except Exception as e:
                logger.warning(f"Xray stats error for {user.username}: {e}")
            
            # 2. Collect from sing-box (Hysteria traffic via Clash API)
            # Note: sing-box doesn't have per-user stats, so we collect total traffic
            # and distribute proportionally or assign to first active user
            try:
                # sing-box Clash API provides cumulative traffic counters
                response = requests.get('http://127.0.0.1:9090/connections', timeout=2)
                if response.status_code == 200:
                    data = response.json()
                    
                    # Use cumulative totals instead of per-connection stats
                    singbox_up = data.get('uploadTotal', 0)
                    singbox_down = data.get('downloadTotal', 0)
                    singbox_total = singbox_up + singbox_down
                    
                    # Store in first active user (limitation: no per-user stats in sing-box)
                    # TODO: implement proper user identification if needed
                    if singbox_total > 0 and user.id == users[0].id:
                        total_bytes += singbox_total
                        logger.info(f"  sing-box total: {singbox_total:,} bytes ({singbox_total/1024/1024:.2f} MB)")
                
            except Exception as e:
                logger.debug(f"sing-box stats error: {e}")
            
            # Update total traffic
            if total_bytes > 0:
                user.traffic_used_bytes = total_bytes
                logger.info(f"✅ Updated {user.username}: {total_bytes:,} bytes ({total_bytes/1024/1024:.2f} MB)")
        
        await session.commit()
        logger.info(f"Traffic collection completed for {len(users)} users")


async def check_user_connection_limits_async():
    """Check and enforce max_connections limit for users"""
    async with async_session_maker() as session:
        # Get users with connection limits
        result = await session.execute(
            select(User).where(
                User.status == UserStatus.ACTIVE.value,
                User.max_connections.isnot(None)
            )
        )
        users = result.scalars().all()
        
        if not users:
            return
        
        # Get online nodes
        nodes_result = await session.execute(
            select(Node).where(Node.is_connected == True, Node.is_enabled == True, Node.xray_running == True)
        )
        nodes = nodes_result.scalars().all()
        
        for user in users:
            total_connections = 0
            
            # Count connections across all nodes
            for node in nodes:
                try:
                    client = NodeGRPCClient(node)
                    online_users = await client.get_online_users()
                    
                    email = user.email or user.username
                    if email in online_users:
                        total_connections += online_users[email]["connection_count"]
                    
                except Exception as e:
                    logger.warning(f"Failed to get online users from node {node.name}: {e}")
            
            # Check if limit exceeded
            if total_connections > user.max_connections:
                logger.warning(
                    f"User {user.username} exceeded connection limit: "
                    f"{total_connections}/{user.max_connections}"
                )
                
                # Optionally disable user or send webhook
                # user.status = UserStatus.LIMITED.value
                
                # Trigger webhook for exceeded connection limit
                webhook_item = WebhookQueue(
                    webhook_type="user_connection_limit_exceeded",
                    payload={
                        "user_id": user.id,
                        "username": user.username,
                        "email": user.email,
                        "current_connections": total_connections,
                        "max_connections": user.max_connections
                    },
                    status="pending",
                    next_try_at=datetime.utcnow(),
                    tries=0,
                    max_tries=3
                )
                session.add(webhook_item)
        
        await session.commit()


async def check_user_expiration_async():
    """Check and update expired users"""
    async with async_session_maker() as session:
        now = datetime.utcnow()
        
        result = await session.execute(
            select(User).where(
                User.status == UserStatus.ACTIVE.value,
                User.expire_at.isnot(None),
                User.expire_at <= now
            )
        )
        users = result.scalars().all()

        for user in users:
            user.status = UserStatus.EXPIRED.value
            
            # Trigger webhook
            webhook_item = WebhookQueue(
                webhook_type="user_expired",
                payload={
                    "user_id": user.id,
                    "username": user.username,
                    "email": user.email,
                    "expired_at": user.expire_at.isoformat() if user.expire_at else None
                },
                status="pending",
                next_try_at=datetime.utcnow(),
                tries=0,
                max_tries=3
            )
            session.add(webhook_item)
            logger.info(f"User {user.username} expired, webhook queued")
            
        await session.commit()


async def check_traffic_limits_async():
    """Check users who exceeded traffic limits"""
    async with async_session_maker() as session:
        result = await session.execute(
            select(User).where(
                User.status == UserStatus.ACTIVE.value,
                User.traffic_limit_bytes.isnot(None)
            )
        )
        users = result.scalars().all()

        for user in users:
            if user.traffic_used_bytes >= user.traffic_limit_bytes:
                user.status = UserStatus.LIMITED.value
                
                # Trigger webhook
                webhook_item = WebhookQueue(
                    webhook_type="user_traffic_limit",
                    payload={
                        "user_id": user.id,
                        "username": user.username,
                        "email": user.email,
                        "traffic_used": user.traffic_used_bytes,
                        "traffic_limit": user.traffic_limit_bytes
                    },
                    status="pending",
                    next_try_at=datetime.utcnow(),
                    tries=0,
                    max_tries=3
                )
                session.add(webhook_item)
                logger.info(f"User {user.username} exceeded traffic limit, webhook queued")
                
        await session.commit()


async def process_webhook_queue_async():
    """Process pending webhooks"""
    async with async_session_maker() as session:
        now = datetime.utcnow()
        
        result = await session.execute(
            select(WebhookQueue).where(
                WebhookQueue.status == "pending",
                WebhookQueue.next_try_at <= now,
                WebhookQueue.tries < WebhookQueue.max_tries
            ).limit(50)
        )
        queue_items = result.scalars().all()

        sender = WebhookSender()
        
        for item in queue_items:
            try:
                await sender.send(item)
                item.status = "success"
            except Exception as e:
                item.tries += 1
                item.error_message = str(e)
                item.next_try_at = now + timedelta(seconds=60 * item.tries)
                
                if item.tries >= item.max_tries:
                    item.status = "failed"
            
            item.updated_at = now
        
        await session.commit()


async def reset_periodic_traffic_async():
    """Reset traffic for users with periodic reset strategy"""
    async with async_session_maker() as session:
        now = datetime.utcnow()
        
        # Daily reset
        result = await session.execute(
            select(User).where(
                User.traffic_limit_strategy == TrafficLimitStrategy.DAY.value,
            )
        )
        users = result.scalars().all()
        
        for user in users:
            if not user.last_traffic_reset_at or \
               (now - user.last_traffic_reset_at).days >= 1:
                user.traffic_used_bytes = 0
                user.last_traffic_reset_at = now
        
        # Weekly reset
        result = await session.execute(
            select(User).where(
                User.traffic_limit_strategy == TrafficLimitStrategy.WEEK.value,
            )
        )
        users = result.scalars().all()
        
        for user in users:
            if not user.last_traffic_reset_at or \
               (now - user.last_traffic_reset_at).days >= 7:
                user.traffic_used_bytes = 0
                user.last_traffic_reset_at = now
        
        # Monthly reset
        result = await session.execute(
            select(User).where(
                User.traffic_limit_strategy == TrafficLimitStrategy.MONTH.value,
            )
        )
        users = result.scalars().all()
        
        for user in users:
            if not user.last_traffic_reset_at or \
               (now - user.last_traffic_reset_at).days >= 30:
                user.traffic_used_bytes = 0
                user.last_traffic_reset_at = now
        
        await session.commit()


# Celery task wrappers
@celery_app.task
def collect_node_stats():
    """Celery task wrapper"""
    import asyncio
    return asyncio.run(collect_node_stats_async())


@celery_app.task
def collect_user_traffic_stats():
    """Celery task wrapper"""
    import asyncio
    return asyncio.run(collect_user_traffic_stats_async())


@celery_app.task
def check_user_connection_limits():
    """Celery task wrapper"""
    import asyncio
    return asyncio.run(check_user_connection_limits_async())


@celery_app.task
def check_user_expiration():
    """Celery task wrapper"""
    import asyncio
    return asyncio.run(check_user_expiration_async())


@celery_app.task
def check_traffic_limits():
    """Celery task wrapper"""
    import asyncio
    return asyncio.run(check_traffic_limits_async())


@celery_app.task
def process_webhook_queue():
    """Celery task wrapper"""
    import asyncio
    return asyncio.run(process_webhook_queue_async())


@celery_app.task
def reset_periodic_traffic():
    """Celery task wrapper"""
    import asyncio
    return asyncio.run(reset_periodic_traffic_async())
