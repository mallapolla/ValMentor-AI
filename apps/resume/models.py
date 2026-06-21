from django.db import models
from django.conf import settings
from apps.core.models import TimeStampedModel

class Resume(TimeStampedModel):
    """Tracks uploaded resume documents and associated AI evaluations."""
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='resumes')
    file = models.FileField(upload_to='resumes/')
    
    status = models.CharField(
        max_length=20,
        choices=[
            ('pending', 'Queued'),
            ('processing', 'Analyzing...'),
            ('completed', 'Completed'),
            ('failed', 'Failed')
        ],
        default='pending'
    )
    
    ats_score = models.IntegerField(default=0)  # ATS score (0-100)
    missing_skills = models.JSONField(default=list, blank=True)
    suggestions = models.JSONField(default=list, blank=True)
    job_matches = models.JSONField(default=dict, blank=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.user.email} - ATS Score: {self.ats_score} ({self.created_at.strftime('%Y-%m-%d')})"
