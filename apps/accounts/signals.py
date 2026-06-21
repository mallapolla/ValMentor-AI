from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import User, UserProfile

@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    """Automatically create a UserProfile and GamificationProfile when a User is created."""
    if created:
        UserProfile.objects.create(user=instance)
        
        # Avoid circular dependency with apps.gamification
        from apps.gamification.models import GamificationProfile
        GamificationProfile.objects.create(user=instance)

@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    """Save user profile details on user updates."""
    if hasattr(instance, 'profile'):
        instance.profile.save()
