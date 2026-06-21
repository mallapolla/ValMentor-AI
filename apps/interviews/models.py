from django.db import models
from django.conf import settings
from apps.core.models import TimeStampedModel

class InterviewSession(TimeStampedModel):
    """Stores information about a mock interview session taken by a user."""
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='interviews')
    category = models.CharField(
        max_length=50,
        choices=[
            ('python', 'Python Programming'),
            ('django', 'Django Framework'),
            ('rest_apis', 'REST APIs & Web Services'),
            ('sql', 'SQL & Databases'),
            ('postgresql', 'PostgreSQL Internals'),
            ('machine_learning', 'Machine Learning'),
            ('data_structures', 'Data Structures & Algorithms'),
            ('system_design', 'System Design')
        ]
    )
    difficulty = models.CharField(
        max_length=20,
        choices=[
            ('junior', 'Junior'),
            ('mid', 'Mid-Level'),
            ('senior', 'Senior')
        ],
        default='mid'
    )
    is_completed = models.BooleanField(default=False)
    score = models.IntegerField(default=0)  # average of question scores
    weak_areas = models.JSONField(default=list, blank=True)
    feedback = models.TextField(blank=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.user.email} - {self.get_category_display()} ({self.difficulty}) - Score: {self.score}"

class InterviewQuestion(TimeStampedModel):
    """Tracks questions asked, user answers, AI feedback, and scores in a session."""
    session = models.ForeignKey(InterviewSession, on_delete=models.CASCADE, related_name='questions')
    question_text = models.TextField()
    user_answer = models.TextField(blank=True)
    ai_feedback = models.TextField(blank=True)
    score = models.IntegerField(default=0)  # 0-100 scale

    def __str__(self):
        return f"Q: {self.question_text[:50]} (Score: {self.score})"
