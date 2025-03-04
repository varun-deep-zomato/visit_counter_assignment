from typing import Dict, List, Any
import asyncio
from datetime import datetime
from ..core.redis_manager import RedisManager
from fastapi import HTTPException
import time

cache = {}
cache_timestamps = {}
cache_ttl = 5 

class VisitCounterService:
    def __init__(self, redis_manager):
        """Initialize the visit counter service with Redis manager"""
        self.redis_manager = redis_manager

    async def increment_visit(self, page_id: str) -> None:
        """
        Increment visit count for a page
        
        Args:
            page_id: Unique identifier for the page
        """
        redis_key = f"visit_counter:{page_id}"
        try:
            result = await self.redis_manager.increment(redis_key)
            if result == 0:
                raise HTTPException(status_code=500, detail="Failed to increment counter")
            if page_id in cache:
                del cache[page_id]
                del cache_timestamps[page_id]
        except Exception as e:
            print(f"Error incrementing visit count: {str(e)}")
            raise HTTPException(status_code=500, detail="Failed to increment visit count")

    async def get_visit_count(self, page_id: str) -> Dict[str, Any]:
        """
        Get current visit count for a page
        
        Args:
            page_id: Unique identifier for the page
            
        Returns:
            Current visit count
        """
        current_time = time.time()
        if page_id in cache and (current_time - cache_timestamps[page_id]) < cache_ttl:
            return {'visits': [cache[page_id]], 'served_via': 'in_memory'}
        else:
            redis_key = f"visit_counter:{page_id}"
            count = await self.redis_manager.get(redis_key)
            cache[page_id] = count
            cache_timestamps[page_id] = current_time
            return {'visits': [count], 'served_via': 'redis'} if count is not None else {'visits': [0], 'served_via': 'redis'}
