"""Firewall management for nodes"""
import logging
from typing import List, Dict, Any
from app.services.node.grpc_client import NodeGRPCClient
from app.models.node import Node

logger = logging.getLogger(__name__)


class FirewallManager:
    """Manage firewall rules on nodes"""
    
    @staticmethod
    async def open_port_on_node(node: Node, port: int, protocol: str = "tcp") -> Dict[str, Any]:
        """
        Open a port on a specific node via gRPC
        
        Args:
            node: Node instance
            port: Port number to open
            protocol: Protocol (tcp/udp)
            
        Returns:
            Dict with success status and message
        """
        try:
            client = NodeGRPCClient(node)
            
            # Send firewall command to node
            # The node service should handle ufw/iptables commands
            result = await client.open_firewall_port(port, protocol)
            
            logger.info(f"Opened port {port}/{protocol} on node {node.name}")
            return {
                "success": True,
                "message": f"Port {port}/{protocol} opened on {node.name}",
                "details": result
            }
            
        except Exception as e:
            logger.error(f"Failed to open port {port} on node {node.name}: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    @staticmethod
    async def open_port_on_all_nodes(nodes: List[Node], port: int, protocol: str = "tcp") -> Dict[str, Any]:
        """
        Open a port on all nodes
        
        Args:
            nodes: List of Node instances
            port: Port number to open
            protocol: Protocol (tcp/udp)
            
        Returns:
            Dict with results for each node
        """
        results = []
        
        for node in nodes:
            result = await FirewallManager.open_port_on_node(node, port, protocol)
            results.append({
                "node_id": node.id,
                "node_name": node.name,
                **result
            })
        
        return {
            "total_nodes": len(nodes),
            "results": results
        }
    
    @staticmethod
    def open_local_port(port: int, protocol: str = "tcp") -> Dict[str, Any]:
        """
        Open a port on the local server (panel server)
        
        Args:
            port: Port number to open
            protocol: Protocol (tcp/udp)
            
        Returns:
            Dict with success status
        """
        import subprocess
        
        try:
            # Try UFW first
            ufw_check = subprocess.run(
                ["which", "ufw"],
                capture_output=True,
                timeout=2
            )
            
            if ufw_check.returncode == 0:
                # UFW is available
                result = subprocess.run(
                    ["ufw", "allow", f"{port}/{protocol}"],
                    capture_output=True,
                    text=True,
                    timeout=5
                )
                
                if result.returncode == 0:
                    logger.info(f"Opened port {port}/{protocol} locally via UFW")
                    return {
                        "success": True,
                        "method": "ufw",
                        "message": f"Port {port}/{protocol} opened via UFW"
                    }
                else:
                    logger.warning(f"UFW command failed: {result.stderr}")
            
            # Try iptables as fallback
            result = subprocess.run(
                [
                    "iptables", "-I", "INPUT", "-p", protocol,
                    "--dport", str(port), "-j", "ACCEPT"
                ],
                capture_output=True,
                text=True,
                timeout=5
            )
            
            if result.returncode == 0:
                # Save iptables rules
                subprocess.run(["iptables-save"], timeout=5)
                
                logger.info(f"Opened port {port}/{protocol} locally via iptables")
                return {
                    "success": True,
                    "method": "iptables",
                    "message": f"Port {port}/{protocol} opened via iptables"
                }
            else:
                raise Exception(f"iptables failed: {result.stderr}")
                
        except Exception as e:
            logger.error(f"Failed to open local port {port}: {e}")
            return {
                "success": False,
                "error": str(e)
            }
