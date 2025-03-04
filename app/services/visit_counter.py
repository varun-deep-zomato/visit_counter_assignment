from typing import Dict, List, Any
import asyncio
from datetime import datetime
from ..core.redis_manager import RedisManager
from fastapi import HTTPException
import time
from collections import defaultdict

cache = {}
cache_timestamps = {}
cache_ttl = 5

class VisitCounterService:
    def __init__(self, redis_manager):
        """Initialize the visit counter service with Redis manager"""
        self.redis_manager = redis_manager
        self.visit_buffer = defaultdict(int)
        self.buffer_lock = asyncio.Lock()
        self.last_flush_time = time.time()
        self.flush_interval = 5  # seconds

    async def start_periodic_flush(self):
        """Start the periodic flush background task"""
        asyncio.create_task(self.periodic_flush())

    async def periodic_flush(self):
        """Background task to periodically flush visit counts to Redis"""
        while True:
            await asyncio.sleep(self.flush_interval)
            await self.flush_buffer()

    async def flush_buffer(self):
        """Flush accumulated visit counts to Redis"""
        async with self.buffer_lock:
            if not self.visit_buffer:
                return

            for page_id, count in self.visit_buffer.items():
                if count > 0:
                    redis_key = f"visit_counter:{page_id}"
                    try:
                        await self.redis_manager.increment(redis_key, count)
                        if page_id in cache:
                            del cache[page_id]
                            del cache_timestamps[page_id]
                    except Exception as e:
                        print(f"Error flushing visit count for {page_id}: {str(e)}")

            self.visit_buffer.clear()
            self.last_flush_time = time.time()

    async def increment_visit(self, page_id: str) -> None:
        """Increment visit count for a page in the memory buffer"""
        async with self.buffer_lock:
            self.visit_buffer[page_id] += 1
            if page_id in cache:
                del cache[page_id]
                del cache_timestamps[page_id]

    async def get_visit_count(self, page_id: str) -> Dict[str, Any]:
        """Get current visit count combining Redis and buffer counts"""
        current_time = time.time()
        buffered_count = 0
        async with self.buffer_lock:
            buffered_count = self.visit_buffer.get(page_id, 0)

        if page_id in cache and (current_time - cache_timestamps[page_id]) < cache_ttl:
            total_count = cache[page_id] + buffered_count
            return {'visits': total_count, 'served_via': 'in_memory'}
        else:
            await self.flush_buffer()
            redis_key = f"visit_counter:{page_id}"
            count = await self.redis_manager.get(redis_key) or 0
            cache[page_id] = count
            cache_timestamps[page_id] = current_time
            total_count = count + buffered_count
            return {'visits': total_count, 'served_via': 'redis'}
