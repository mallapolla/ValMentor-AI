from django.db import models
from django.conf import settings
from apps.core.models import TimeStampedModel

class MemoryEntry(TimeStampedModel):
    """
    Stores long-term facts, key summaries, or career preferences extracted
    from conversations with the user.
    """
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='memories')
    memory_type = models.CharField(
        max_length=50,
        choices=[
            ('fact', 'Fact about User'),
            ('preference', 'Career Preference'),
            ('strength', 'Identified Strength'),
            ('weakness', 'Identified Weakness'),
            ('general', 'General Background')
        ],
        default='general'
    )
    content = models.TextField()
    metadata = models.JSONField(default=dict, blank=True)
    relevance_score = models.FloatField(default=1.0)
    last_accessed = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user.email} [{self.memory_type}]: {self.content[:40]}"

class UserGoal(TimeStampedModel):
    """Stores specific long-term and short-term career achievements planned by the user."""
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='goals')
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    status = models.CharField(
        max_length=20,
        choices=[
            ('pending', 'Not Started'),
            ('active', 'In Progress'),
            ('completed', 'Completed'),
            ('paused', 'Paused')
        ],
        default='active'
    )
    priority = models.CharField(
        max_length=20,
        choices=[
            ('low', 'Low'),
            ('medium', 'Medium'),
            ('high', 'High')
        ],
        default='medium'
    )
    target_date = models.DateField(null=True, blank=True)

    def __str__(self):
        return f"{self.user.email} - Goal: {self.title}"

class SkillRecord(TimeStampedModel):
    """Track user's self-assessed and interview-validated technology proficiencies."""
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='skills_records')
    skill_name = models.CharField(max_length=100)
    category = models.CharField(max_length=100, blank=True)
    proficiency_level = models.IntegerField(default=1)  # scale 1-5
    evidence = models.JSONField(default=dict, blank=True)  # records scores, roadmap modules
    last_assessed = models.DateTimeField(null=True, blank=True)

    class Meta:
        unique_together = ('user', 'skill_name')

    def __str__(self):
        return f"{self.user.email} - Skill: {self.skill_name} (Lvl {self.proficiency_level})"

class LearningEvent(models.Model):
    """Audit ledger of all roadmap milestones reached, questions answered, etc."""
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='learning_history')
    event_type = models.CharField(
        max_length=50,
        choices=[
            ('roadmap_milestone', 'Roadmap Milestone Completed'),
            ('chat_interaction', 'AI Chat Interaction'),
            ('interview_session', 'Completed Mock Interview'),
            ('resume_upload', 'Resume ATS Scored')
        ]
    )
    topic = models.CharField(max_length=150)
    details = models.JSONField(default=dict, blank=True)
    duration_minutes = models.IntegerField(default=0)
    occurred_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.email} - {self.event_type} on {self.topic}"
