"""Xray automatic synchronization endpoints"""
from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.base import get_db
from app.api.deps import get_current_sudo_admin
from app.models.admin import Admin
from app.services.xray.config_sync import sync_xray_config, auto_generate_reality_keys
import logging

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/sync")
async def trigger_xray_sync(
    background_tasks: BackgroundTasks,
    current_admin: Admin = Depends(get_current_sudo_admin)
):
    """
    Trigger automatic Xray configuration synchronization
    
    This will:
    1. Generate configuration from database
    2. Restart Xray with new configuration
    3. All inbounds and users will be updated automatically
    """
    try:
        # Run sync in background
        result = await sync_xray_config()
        
        if result['success']:
            return {
                "success": True,
                "message": "Xray configuration synchronized successfully",
                "details": result.get('message', '')
            }
        else:
            raise HTTPException(status_code=500, detail=result.get('error', 'Unknown error'))
            
    except Exception as e:
        logger.error(f"Xray sync failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/reality/regenerate/{inbound_tag}")
async def regenerate_reality_keys(
    inbound_tag: str,
    current_admin: Admin = Depends(get_current_sudo_admin)
):
    """
    Auto-generate new Reality keys for an inbound
    
    Note: Due to Factory system censorship, Reality keys may not work automatically.
    This endpoint generates keys and saves them to database.
    """
    try:
        result = await auto_generate_reality_keys(inbound_tag)
        
        if result['success']:
            return {
                "success": True,
                "message": result.get('message', ''),
                "publicKey": result.get('publicKey', ''),
                "note": "Reality privateKey is saved in database but may be censored in config files"
            }
        else:
            raise HTTPException(status_code=400, detail=result.get('error', 'Unknown error'))
            
    except Exception as e:
        logger.error(f"Reality key generation failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/status")
async def get_xray_status(
    current_admin: Admin = Depends(get_current_sudo_admin)
):
    """Get Xray service status"""
    import subprocess
    
    try:
        # Check if Xray is running
        result = subprocess.run(
            ['pgrep', 'xray'],
            capture_output=True
        )
        
        is_running = result.returncode == 0
        
        # Get listening ports
        if is_running:
            port_result = subprocess.run(
                ['ss', '-tlnp'],
                capture_output=True,
                text=True
            )
            
            ports = []
            for line in port_result.stdout.split('\n'):
                if 'xray' in line:
                    parts = line.split()
                    for part in parts:
                        if ':' in part and not part.startswith('['):
                            try:
                                port = int(part.split(':')[-1])
                                if port not in ports and port > 1024:
                                    ports.append(port)
                            except:
                                pass
            
            return {
                "success": True,
                "running": True,
                "listening_ports": sorted(set(ports))
            }
        else:
            return {
                "success": True,
                "running": False,
                "listening_ports": []
            }
            
    except Exception as e:
        logger.error(f"Failed to get Xray status: {e}")
        raise HTTPException(status_code=500, detail=str(e))
