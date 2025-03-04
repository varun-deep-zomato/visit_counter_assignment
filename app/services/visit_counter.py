from typing import Dict, List, Any
import asyncio
from datetime import datetime
from ..core.redis_manager import RedisManager
from fastapi import HTTPException

class VisitCounterService:
    def __init__(self):
        """Initialize the visit counter service with Redis manager"""
        self.redis_manager = RedisManager()

    async def increment_visit(self, page_id: str) -> None:
        """
        Increment visit count for a page
        
        Args:
            page_id: Unique identifier for the page
        """
        try:
            redis_key = f"visit_counter:{page_id}"
            result = await self.redis_manager.increment(redis_key)
            if result == 0:
                raise HTTPException(status_code=500, detail="Failed to increment counter")
        except Exception as e:
            print(f"Error incrementing visit count: {str(e)}")
            raise HTTPException(status_code=500, detail="Failed to increment visit count")

    async def get_visit_count(self, page_id: str) -> int:
        """
        Get current visit count for a page
        
        Args:
            page_id: Unique identifier for the page
            
        Returns:
            Current visit count
        """
        redis_key = f"visit_counter:{page_id}"
        count = await self.redis_manager.get(redis_key)
        return count if count is not None else 0
