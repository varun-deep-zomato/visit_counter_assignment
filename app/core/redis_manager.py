import redis.asyncio as redis
from typing import Dict, List, Optional, Any
from urllib.parse import urlparse
from .consistent_hash import ConsistentHash
from .config import settings
import asyncio

class RedisManager:
    def __init__(self):
        """Initialize Redis connection pools and consistent hashing"""
        self.redis_clients: Dict[str, redis.Redis] = {}
        
        # Parse Redis nodes from comma-separated string
        redis_nodes = [node.strip() for node in settings.REDIS_NODES.split(",") if node.strip()]
        self.consistent_hash = ConsistentHash(redis_nodes, settings.VIRTUAL_NODES)
        
        for node in redis_nodes:
            try:
                client = redis.from_url(
                    node,
                    db=settings.REDIS_DB,
                    decode_responses=True,
                    socket_timeout=5,
                    socket_connect_timeout=5
                )        
                self.redis_clients[node] = client
                print(f"Successfully connected to Redis node: {node}")
            except Exception as e:
                print(f"Error connecting to Redis node {node}: {str(e)}")
                raise

    async def get_connection(self, key: str, max_retries: int = 3) -> redis.Redis:
        """
        Get Redis connection for the given key using consistent hashing with retry logic
        
        Args:
            key: The key to determine which Redis node to use
            max_retries: Maximum number of retry attempts
            
        Returns:
            Redis client for the appropriate node
        """
        retries = 0
        while retries < max_retries:
            node = self.consistent_hash.get_node(key)
            try:
                client = self.redis_clients[node]
                # Test the connection
                await client.ping()
                return client
            except (redis.ConnectionError, redis.TimeoutError) as e:
                retries += 1
                if retries == max_retries:
                    raise e
                await asyncio.sleep(0.1 * (2 ** retries))  # Exponential backoff
                # Try to reconnect
                try:
                    self.redis_clients[node] = redis.from_url(
                        node,
                        db=settings.REDIS_DB,
                        decode_responses=True,
                        socket_timeout=5,
                        socket_connect_timeout=5
                    )
                except Exception:
                    pass  # Continue to next retry if reconnection fails

    async def increment(self, key: str, amount: int = 1) -> int:
        """
        Increment a counter in Redis
        
        Args:
            key: The key to increment
            amount: Amount to increment by
            
        Returns:
            New value of the counter
        """
        redis_client = await self.get_connection(key)
        
        try:
            return await redis_client.incrby(key, amount)
        except Exception as e:
            print(f"Error incrementing key {key}: {str(e)}")
            return 0

    async def get(self, key: str) -> Optional[int]:
        """
        Get value for a key from Redis
        
        Args:
            key: The key to get
            
        Returns:
            Value of the key or None if not found
        """
        redis_client = await self.get_connection(key)
        try:
            value = await redis_client.get(key)
            return int(value) if value is not None else None
        except Exception as e:
            print(f"Error getting key {key}: {str(e)}")
            return None
