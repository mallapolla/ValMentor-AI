from django.contrib.auth.models import AbstractUser
from django.db import models
from apps.core.models import TimeStampedModel

class User(AbstractUser):
    """Custom user model supporting email verification status and profiles."""
    email = models.EmailField(unique=True)
    is_email_verified = models.BooleanField(default=False)
    verification_token = models.CharField(max_length=100, blank=True, null=True)

    # Use email as username for registration/login flows
    REQUIRED_FIELDS = ['username']
    USERNAME_FIELD = 'email'

    def __str__(self):
        return self.email

class UserProfile(TimeStampedModel):
    """User profile data tracking roles, target position, skills, and interests."""
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    avatar = models.ImageField(upload_to='avatars/', blank=True, null=True)
    bio = models.TextField(max_length=500, blank=True)
    
    current_role = models.CharField(max_length=100, blank=True, default='Student')
    target_role = models.CharField(max_length=100, blank=True, default='Python Developer')
    experience_level = models.CharField(
        max_length=50, 
        choices=[
            ('Entry', 'Entry Level (0-2 years)'),
            ('Mid', 'Mid Level (2-5 years)'),
            ('Senior', 'Senior Level (5+ years)'),
        ],
        default='Entry'
    )
    
    career_interests = models.JSONField(default=list, blank=True)
    skills = models.JSONField(default=list, blank=True)

    def __str__(self):
        return f"{self.user.email}'s Profile"
