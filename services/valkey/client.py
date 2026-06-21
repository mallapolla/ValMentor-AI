import logging
import valkey
from django.conf import settings

logger = logging.getLogger(__name__)

class MockValkeyPipeline:
    def __init__(self):
        self.results = [0, 0, 0, 0]

    def zremrangebyscore(self, *args, **kwargs):
        return self

    def zcard(self, *args, **kwargs):
        return self

    def zadd(self, *args, **kwargs):
        return self

    def expire(self, *args, **kwargs):
        return self

    def execute(self):
        return self.results

class MockValkeyClient:
    """
    Mock Valkey Client that replicates Valkey command responses in-memory.
    Ensures local development works without an active Valkey/Redis instance.
    """
    def __init__(self):
        self._data = {}
        self._lists = {}
        self._zsets = {}

    def ping(self):
        return True

    def get(self, key):
        return self._data.get(key)

    def set(self, key, value, ex=None, px=None, nx=False, xx=False):
        self._data[key] = str(value)
        return True

    def delete(self, *keys):
        count = 0
        for k in keys:
            if k in self._data:
                del self._data[k]
                count += 1
            if k in self._lists:
                del self._lists[k]
                count += 1
            if k in self._zsets:
                del self._zsets[k]
                count += 1
        return count

    def rpush(self, key, *values):
        if key not in self._lists:
            self._lists[key] = []
        for val in values:
            self._lists[key].append(str(val))
        return len(self._lists[key])

    def ltrim(self, key, start, end):
        if key in self._lists:
            self._lists[key] = self._lists[key][start:end+1]
        return True

    def lrange(self, key, start, end):
        if key not in self._lists:
            return []
        if end == -1:
            return self._lists[key][start:]
        return self._lists[key][start:end+1]

    def expire(self, key, time):
        return True

    def zadd(self, key, mapping, *args, **kwargs):
        if key not in self._zsets:
            self._zsets[key] = {}
        for member, score in mapping.items():
            self._zsets[key][member] = float(score)
        return len(mapping)

    def zincrby(self, key, amount, member):
        if key not in self._zsets:
            self._zsets[key] = {}
        old_score = self._zsets[key].get(member, 0.0)
        new_score = old_score + float(amount)
        self._zsets[key][member] = new_score
        return new_score

    def zrevrange(self, key, start, end, withscores=False, **kwargs):
        if key not in self._zsets:
            return []
        sorted_members = sorted(self._zsets[key].items(), key=lambda item: item[1], reverse=True)
        slice_range = sorted_members[start:end+1] if end != -1 else sorted_members[start:]
        if withscores:
            return [(member, score) for member, score in slice_range]
        return [member for member, score in slice_range]

    def zrevrank(self, key, member):
        if key not in self._zsets or member not in self._zsets[key]:
            return None
        sorted_members = sorted(self._zsets[key].items(), key=lambda item: item[1], reverse=True)
        for rank, (m, _) in enumerate(sorted_members):
            if m == member:
                return rank
        return None

    def zscore(self, key, member):
        if key not in self._zsets:
            return None
        return self._zsets[key].get(member)

    def pipeline(self):
        return MockValkeyPipeline()

class ValkeyClientManager:
    """
    Thread-safe connection pool manager for Valkey.
    Exposes a standardized connection client, falling back to a Mock client on connection failure.
    """
    _instance = None
    _client = None

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super(ValkeyClientManager, cls).__new__(cls, *args, **kwargs)
        return cls._instance

    @property
    def client(self):
        """Returns the pooled Valkey connection client, establishing it if necessary."""
        if self._client is None:
            try:
                self._client = valkey.Valkey(
                    host=settings.VALKEY_HOST,
                    port=settings.VALKEY_PORT,
                    db=settings.VALKEY_DB,
                    decode_responses=True,
                    socket_connect_timeout=3,
                    socket_timeout=3,
                    retry_on_timeout=False
                )
                # Health Check connection test
                self._client.ping()
                logger.info("Successfully connected to Valkey server.")
            except Exception as e:
                logger.warning(f"Failed to connect to Valkey at {settings.VALKEY_HOST}:{settings.VALKEY_PORT}: {str(e)}. Falling back to in-memory MockValkeyClient.")
                self._client = MockValkeyClient()
        return self._client

# Helper helper instance
def get_valkey_client():
    return ValkeyClientManager().client
