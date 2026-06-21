from django.test import TestCase
from django.contrib.auth import get_user_model
from apps.accounts.models import UserProfile
from apps.gamification.models import GamificationProfile

User = get_user_model()

class AccountsAuthTests(TestCase):
    """Verifies that user creation correctly spins up subprofiles and models."""
    
    def test_user_registration_creates_profiles(self):
        user = User.objects.create_user(
            username='testcandidate',
            email='candidate@valmentor.ai',
            password='SecretPassword123'
        )
        
        # Verify custom user fields
        self.assertEqual(user.email, 'candidate@valmentor.ai')
        self.assertFalse(user.is_email_verified)
        
        # Verify signal handler creates profile
        profile = UserProfile.objects.filter(user=user).first()
        self.assertIsNotNone(profile)
        self.assertEqual(profile.current_role, 'Student')
        self.assertEqual(profile.target_role, 'Python Developer')
        
        # Verify signal handler creates gamification metrics
        gamification = GamificationProfile.objects.filter(user=user).first()
        self.assertIsNotNone(gamification)
        self.assertEqual(gamification.xp, 0)
        self.assertEqual(gamification.level, 1)
