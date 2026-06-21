from django.db import models
from django.conf import settings
from django.utils import timezone
from apps.core.models import TimeStampedModel

class GamificationProfile(TimeStampedModel):
    """Tracks XP, levels, activity streaks, and unlocked badges for a user."""
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='gamification')
    xp = models.IntegerField(default=0)
    level = models.IntegerField(default=1)
    streak_days = models.IntegerField(default=0)
    last_activity = models.DateTimeField(null=True, blank=True)
    badges = models.JSONField(default=list, blank=True)  # unlocked badge names/slugs

    def __str__(self):
        return f"{self.user.email} - Level {self.level} (XP: {self.xp}, Streak: {self.streak_days})"

    def update_streak(self):
        """Calculates and updates user daily activity streaks."""
        now = timezone.now()
        if not self.last_activity:
            self.streak_days = 1
            self.last_activity = now
            self.save(update_fields=['streak_days', 'last_activity'])
            return

        delta = now.date() - self.last_activity.date()
        if delta.days == 1:
            self.streak_days += 1
            self.last_activity = now
            self.save(update_fields=['streak_days', 'last_activity'])
        elif delta.days > 1:
            self.streak_days = 1
            self.last_activity = now
            self.save(update_fields=['streak_days', 'last_activity'])
        elif delta.days == 0:
            # Already active today, just update time
            self.last_activity = now
            self.save(update_fields=['last_activity'])

class Achievement(models.Model):
    """Configuration database of badge requirements and rewards."""
    name = models.CharField(max_length=150)
    slug = models.SlugField(max_length=150, unique=True)
    description = models.TextField()
    xp_reward = models.IntegerField(default=100)
    icon = models.CharField(max_length=50, default='star')  # FontAwesome or SVG icon name
    
    # Matching rules
    criteria_type = models.CharField(
        max_length=50,
        choices=[
            ('interviews_completed', 'Mock Interviews Completed'),
            ('roadmap_milestones', 'Roadmap Milestones Checked'),
            ('first_resume', 'ATS Resume Evaluated'),
            ('streak_days', 'Daily Streak Threshold')
        ]
    )
    criteria_value = models.IntegerField(default=1)

    def __str__(self):
        return f"{self.name} (+{self.xp_reward} XP)"

class UserAchievement(models.Model):
    """Record of achievements earned by users."""
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='earned_achievements')
    achievement = models.ForeignKey(Achievement, on_delete=models.CASCADE)
    earned_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'achievement')

    def __str__(self):
        return f"{self.user.email} unlocked {self.achievement.name}"
