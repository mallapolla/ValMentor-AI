from apps.core.utils import calculate_sha256
from .client import get_valkey_client

class ResponseCacheManager:
    """
    Caches LLM answers based on hashed questions.
    Key format: 'cache:response:{question_hash}' (simple string value).
    """
    def __init__(self):
        self.client = get_valkey_client()
        self.ttl = 3600  # 1 hour TTL for cached responses

    def _get_key(self, question: str) -> str:
        q_hash = calculate_sha256(question.strip().lower())
        return f"cache:response:{q_hash}"

    def get_cached_response(self, question: str) -> str:
        """Checks if a matching question is cached, returning content or None."""
        key = self._get_key(question)
        return self.client.get(key)

    def set_cached_response(self, question: str, response: str) -> bool:
        """Saves LLM response to key-value cache under hashed question query."""
        key = self._get_key(question)
        return self.client.set(key, response, ex=self.ttl)
