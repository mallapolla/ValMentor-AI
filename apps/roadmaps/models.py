from django.db import models
from django.conf import settings
from apps.core.models import TimeStampedModel

class Roadmap(TimeStampedModel):
    """Stores structured roadmap specifications (e.g., Python Developer)."""
    title = models.CharField(max_length=200)
    slug = models.SlugField(max_length=250, unique=True)
    category = models.CharField(max_length=100)
    description = models.TextField()
    difficulty = models.CharField(max_length=50, default='Intermediate')
    estimated_weeks = models.IntegerField(default=8)
    
    # Milestones represented in JSON
    # Format: [{"id": 1, "title": "Milestone Title", "description": "...", "topics": ["A", "B"]}]
    milestones = models.JSONField(default=list)

    def __str__(self):
        return f"{self.title} ({self.difficulty})"

class UserRoadmap(TimeStampedModel):
    """Tracks a user's progress through a specific tech learning roadmap."""
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='user_roadmaps')
    roadmap = models.ForeignKey(Roadmap, on_delete=models.CASCADE, related_name='enrollments')
    progress_pct = models.IntegerField(default=0)  # progress percentage 0-100
    
    # Track completed milestones by ID
    # Format: [1, 3]
    completed_milestones = models.JSONField(default=list, blank=True)
    started_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'roadmap')

    def __str__(self):
        return f"{self.user.email} - {self.roadmap.title} ({self.progress_pct}%)"
