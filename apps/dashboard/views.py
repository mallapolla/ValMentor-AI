import json
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.db.models import Avg, Sum
from django.utils import timezone
from datetime import timedelta

from apps.accounts.models import UserProfile
from apps.gamification.models import GamificationProfile
from services.breeth.models import UserGoal, SkillRecord, LearningEvent
from apps.interviews.models import InterviewSession
from apps.roadmaps.models import UserRoadmap
from services.ai.agents import CareerMentorAgent
from services.valkey.leaderboard import LeaderboardManager

@login_required
def dashboard_home(request):
    """
    Assembles user metrics: active goals, technology learning duration,
    interview history scores, gamification points, global leaderboard,
    and calls CareerMentorAgent to supply dynamic recommendations.
    """
    user = request.user
    
    # 1. Fetch user profiles and gamification profile
    profile, _ = UserProfile.objects.get_or_create(user=user)
    gamification, _ = GamificationProfile.objects.get_or_create(user=user)
    
    # 2. Goals (PostgreSQL Breeth)
    active_goals = UserGoal.objects.filter(user=user, status__in=['active', 'pending']).order_by('-priority')[:3]
    
    # 3. Roadmap Progress
    roadmaps = UserRoadmap.objects.filter(user=user)
    avg_roadmap_progress = roadmaps.aggregate(Avg('progress_pct'))['progress_pct__avg'] or 0
    
    # 4. Mock Interview Scores
    interviews = InterviewSession.objects.filter(user=user, is_completed=True)
    avg_interview_score = interviews.aggregate(Avg('score'))['score__avg'] or 0
    completed_interviews = interviews.count()

    # 5. Weekly Learning Time calculation
    seven_days_ago = timezone.now() - timedelta(days=7)
    weekly_learning_events = LearningEvent.objects.filter(
        user=user,
        occurred_at__gte=seven_days_ago
    )
    weekly_learning_minutes = weekly_learning_events.aggregate(Sum('duration_minutes'))['duration_minutes__sum'] or 0
    
    # 6. Fetch Global Leaderboard rank from Valkey
    leaderboard = LeaderboardManager()
    user_rank_data = leaderboard.get_user_rank(user.username)
    leaderboard_rank = user_rank_data.get('rank')
    
    # Update score in Valkey in case of dev cache clears
    leaderboard.update_score(user.username, gamification.xp)

    # 7. Skills & Streaks
    skills = SkillRecord.objects.filter(user=user).order_by('-proficiency_level')[:5]

    # 8. Dynamic AI recommendations
    agent = CareerMentorAgent()
    prompt = (
        f"Provide 3 short, bulleted actionable recommendations for this candidate's career. "
        f"Target Role: {profile.target_role}. Target Experience: {profile.experience_level}.\n"
        f"Active Goals: {[g.title for g in active_goals]}\n"
        f"Skills: {[f'{s.skill_name}(Lvl {s.proficiency_level})' for s in skills]}\n"
        f"Weak Areas from Mock interviews: {[i.weak_areas for i in interviews if i.weak_areas]}\n"
        f"Format output as HTML items (e.g. <li>...</li>). Make them concise and practical."
    )
    
    ai_recommendations = agent.run(prompt)
    if not ai_recommendations.strip() or "<li>" not in ai_recommendations:
        ai_recommendations = (
            "<li>Start your enrolled roadmaps to cover core engineering skills.</li>"
            "<li>Take a mock interview session for Python internals to gauge metrics.</li>"
            "<li>Upload your resume file PDF to get ATS recommendation optimization checks.</li>"
        )

    # 9. Learning Chart Coordinates (for Chart.js rendering)
    chart_data = {
        'labels': ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'],
        'values': [0] * 7
    }
    
    # Map event counts to weekdays
    for event in weekly_learning_events:
        day_index = event.occurred_at.weekday()  # 0=Mon, 6=Sun
        chart_data['values'][day_index] += event.duration_minutes

    return render(request, 'dashboard/home.html', {
        'profile': profile,
        'gamification': gamification,
        'active_goals': active_goals,
        'avg_roadmap_progress': int(avg_roadmap_progress),
        'avg_interview_score': int(avg_interview_score),
        'completed_interviews': completed_interviews,
        'weekly_learning_time': weekly_learning_minutes,
        'leaderboard_rank': leaderboard_rank,
        'skills': skills,
        'ai_recommendations': ai_recommendations,
        'chart_values': json.dumps(chart_data['values']),
        'chart_labels': json.dumps(chart_data['labels'])
    })
