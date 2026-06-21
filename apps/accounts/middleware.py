from django.utils import timezone
from apps.gamification.models import GamificationProfile

class ActivityTrackingMiddleware:
    """
    Middleware that tracks when a user last performed an request
    and automatically calculates daily activity streaks.
    """
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)

        if request.user and request.user.is_authenticated:
            try:
                # Update last active time and check streak
                profile = GamificationProfile.objects.get(user=request.user)
                profile.update_streak()
            except Exception:
                pass

        return response
