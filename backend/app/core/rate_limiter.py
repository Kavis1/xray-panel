import time
from typing import Dict, Optional
from collections import defaultdict
from datetime import datetime, timedelta
import asyncio


class RateLimiter:
    """In-memory rate limiter с поддержкой множественных окон"""
    
    def __init__(self):
        self.requests: Dict[str, list] = defaultdict(list)
        self._lock = asyncio.Lock()
    
    async def is_allowed(
        self,
        key: str,
        limit_per_minute: Optional[int] = None,
        limit_per_hour: Optional[int] = None
    ) -> tuple[bool, Optional[str]]:
        """
        Проверка лимита запросов
        
        Returns:
            (allowed, reason) - разрешен ли запрос и причина отказа
        """
        async with self._lock:
            now = time.time()
            
            # Очистка старых записей
            if key in self.requests:
                self.requests[key] = [
                    ts for ts in self.requests[key]
                    if now - ts < 3600  # Храним за последний час
                ]
            
            timestamps = self.requests[key]
            
            # Проверка минутного лимита
            if limit_per_minute:
                minute_ago = now - 60
                recent_requests = sum(1 for ts in timestamps if ts > minute_ago)
                
                if recent_requests >= limit_per_minute:
                    return False, f"Rate limit exceeded: {limit_per_minute} requests per minute"
            
            # Проверка часового лимита
            if limit_per_hour:
                hour_ago = now - 3600
                recent_requests = sum(1 for ts in timestamps if ts > hour_ago)
                
                if recent_requests >= limit_per_hour:
                    return False, f"Rate limit exceeded: {limit_per_hour} requests per hour"
            
            # Добавляем текущий запрос
            self.requests[key].append(now)
            
            return True, None
    
    async def get_remaining(
        self,
        key: str,
        limit_per_minute: Optional[int] = None,
        limit_per_hour: Optional[int] = None
    ) -> Dict[str, int]:
        """Получить оставшееся количество запросов"""
        async with self._lock:
            now = time.time()
            timestamps = self.requests.get(key, [])
            
            result = {}
            
            if limit_per_minute:
                minute_ago = now - 60
                used = sum(1 for ts in timestamps if ts > minute_ago)
                result['remaining_per_minute'] = max(0, limit_per_minute - used)
                result['reset_minute'] = int(minute_ago + 60)
            
            if limit_per_hour:
                hour_ago = now - 3600
                used = sum(1 for ts in timestamps if ts > hour_ago)
                result['remaining_per_hour'] = max(0, limit_per_hour - used)
                result['reset_hour'] = int(hour_ago + 3600)
            
            return result


# Глобальный экземпляр
rate_limiter = RateLimiter()
