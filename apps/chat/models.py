from django.db import models
from django.conf import settings
from apps.core.models import TimeStampedModel

class Conversation(TimeStampedModel):
    """Represents an active or past career coaching conversation thread."""
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='conversations')
    title = models.CharField(max_length=200, default='New Career Coaching Session')
    category = models.CharField(max_length=100, default='General Career')
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ['-updated_at']

    def __str__(self):
        return f"{self.user.email} - {self.title} ({self.updated_at.strftime('%Y-%m-%d')})"

class Message(TimeStampedModel):
    """Individual user and AI chat exchanges within a specific Conversation."""
    conversation = models.ForeignKey(Conversation, on_delete=models.CASCADE, related_name='messages')
    role = models.CharField(
        max_length=20,
        choices=[
            ('user', 'User'),
            ('assistant', 'ValMentor AI')
        ]
    )
    content = models.TextField()
    metadata = models.JSONField(default=dict, blank=True)

    class Meta:
        ordering = ['created_at']

    def __str__(self):
        return f"{self.role.capitalize()}: {self.content[:50]}"
