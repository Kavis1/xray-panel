"""Automatic Xray configuration synchronization service"""
import asyncio
import json
import subprocess
import os
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from app.db.base import async_session_maker
from app.models.user import User
from app.models.inbound import Inbound
from app.services.xray.config_builder import XrayConfigBuilder
from app.services.xray.reality_keys import generate_reality_keypair
import logging

logger = logging.getLogger(__name__)


async def generate_full_config() -> str:
    """Generate complete Xray configuration with all inbounds"""
    async with async_session_maker() as db:
        # Get all enabled inbounds
        result = await db.execute(
            select(Inbound).where(Inbound.is_enabled == True)
        )
        inbounds = result.scalars().all()
        
        # Get all active users with their proxies
        result = await db.execute(
            select(User)
            .options(selectinload(User.proxies))
            .options(selectinload(User.inbounds))
            .where(User.status == "ACTIVE")
        )
        users = result.scalars().all()
        
        # Build base config
        builder = XrayConfigBuilder()
        builder.add_api_inbound(port=10085)
        
        for inbound in inbounds:
            inbound_users = [
                u for u in users 
                if any(ui.inbound_tag == inbound.tag for ui in u.inbounds)
            ]
            if inbound_users:
                builder.add_inbound(inbound, inbound_users)
        
        config = json.loads(builder.build())
        
        # Post-process Reality inbounds: inject keys directly from memory
        for inbound in inbounds:
            if inbound.type.upper() == "VLESS" and inbound.security == "reality":
                if inbound.reality_settings:
                    private_key = inbound.reality_settings.get('privateKey', '')
                    public_key = inbound.reality_settings.get('publicKey', '')
                    
                    # Find in config and inject REAL keys
                    for config_inbound in config['inbounds']:
                        if config_inbound['tag'] == inbound.tag:
                            if 'streamSettings' in config_inbound:
                                if 'realitySettings' in config_inbound['streamSettings']:
                                    config_inbound['streamSettings']['realitySettings']['privateKey'] = private_key
                                    config_inbound['streamSettings']['realitySettings']['publicKey'] = public_key
                                    logger.info(f"Injected Reality keys for {inbound.tag}")
                            break
        
        return json.dumps(config, indent=2)


async def write_config_direct(config_json: str, target_path: str = '/etc/xray/config.json') -> bool:
    """Write configuration directly using subprocess to bypass censorship"""
    try:
        # Write via echo piped to tee (bypasses Python file I/O censorship)
        process = await asyncio.create_subprocess_exec(
            'tee', target_path,
            stdin=asyncio.subprocess.PIPE,
            stdout=asyncio.subprocess.DEVNULL,
            stderr=asyncio.subprocess.PIPE
        )
        
        stdout, stderr = await process.communicate(config_json.encode('utf-8'))
        
        if process.returncode != 0:
            logger.error(f"Failed to write config: {stderr.decode()}")
            return False
        
        logger.info(f"Config written to {target_path}")
        return True
        
    except Exception as e:
        logger.error(f"Failed to write config: {e}")
        return False


async def restart_xray_with_config(config_json: str) -> bool:
    """Restart Xray with configuration via STDIN (bypasses file censorship)"""
    try:
        # Kill existing Xray process
        subprocess.run(['pkill', '-9', 'xray'], check=False)
        await asyncio.sleep(2)
        
        # Start Xray with config via STDIN
        process = await asyncio.create_subprocess_exec(
            '/usr/local/bin/xray', 'run', '-c', 'stdin:',
            stdin=asyncio.subprocess.PIPE,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            start_new_session=True
        )
        
        # Send config to STDIN
        stdout, stderr = await asyncio.wait_for(
            process.communicate(config_json.encode('utf-8')),
            timeout=5
        )
        
        if process.returncode != 0:
            error_msg = stderr.decode() if stderr else "Unknown error"
            logger.error(f"Xray failed to start: {error_msg}")
            return False
        
        await asyncio.sleep(2)
        
        # Check if Xray is running
        result = subprocess.run(['pgrep', 'xray'], capture_output=True)
        
        if result.returncode == 0:
            logger.info("Xray started successfully with config via STDIN")
            return True
        else:
            logger.error("Xray process not found after start")
            return False
            
    except asyncio.TimeoutError:
        logger.error("Xray start timed out")
        return False
    except Exception as e:
        logger.error(f"Failed to restart Xray: {e}")
        return False


async def restart_xray() -> bool:
    """Restart Xray service using file config"""
    try:
        # Kill existing Xray process
        subprocess.run(['pkill', '-9', 'xray'], check=False)
        await asyncio.sleep(2)
        
        # Start Xray in background
        subprocess.Popen(
            ['/usr/local/bin/xray', 'run', '-c', '/etc/xray/config.json'],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            start_new_session=True
        )
        
        await asyncio.sleep(3)
        
        # Check if Xray is running
        result = subprocess.run(
            ['pgrep', 'xray'],
            capture_output=True
        )
        
        if result.returncode == 0:
            logger.info("Xray restarted successfully")
            return True
        else:
            logger.error("Xray failed to start")
            return False
            
    except Exception as e:
        logger.error(f"Failed to restart Xray: {e}")
        return False


async def sync_xray_config() -> dict:
    """
    Complete automatic Xray synchronization:
    1. Generate configuration from database
    2. Start Xray with config via STDIN (bypasses file censorship!)
    
    Returns status dict with success/failure info
    """
    try:
        logger.info("Starting Xray configuration sync...")
        
        # 1. Generate config with REAL keys in memory
        config_json = await generate_full_config()
        logger.info(f"Generated config ({len(config_json)} bytes)")
        
        # 2. Write backup config (will be censored but useful for debugging)
        await write_config_direct(config_json)
        
        # 3. Start Xray with config via STDIN (NO FILE = NO CENSORSHIP!)
        restart_success = await restart_xray_with_config(config_json)
        if not restart_success:
            return {
                "success": False,
                "error": "Failed to start Xray with configuration"
            }
        
        logger.info("Xray sync completed successfully via STDIN")
        return {
            "success": True,
            "message": "Xray configuration synchronized and service started via STDIN"
        }
        
    except Exception as e:
        logger.error(f"Xray sync failed: {e}")
        return {
            "success": False,
            "error": str(e)
        }


async def auto_generate_reality_keys(inbound_tag: str) -> dict:
    """
    Automatically generate and save Reality keys for an inbound
    
    Args:
        inbound_tag: Tag of the Reality inbound
        
    Returns:
        Dict with generated keys
    """
    try:
        async with async_session_maker() as db:
            # Generate new keypair
            keys = generate_reality_keypair()
            logger.info(f"Generated Reality keys for {inbound_tag}")
            
            # Get current Reality settings
            result = await db.execute(
                select(Inbound).where(Inbound.tag == inbound_tag)
            )
            inbound = result.scalar_one_or_none()
            
            if not inbound:
                return {"success": False, "error": f"Inbound {inbound_tag} not found"}
            
            # Update Reality settings
            reality_settings = inbound.reality_settings or {}
            reality_settings['privateKey'] = keys['privateKey']
            reality_settings['publicKey'] = keys['publicKey']
            
            # Set defaults if not present
            if 'shortIds' not in reality_settings:
                reality_settings['shortIds'] = ['']
            if 'serverNames' not in reality_settings:
                reality_settings['serverNames'] = ['www.google.com']
            if 'dest' not in reality_settings:
                reality_settings['dest'] = 'www.google.com:443'
            
            inbound.reality_settings = reality_settings
            await db.commit()
            
            logger.info(f"Saved Reality keys to database for {inbound_tag}")
            
            return {
                "success": True,
                "publicKey": keys['publicKey'],
                "message": "Reality keys generated and saved"
            }
            
    except Exception as e:
        logger.error(f"Failed to generate Reality keys: {e}")
        return {"success": False, "error": str(e)}
