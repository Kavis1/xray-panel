#!/usr/bin/env python3
import asyncio
import sys
from typing import Optional

import click
from sqlalchemy import select
from app.db.base import async_session_maker
from app.models.admin import Admin
from app.models.user import User
from app.models.node import Node
from app.core.security import get_password_hash


@click.group()
def cli():
    """Xray Panel CLI"""
    pass


@cli.group()
def admin():
    """Admin management commands"""
    pass


@admin.command("create")
@click.option("--username", prompt=True, help="Admin username")
@click.option("--password", prompt=True, hide_input=True, confirmation_prompt=True, help="Admin password")
@click.option("--sudo", is_flag=True, help="Grant sudo privileges")
def admin_create(username: str, password: str, sudo: bool):
    """Create a new admin"""
    async def _create():
        async with async_session_maker() as session:
            result = await session.execute(
                select(Admin).where(Admin.username == username)
            )
            existing = result.scalar_one_or_none()
            
            if existing:
                click.echo(f"Error: Admin '{username}' already exists", err=True)
                sys.exit(1)
            
            new_admin = Admin(
                username=username,
                hashed_password=get_password_hash(password),
                is_sudo=sudo,
                is_active=True,
            )
            
            session.add(new_admin)
            await session.commit()
            
            click.echo(f"✓ Admin '{username}' created successfully")
            if sudo:
                click.echo("  Sudo privileges: Yes")
    
    asyncio.run(_create())


@admin.command("list")
def admin_list():
    """List all admins"""
    async def _list():
        async with async_session_maker() as session:
            result = await session.execute(select(Admin))
            admins = result.scalars().all()
            
            if not admins:
                click.echo("No admins found")
                return
            
            click.echo("\nAdmins:")
            click.echo("-" * 60)
            for admin in admins:
                status = "✓" if admin.is_active else "✗"
                sudo = " [SUDO]" if admin.is_sudo else ""
                click.echo(f"{status} {admin.username}{sudo} (ID: {admin.id})")
    
    asyncio.run(_list())


@cli.group()
def user():
    """User management commands"""
    pass


@user.command("add")
@click.option("--username", prompt=True, help="Username")
@click.option("--expire", help="Expiration date (YYYY-MM-DD)")
@click.option("--traffic", help="Traffic limit in GB")
def user_add(username: str, expire: Optional[str], traffic: Optional[str]):
    """Add a new user"""
    async def _add():
        from datetime import datetime
        
        async with async_session_maker() as session:
            result = await session.execute(
                select(User).where(User.username == username)
            )
            existing = result.scalar_one_or_none()
            
            if existing:
                click.echo(f"Error: User '{username}' already exists", err=True)
                sys.exit(1)
            
            expire_at = None
            if expire:
                expire_at = datetime.strptime(expire, "%Y-%m-%d")
            
            traffic_bytes = None
            if traffic:
                traffic_bytes = int(float(traffic) * 1024 * 1024 * 1024)
            
            new_user = User(
                username=username,
                status="ACTIVE",
                expire_at=expire_at,
                traffic_limit_bytes=traffic_bytes,
            )
            
            session.add(new_user)
            await session.commit()
            
            click.echo(f"✓ User '{username}' created successfully")
    
    asyncio.run(_add())


@user.command("list")
@click.option("--status", type=click.Choice(["ACTIVE", "DISABLED", "LIMITED", "EXPIRED"]))
def user_list(status: Optional[str]):
    """List all users"""
    async def _list():
        async with async_session_maker() as session:
            query = select(User)
            if status:
                query = query.where(User.status == status)
            
            result = await session.execute(query)
            users = result.scalars().all()
            
            if not users:
                click.echo("No users found")
                return
            
            click.echo("\nUsers:")
            click.echo("-" * 80)
            for user in users:
                traffic = f"{user.traffic_used_bytes / 1024 / 1024 / 1024:.2f}GB"
                click.echo(f"[{user.status}] {user.username} - Traffic: {traffic} (ID: {user.id})")
    
    asyncio.run(_list())


@cli.group()
def node():
    """Node management commands"""
    pass


@node.command("list")
def node_list():
    """List all nodes"""
    async def _list():
        async with async_session_maker() as session:
            result = await session.execute(select(Node))
            nodes = result.scalars().all()
            
            if not nodes:
                click.echo("No nodes found")
                return
            
            click.echo("\nNodes:")
            click.echo("-" * 80)
            for node in nodes:
                status = "✓ Online" if node.is_connected else "✗ Offline"
                click.echo(f"{status} {node.name} - {node.address}:{node.api_port} (ID: {node.id})")
    
    asyncio.run(_list())


if __name__ == "__main__":
    cli()
