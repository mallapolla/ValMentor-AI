from django.conf import settings

def global_context(request):
    """
    Exposes global variables to all templates (e.g. user profiles, XP levels, and system parameters).
    """
    context = {
        'debug': settings.DEBUG,
        'app_name': 'ValMentor AI',
    }
    
    if request.user and request.user.is_authenticated:
        # Avoid circular imports in loading profiles/gamification
        try:
            from apps.accounts.models import UserProfile
            from apps.gamification.models import GamificationProfile
            
            profile, _ = UserProfile.objects.get_or_create(user=request.user)
            gamification, _ = GamificationProfile.objects.get_or_create(user=request.user)
            
            context.update({
                'user_profile': profile,
                'user_gamification': gamification,
                'user_streak': gamification.streak_days,
                'user_xp': gamification.xp,
                'user_level': gamification.level,
            })
        except Exception:
            pass
            
    return context
