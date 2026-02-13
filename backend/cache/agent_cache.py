"""Agent result caching to avoid re-running expensive agent queries."""
import time
import threading
from typing import Dict, Any, Optional, Tuple, List, Set
from backend.utils.logger import get_logger

logger = get_logger(__name__)


class AgentCache:
    """Simple in-memory cache for agent results with TTL."""
    
    def __init__(self, default_ttl: int = 300):  # 5 minutes default
        """Initialize the cache.
        
        Args:
            default_ttl: Default time-to-live in seconds for cache entries
        """
        self._cache: Dict[str, Tuple[Dict[str, Any], float]] = {}
        self._excluded_items: Dict[str, Set[str]] = {}  # incident_id -> set of excluded item IDs
        self._lock = threading.Lock()
        self.default_ttl = default_ttl
        logger.info(f"AgentCache initialized with TTL={default_ttl}s")
    
    def get(self, incident_id: str) -> Optional[Dict[str, Any]]:
        """Get cached agent results for an incident.
        
        Args:
            incident_id: The incident ID to lookup
            
        Returns:
            Cached results dict or None if not found/expired
        """
        with self._lock:
            if incident_id not in self._cache:
                logger.debug(f"Cache miss for incident: {incident_id}")
                return None
            
            results, expiry_time = self._cache[incident_id]
            
            # Check if expired
            if time.time() > expiry_time:
                logger.debug(f"Cache expired for incident: {incident_id}")
                del self._cache[incident_id]
                return None
            
            logger.debug(f"Cache hit for incident: {incident_id}")
            return results
    
    def set(self, incident_id: str, results: Dict[str, Any], ttl: Optional[int] = None):
        """Store agent results in cache.
        
        Args:
            incident_id: The incident ID
            results: The agent results to cache
            ttl: Optional custom TTL in seconds (uses default if not provided)
        """
        ttl = ttl or self.default_ttl
        expiry_time = time.time() + ttl
        
        with self._lock:
            self._cache[incident_id] = (results, expiry_time)
            logger.info(f"Cached results for incident: {incident_id}, TTL={ttl}s")
    
    def invalidate(self, incident_id: str):
        """Invalidate cache for a specific incident.
        
        Args:
            incident_id: The incident ID to invalidate
        """
        with self._lock:
            if incident_id in self._cache:
                del self._cache[incident_id]
                logger.info(f"Cache invalidated for incident: {incident_id}")
    
    def clear(self):
        """Clear all cache entries."""
        with self._lock:
            count = len(self._cache)
            self._cache.clear()
            logger.info(f"Cache cleared, removed {count} entries")
    
    def cleanup_expired(self):
        """Remove expired entries from cache."""
        with self._lock:
            current_time = time.time()
            expired_keys = [
                key for key, (_, expiry) in self._cache.items()
                if current_time > expiry
            ]
            
            for key in expired_keys:
                del self._cache[key]
            
            if expired_keys:
                logger.info(f"Cleaned up {len(expired_keys)} expired cache entries")
    
    def add_excluded_item(self, incident_id: str, item_id: str):
        """Add an item to the exclusion list for an incident.
        
        Args:
            incident_id: The incident ID
            item_id: The item ID to exclude
        """
        with self._lock:
            if incident_id not in self._excluded_items:
                self._excluded_items[incident_id] = set()
            self._excluded_items[incident_id].add(item_id)
            logger.info(f"Added excluded item {item_id} for incident {incident_id}")
    
    def remove_excluded_item(self, incident_id: str, item_id: str):
        """Remove an item from the exclusion list for an incident.
        
        Args:
            incident_id: The incident ID
            item_id: The item ID to un-exclude
        """
        with self._lock:
            if incident_id in self._excluded_items:
                self._excluded_items[incident_id].discard(item_id)
                logger.info(f"Removed excluded item {item_id} for incident {incident_id}")
    
    def get_excluded_items(self, incident_id: str) -> List[str]:
        """Get all excluded items for an incident.
        
        Args:
            incident_id: The incident ID
            
        Returns:
            List of excluded item IDs
        """
        with self._lock:
            if incident_id not in self._excluded_items:
                return []
            return list(self._excluded_items[incident_id])
    
    def is_item_excluded(self, incident_id: str, item_id: str) -> bool:
        """Check if an item is excluded for an incident.
        
        Args:
            incident_id: The incident ID
            item_id: The item ID to check
            
        Returns:
            True if the item is excluded, False otherwise
        """
        with self._lock:
            if incident_id not in self._excluded_items:
                return False
            return item_id in self._excluded_items[incident_id]


# Global cache instance
_agent_cache: Optional[AgentCache] = None
_cache_lock = threading.Lock()


def get_agent_cache() -> AgentCache:
    """Get the global agent cache instance."""
    global _agent_cache
    
    if _agent_cache is None:
        with _cache_lock:
            if _agent_cache is None:
                _agent_cache = AgentCache()
    
    return _agent_cache
