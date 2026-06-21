from django.utils import timezone
from .models import GamificationProfile, Achievement, UserAchievement
from services.valkey.leaderboard import LeaderboardManager

def award_xp_and_streak(user, xp_amount):
    """
    Core function to reward users with XP, recalculate level status,
    update Valkey sorted set leaderboards, and check for unlocked achievements.
    """
    profile, _ = GamificationProfile.objects.get_or_create(user=user)
    
    # 1. Update XP
    profile.xp += xp_amount
    
    # 2. Level calculation (simple formula: level = (xp / 1000) + 1)
    new_level = int(profile.xp / 1000) + 1
    if new_level > profile.level:
        profile.level = new_level
        # Optional: Add system message about level up
        
    profile.last_activity = timezone.now()
    profile.save()

    # 3. Update Valkey global sorted set leaderboard
    leaderboard = LeaderboardManager()
    leaderboard.update_score(user.username, profile.xp)

    # 4. Check achievements qualifications
    check_achievements(user, profile)

def check_achievements(user, profile):
    """Queries user history databases to see if any criteria matches Achievement rules."""
    achievements = Achievement.objects.exclude(
        id__in=UserAchievement.objects.filter(user=user).values_list('achievement_id', flat=True)
    )

    for ach in achievements:
        unlocked = False
        
        if ach.criteria_type == 'streak_days':
            if profile.streak_days >= ach.criteria_value:
                unlocked = True
                
        elif ach.criteria_type == 'interviews_completed':
            from apps.interviews.models import InterviewSession
            count = InterviewSession.objects.filter(user=user, is_completed=True).count()
            if count >= ach.criteria_value:
                unlocked = True
                
        elif ach.criteria_type == 'roadmap_milestones':
            from apps.roadmaps.models import UserRoadmap
            # Sum up counts of elements in completed_milestones lists
            user_rm = UserRoadmap.objects.filter(user=user)
            milestones_count = sum([len(rm.completed_milestones) for rm in user_rm])
            if milestones_count >= ach.criteria_value:
                unlocked = True
                
        elif ach.criteria_type == 'first_resume':
            from apps.resume.models import Resume
            if Resume.objects.filter(user=user, status='completed').exists():
                unlocked = True

        if unlocked:
            # Grant Achievement
            UserAchievement.objects.create(user=user, achievement=ach)
            # Award reward XP
            profile.xp += ach.xp_reward
            
            # Append badge label to JSON
            if ach.slug not in profile.badges:
                profile.badges.append(ach.slug)
                
            profile.save()
            
            # Refresh leaderboard score
            leaderboard = LeaderboardManager()
            leaderboard.update_score(user.username, profile.xp)
