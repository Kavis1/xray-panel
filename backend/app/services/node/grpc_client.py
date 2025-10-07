import grpc
import json
from typing import List, Dict, Any
from app.grpc_gen import node_pb2, node_pb2_grpc
from app.models.node import Node
from app.models.user import User
from app.models.inbound import Inbound


class NodeGRPCClient:
    """gRPC client for Node Service communication"""
    
    def __init__(self, node: Node):
        self.node = node
        self.address = f"{node.address}:{node.api_port}"
        
    async def start_xray(self, config: str, users: List[User]) -> Dict[str, Any]:
        """Start Xray on node with configuration and users"""
        async with grpc.aio.insecure_channel(self.address) as channel:
            stub = node_pb2_grpc.NodeServiceStub(channel)
            
            # Prepare Backend message
            user_messages = []
            for user in users:
                proxies = []
                for proxy in user.proxies:
                    proxy_msg = node_pb2.Proxy(
                        vmess_id=proxy.vmess_uuid or "",
                        vless_id=proxy.vless_uuid or "",
                        vless_flow=proxy.vless_flow or "",
                        trojan_pwd=proxy.trojan_password or "",
                        ss_method=proxy.ss_method or "",
                        ss_pass=proxy.ss_password or ""
                    )
                    proxies.append(proxy_msg)
                
                inbound_tags = [ui.inbound_tag for ui in user.inbounds]
                
                user_msg = node_pb2.User(
                    email=user.email or user.username,
                    proxies=proxies,
                    inbounds=inbound_tags
                )
                user_messages.append(user_msg)
            
            backend = node_pb2.Backend(
                type="XRAY",
                config=config,
                users=user_messages,
                keep_alive=True
            )
            
            # Call gRPC Start
            response = await stub.Start(backend)
            
            return {
                "running": response.running,
                "xray_version": response.xray_version,
                "uptime": response.uptime,
                "session_id": response.session_id
            }
    
    async def stop_xray(self) -> Dict[str, Any]:
        """Stop Xray on node"""
        async with grpc.aio.insecure_channel(self.address) as channel:
            stub = node_pb2_grpc.NodeServiceStub(channel)
            response = await stub.Stop(node_pb2.Empty())
            
            return {
                "running": response.running,
                "message": "Xray stopped successfully"
            }
    
    async def get_info(self) -> Dict[str, Any]:
        """Get node information"""
        import logging
        logger = logging.getLogger(__name__)
        
        logger.info(f"[gRPC Client] Connecting to {self.address}")
        
        try:
            async with grpc.aio.insecure_channel(self.address) as channel:
                stub = node_pb2_grpc.NodeServiceStub(channel)
                
                logger.info(f"[gRPC Client] Calling GetBaseInfo on {self.address}")
                response = await stub.GetBaseInfo(node_pb2.Empty())
                
                logger.info(f"[gRPC Client] Response from {self.address}: running={response.running}")
                
                return {
                    "version": response.version,
                    "core_type": response.core_type,
                    "running": response.running,
                    "xray_version": response.xray_version,
                    "uptime": response.uptime,
                    "session_id": response.session_id
                }
        except grpc.aio.AioRpcError as e:
            logger.error(f"[gRPC Client] gRPC error connecting to {self.address}: {e.code()}")
            
            # Понятные сообщения для пользователя
            if e.code() == grpc.StatusCode.UNAVAILABLE:
                if "No route to host" in str(e.details()):
                    raise Exception(f"Не удается подключиться к ноде {self.address}. Проверьте: 1) Файрвол на ноде (порт 50051 должен быть открыт), 2) Node Service запущен (systemctl status xray-panel-node)")
                else:
                    raise Exception(f"Нода {self.address} недоступна. Node Service не запущен или неверный порт.")
            elif e.code() == grpc.StatusCode.UNAUTHENTICATED:
                raise Exception(f"Ошибка аутентификации с нодой {self.address}. Проверьте API_KEY в .env файле ноды.")
            elif e.code() == grpc.StatusCode.DEADLINE_EXCEEDED:
                raise Exception(f"Превышено время ожидания ответа от ноды {self.address}. Нода перегружена или медленная сеть.")
            else:
                raise Exception(f"Ошибка подключения к ноде {self.address}: {e.code().name}")
        except Exception as e:
            logger.error(f"[gRPC Client] Unexpected error: {e}")
            raise
    
    async def sync_user(self, user: User) -> Dict[str, Any]:
        """Sync single user to node"""
        async with grpc.aio.insecure_channel(self.address) as channel:
            stub = node_pb2_grpc.NodeServiceStub(channel)
            
            proxies = []
            for proxy in user.proxies:
                proxy_msg = node_pb2.Proxy(
                    vmess_id=proxy.vmess_uuid or "",
                    vless_id=proxy.vless_uuid or "",
                    vless_flow=proxy.vless_flow or "",
                    trojan_pwd=proxy.trojan_password or "",
                    ss_method=proxy.ss_method or "",
                    ss_pass=proxy.ss_password or ""
                )
                proxies.append(proxy_msg)
            
            inbound_tags = [ui.inbound_tag for ui in user.inbounds]
            
            user_msg = node_pb2.User(
                email=user.email or user.username,
                proxies=proxies,
                inbounds=inbound_tags
            )
            
            response = await stub.SyncUser(user_msg)
            
            return {
                "success": response.success,
                "message": response.message,
                "synced_count": response.synced_count
            }
    
    async def sync_users(self, users: List[User]) -> Dict[str, Any]:
        """Sync all users to node"""
        async with grpc.aio.insecure_channel(self.address) as channel:
            stub = node_pb2_grpc.NodeServiceStub(channel)
            
            user_messages = []
            for user in users:
                proxies = []
                for proxy in user.proxies:
                    proxy_msg = node_pb2.Proxy(
                        vmess_id=proxy.vmess_uuid or "",
                        vless_id=proxy.vless_uuid or "",
                        vless_flow=proxy.vless_flow or "",
                        trojan_pwd=proxy.trojan_password or "",
                        ss_method=proxy.ss_method or "",
                        ss_pass=proxy.ss_password or ""
                    )
                    proxies.append(proxy_msg)
                
                inbound_tags = [ui.inbound_tag for ui in user.inbounds]
                
                user_msg = node_pb2.User(
                    email=user.email or user.username,
                    proxies=proxies,
                    inbounds=inbound_tags
                )
                user_messages.append(user_msg)
            
            users_msg = node_pb2.Users(users=user_messages)
            response = await stub.SyncUsers(users_msg)
            
            return {
                "success": response.success,
                "message": response.message,
                "synced_count": response.synced_count
            }
    
    async def get_user_stats(self, email: str, reset: bool = False) -> Dict[str, Any]:
        """Get traffic statistics for specific user"""
        async with grpc.aio.insecure_channel(self.address) as channel:
            stub = node_pb2_grpc.NodeServiceStub(channel)
            
            request = node_pb2.StatsRequest(
                type="user",
                name=email,
                reset=reset
            )
            
            response = await stub.GetStats(request)
            
            return {
                "name": response.name,
                "bytes_up": response.bytes_up,
                "bytes_down": response.bytes_down,
                "total": response.bytes_up + response.bytes_down
            }
    
    async def get_online_users(self) -> Dict[str, Any]:
        """Get list of online users with their active connections"""
        async with grpc.aio.insecure_channel(self.address) as channel:
            stub = node_pb2_grpc.NodeServiceStub(channel)
            
            response = await stub.GetOnlineUsers(node_pb2.Empty())
            
            online_users = {}
            for user in response.users:
                online_users[user.email] = {
                    "email": user.email,
                    "ips": list(user.ips),
                    "connection_count": len(user.ips),
                    "online_since": user.online_since
                }
            
            return online_users
    
    async def get_inbound_stats(self, tag: str, reset: bool = False) -> Dict[str, Any]:
        """Get traffic statistics for specific inbound"""
        async with grpc.aio.insecure_channel(self.address) as channel:
            stub = node_pb2_grpc.NodeServiceStub(channel)
            
            request = node_pb2.StatsRequest(
                type="inbound",
                name=tag,
                reset=reset
            )
            
            response = await stub.GetStats(request)
            
            return {
                "name": response.name,
                "bytes_up": response.bytes_up,
                "bytes_down": response.bytes_down,
                "total": response.bytes_up + response.bytes_down
            }
    
    async def get_online_users(self) -> Dict[str, Any]:
        """Get list of online users with their active connections"""
        async with grpc.aio.insecure_channel(self.address) as channel:
            stub = node_pb2_grpc.NodeServiceStub(channel)
            
            response = await stub.GetOnlineUsers(node_pb2.Empty())
            
            online_users = {}
            for user in response.users:
                online_users[user.email] = {
                    "email": user.email,
                    "ips": list(user.ips),
                    "connection_count": len(user.ips),
                    "online_since": user.online_since
                }
            
            return online_users
