from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from services.valkey.leaderboard import LeaderboardManager
from .models import Achievement, UserAchievement

@login_required
def leaderboard_view(request):
    """Renders the real-time global leaderboard using Valkey sorted sets and lists badges."""
    leaderboard = LeaderboardManager()
    top_scores = leaderboard.get_top_users(15)  # Get top 15 users
    
    # Get user rank
    user_rank = leaderboard.get_user_rank(request.user.username)
    
    # Get achievements configuration database
    achievements = Achievement.objects.all()
    unlocked_slugs = UserAchievement.objects.filter(user=request.user).values_list('achievement__slug', flat=True)

    return render(request, 'gamification/leaderboard.html', {
        'leaderboard': top_scores,
        'user_rank': user_rank,
        'achievements': achievements,
        'unlocked_slugs': unlocked_slugs
    })
