import json
from django.conf import settings
from .client import get_valkey_client

class SessionMemoryManager:
    """
    Handles user session caching using key structures like 'user:{id}:session'.
    Maintains session state variables across agents with configured TTL.
    """
    def __init__(self):
        self.client = get_valkey_client()
        self.ttl = 1800  # 30 minutes default session TTL

    def _get_key(self, user_id: int) -> str:
        return f"user:{user_id}:session"

    def set_session_data(self, user_id: int, key: str, value) -> bool:
        """Stores a specific key-value pair in user's Valkey session context."""
        session_key = self._get_key(user_id)
        
        # Retrieve existing session context
        session_data = self.get_all_session_data(user_id) or {}
        session_data[key] = value
        
        # Save back and refresh TTL
        return self.client.set(session_key, json.dumps(session_data), ex=self.ttl)

    def get_session_data(self, user_id: int, key: str):
        """Retrieves a specific value from user's Valkey session context."""
        session_data = self.get_all_session_data(user_id)
        return session_data.get(key) if session_data else None

    def get_all_session_data(self, user_id: int) -> dict:
        """Retrieves user's entire session data dict."""
        session_key = self._get_key(user_id)
        raw_data = self.client.get(session_key)
        if raw_data:
            try:
                return json.loads(raw_data)
            except json.JSONDecodeError:
                return {}
        return {}

    def clear_session(self, user_id: int) -> bool:
        """Deletes user's session cache."""
        session_key = self._get_key(user_id)
        return bool(self.client.delete(session_key))
