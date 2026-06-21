import json
from .client import get_valkey_client

class ChatMemoryManager:
    """
    Manages the short-term conversation context for AI chats.
    Key format: 'user:{id}:chat_history' (as a list).
    """
    def __init__(self):
        self.client = get_valkey_client()
        self.max_history_length = 20  # Limit recent messages in active window
        self.ttl = 86400  # 1 day TTL for chat histories in cache

    def _get_key(self, user_id: int) -> str:
        return f"user:{user_id}:chat_history"

    def add_message(self, user_id: int, role: str, content: str) -> None:
        """Appends a new dialogue message to the user's Valkey chat list."""
        key = self._get_key(user_id)
        message_data = json.dumps({"role": role, "content": content})
        
        # Push message onto list tail
        self.client.rpush(key, message_data)
        
        # Enforce maximum list size
        self.client.ltrim(key, -self.max_history_length, -1)
        
        # Set expiration
        self.client.expire(key, self.ttl)

    def get_chat_history(self, user_id: int) -> list:
        """Retrieves user's active short-term chat window list."""
        key = self._get_key(user_id)
        raw_list = self.client.lrange(key, 0, -1)
        
        history = []
        for raw_msg in raw_list:
            try:
                history.append(json.loads(raw_msg))
            except json.JSONDecodeError:
                pass
        return history

    def clear_history(self, user_id: int) -> bool:
        """Clears user's active chat context cache."""
        key = self._get_key(user_id)
        return bool(self.client.delete(key))
