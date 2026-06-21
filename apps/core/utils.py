import hashlib
import json
import uuid
from django.core.serializers.json import DjangoJSONEncoder

def generate_unique_id():
    """Generates a secure random unique string."""
    return str(uuid.uuid4())

def calculate_sha256(text: str) -> str:
    """Calculates SHA-256 hash of a string, useful for Valkey caching keys."""
    return hashlib.sha256(text.encode('utf-8')).hexdigest()

def serialize_json(data) -> str:
    """Serializes data including dates, decimals to JSON string safely."""
    return json.dumps(data, cls=DjangoJSONEncoder)

def deserialize_json(json_str: str):
    """Safely deserializes JSON string back to Python dict/list."""
    try:
        return json.loads(json_str) if json_str else None
    except (json.JSONDecodeError, TypeError):
        return None

def format_learning_duration(minutes: int) -> str:
    """Formats minutes into human readable hours/minutes."""
    if not minutes:
        return "0 mins"
    hours = minutes // 60
    mins = minutes % 60
    if hours > 0:
        return f"{hours}h {mins}m" if mins > 0 else f"{hours}h"
    return f"{mins} mins"
