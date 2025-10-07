"""REST API client for node communication (Marzban-style)"""
import logging
import httpx
from typing import Dict, Any, List
from app.models.node import Node
from app.models.user import User

logger = logging.getLogger(__name__)


class NodeRestClient:
    """REST API client for node communication"""
    
    def __init__(self, node: Node):
        self.node = node
        self.base_url = f"http://{node.address}:8080"
        self.session_id = None
        self.timeout = 30.0
    
    async def connect(self) -> Dict[str, Any]:
        """Connect to node and get session ID"""
        async with httpx.AsyncClient(timeout=self.timeout, verify=False) as client:
            response = await client.post(f"{self.base_url}/connect")
            response.raise_for_status()
            data = response.json()
            self.session_id = data.get("session_id")
            logger.info(f"Connected to node {self.node.name}, session: {self.session_id}")
            return data
    
    async def disconnect(self) -> Dict[str, Any]:
        """Disconnect from node"""
        async with httpx.AsyncClient(timeout=self.timeout, verify=False) as client:
            response = await client.post(
                f"{self.base_url}/disconnect",
                json={"session_id": self.session_id}
            )
            response.raise_for_status()
            self.session_id = None
            return response.json()
    
    async def ping(self) -> bool:
        """Ping node"""
        try:
            async with httpx.AsyncClient(timeout=5.0, verify=False) as client:
                response = await client.post(
                    f"{self.base_url}/ping",
                    json={"session_id": self.session_id}
                )
                return response.status_code == 200
        except:
            return False
    
    async def get_info(self) -> Dict[str, Any]:
        """Get node info"""
        async with httpx.AsyncClient(timeout=self.timeout, verify=False) as client:
            response = await client.get(f"{self.base_url}/")
            response.raise_for_status()
            return response.json()
    
    async def start_xray(self, config: str, users: List[User]) -> Dict[str, Any]:
        """Start Xray with config"""
        if not self.session_id:
            await self.connect()
        
        async with httpx.AsyncClient(timeout=self.timeout, verify=False) as client:
            response = await client.post(
                f"{self.base_url}/start",
                json={
                    "session_id": self.session_id,
                    "config": config
                }
            )
            
            # If already started, restart instead
            if response.status_code == 409:
                return await self.restart_xray(config, users)
            
            response.raise_for_status()
            data = response.json()
            
            logger.info(f"Xray started on node {self.node.name}")
            return {
                "running": data.get("started", False),
                "xray_version": data.get("core_version", ""),
                "session_id": self.session_id
            }
    
    async def stop_xray(self) -> Dict[str, Any]:
        """Stop Xray"""
        if not self.session_id:
            await self.connect()
        
        async with httpx.AsyncClient(timeout=self.timeout, verify=False) as client:
            response = await client.post(
                f"{self.base_url}/stop",
                json={"session_id": self.session_id}
            )
            response.raise_for_status()
            
            logger.info(f"Xray stopped on node {self.node.name}")
            return response.json()
    
    async def restart_xray(self, config: str, users: List[User]) -> Dict[str, Any]:
        """Restart Xray with new config"""
        if not self.session_id:
            await self.connect()
        
        async with httpx.AsyncClient(timeout=self.timeout, verify=False) as client:
            response = await client.post(
                f"{self.base_url}/restart",
                json={
                    "session_id": self.session_id,
                    "config": config
                }
            )
            response.raise_for_status()
            data = response.json()
            
            logger.info(f"Xray restarted on node {self.node.name}")
            return {
                "running": data.get("started", False),
                "xray_version": data.get("core_version", ""),
                "session_id": self.session_id
            }
