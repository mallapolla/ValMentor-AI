from .client import get_valkey_client

class LeaderboardManager:
    """
    Handles scoreboards using Valkey's sorted sets.
    Key format: 'leaderboard:global' & 'leaderboard:weekly'
    """
    def __init__(self):
        self.client = get_valkey_client()
        self.global_key = "leaderboard:global"

    def update_score(self, username: str, xp: int) -> float:
        """Adds or updates a user's total XP score in the global scoreboard."""
        # ZADD returns number of elements added (0 if updated)
        self.client.zadd(self.global_key, {username: xp})
        return float(xp)

    def increment_score(self, username: str, amount: int) -> float:
        """Increments a user's score in the global scoreboard by amount."""
        return self.client.zincrby(self.global_key, amount, username)

    def get_top_users(self, count: int = 10) -> list:
        """Retrieves top users sorted descending by score, returning list of (username, score)."""
        # zrevrange returns elements descending
        raw_list = self.client.zrevrange(self.global_key, 0, count - 1, withscores=True)
        return [(user, int(score)) for user, score in raw_list]

    def get_user_rank(self, username: str) -> dict:
        """Retrieves a specific user's rank (1-indexed) and total score."""
        rank = self.client.zrevrank(self.global_key, username)
        score = self.client.zscore(self.global_key, username)
        
        return {
            "rank": rank + 1 if rank is not None else None,
            "score": int(score) if score is not None else 0
        }
