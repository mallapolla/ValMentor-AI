import json
import logging
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils.text import slugify
from django.http import HttpResponse, JsonResponse
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions

from .models import Roadmap, UserRoadmap
from .serializers import RoadmapSerializer, UserRoadmapSerializer
from services.ai.agents import RoadmapAgent
from services.breeth.memory import BreethMemoryManager
from apps.gamification.signals import award_xp_and_streak

logger = logging.getLogger(__name__)

# ──────────────────────────────────────────────────────────
# Django Template Views
# ──────────────────────────────────────────────────────────

@login_required
def roadmap_list(request):
    """Renders lists of predefined roadmaps and user's currently enrolled roadmaps."""
    predefined = Roadmap.objects.filter(slug__in=['python-developer', 'django-developer', 'ai-engineer', 'backend-developer'])
    user_enrolled = UserRoadmap.objects.filter(user=request.user)
    enrolled_ids = user_enrolled.values_list('roadmap_id', flat=True)
    
    # Exclude enrolled from general predefined list
    available = predefined.exclude(id__in=enrolled_ids)
    
    # Custom/AI-generated roadmaps for user
    custom_roadmaps = Roadmap.objects.exclude(slug__in=['python-developer', 'django-developer', 'ai-engineer', 'backend-developer']).filter(
        id__in=enrolled_ids
    )

    return render(request, 'roadmaps/list.html', {
        'user_roadmaps': user_enrolled,
        'available_roadmaps': available,
        'custom_roadmaps': custom_roadmaps
    })

@login_required
def roadmap_detail(request, slug):
    """Renders details of a single roadmap with progress checkmarks."""
    roadmap = get_object_or_404(Roadmap, slug=slug)
    user_roadmap = UserRoadmap.objects.filter(user=request.user, roadmap=roadmap).first()

    return render(request, 'roadmaps/detail.html', {
        'roadmap': roadmap,
        'user_roadmap': user_roadmap
    })

@login_required
def enroll_roadmap(request, roadmap_id):
    """Enrolls the user in a standard roadmap."""
    roadmap = get_object_or_404(Roadmap, id=roadmap_id)
    UserRoadmap.objects.get_or_create(user=request.user, roadmap=roadmap)
    messages.success(request, f"Successfully enrolled in: {roadmap.title}!")
    return redirect('roadmaps:detail', slug=roadmap.slug)

@login_required
def generate_custom_roadmap(request):
    """
    Form target to generate custom roadmaps using RoadmapAgent.
    Parses prompt parameters and returns dynamically created milestone trees.
    """
    if request.method == 'POST':
        target_role = request.POST.get('target_role', '').strip()
        experience = request.POST.get('experience', 'mid')
        
        if not target_role:
            messages.error(request, "Target role description is required.")
            return redirect('roadmaps:list')

        # Run AI roadmap planner agent
        agent = RoadmapAgent()
        prompt = (
            f"Generate a customized learning roadmap for a developer aiming for the job role: '{target_role}'. "
            f"Candidate current experience level: {experience}."
        )
        
        ai_res = agent.run(prompt)
        
        # Strip code markdown block wrappers if present
        if "```json" in ai_res:
            ai_res = ai_res.split("```json")[1].split("```")[0].strip()
        elif "```" in ai_res:
            ai_res = ai_res.split("```")[1].split("```")[0].strip()

        try:
            parsed = json.loads(ai_res)
            
            # Generate unique slug
            title = parsed.get('title', f"AI Path: {target_role}")
            slug = slugify(f"{title}-{request.user.id}")
            
            # Save new Roadmap specification
            roadmap, created = Roadmap.objects.update_or_create(
                slug=slug,
                defaults={
                    'title': title,
                    'category': parsed.get('category', target_role),
                    'description': parsed.get('description', f"AI Mentor generated guide for {target_role}"),
                    'difficulty': parsed.get('difficulty', experience.capitalize()),
                    'estimated_weeks': int(parsed.get('estimated_weeks', 8)),
                    'milestones': parsed.get('milestones', [])
                }
            )
            
            # Automatically Enroll
            UserRoadmap.objects.get_or_create(user=request.user, roadmap=roadmap)
            
            # Log Breeth activity
            breeth_manager = BreethMemoryManager(request.user)
            breeth_manager.record_learning_activity(
                event_type='roadmap_milestone',
                topic=title,
                details={"action": "generated_roadmap", "slug": slug}
            )
            
            # Add to goals
            breeth_manager.upsert_goal(
                title=f"Complete {title}",
                description=f"Finish dynamic learning modules for {target_role}.",
                priority='high'
            )

            messages.success(request, f"New custom roadmap '{title}' generated by AI!")
            return redirect('roadmaps:detail', slug=roadmap.slug)
            
        except Exception as e:
            logger.error(f"Failed to generate custom roadmap: {e}")
            messages.error(request, "Failed to compile custom path. Falling back to default list.")
            return redirect('roadmaps:list')

    return redirect('roadmaps:list')

@login_required
def complete_milestone(request, user_roadmap_id, milestone_id):
    """
    Checks/unchecks a roadmap milestone.
    Calculates completion percentages, grants 50 XP, and audits progress via HTMX.
    """
    user_roadmap = get_object_or_404(UserRoadmap, id=user_roadmap_id, user=request.user)
    completed = user_roadmap.completed_milestones
    milestone_id = int(milestone_id)
    
    action = request.GET.get('action', 'complete')
    
    if action == 'complete':
        if milestone_id not in completed:
            completed.append(milestone_id)
            # Award XP & streak
            award_xp_and_streak(request.user, 50)
            
            # Log activity in Breeth memory
            breeth_manager = BreethMemoryManager(request.user)
            breeth_manager.record_learning_activity(
                event_type='roadmap_milestone',
                topic=user_roadmap.roadmap.title,
                details={"completed_milestone_id": milestone_id}
            )
    else:
        if milestone_id in completed:
            completed.remove(milestone_id)

    # Recalculate progress percentage
    total_milestones = len(user_roadmap.roadmap.milestones)
    user_roadmap.completed_milestones = completed
    user_roadmap.progress_pct = int((len(completed) / total_milestones) * 100) if total_milestones > 0 else 0
    user_roadmap.save()
    
    # Check if fully complete
    if user_roadmap.progress_pct == 100 and action == 'complete':
        # Final complete goal update
        try:
            breeth_manager = BreethMemoryManager(request.user)
            breeth_manager.upsert_goal(
                title=f"Complete {user_roadmap.roadmap.title}",
                status='completed'
            )
        except Exception:
            pass

    # HTMX response block
    html = f"""
    <div id="milestone-{milestone_id}-status" class="flex items-center space-x-3">
        <span class="text-sm font-semibold {'text-emerald-400' if action == 'complete' else 'text-slate-400'}">
            {'Completed' if action == 'complete' else 'Pending'}
        </span>
        <button hx-get="{reverse_url('roadmaps:complete_milestone', user_roadmap.id, milestone_id)}?action={'revert' if action == 'complete' else 'complete'}" 
                hx-target="#milestone-{milestone_id}-status" 
                hx-swap="outerHTML" 
                class="px-3 py-1 text-xs rounded border border-slate-700 bg-slate-800 hover:bg-slate-700 text-slate-200">
            {'Undo' if action == 'complete' else 'Mark Complete'}
        </button>
        <script>
            // Live DOM update for progress indicators
            const progressFill = document.getElementById("roadmap-progress-fill");
            const progressText = document.getElementById("roadmap-progress-text");
            if (progressFill && progressText) {{
                progressFill.style.width = "{user_roadmap.progress_pct}%";
                progressText.innerText = "{user_roadmap.progress_pct}% Completed";
            }}
        </script>
    </div>
    """
    return HttpResponse(html)

def reverse_url(view_name, *args):
    from django.urls import reverse
    return reverse(view_name, args=args)


# ──────────────────────────────────────────────────────────
# Django REST API Views (for external clients)
# ──────────────────────────────────────────────────────────

class APIRoadmapListView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        roadmaps = Roadmap.objects.filter(slug__in=['python-developer', 'django-developer', 'ai-engineer', 'backend-developer'])
        serializer = RoadmapSerializer(roadmaps, many=True)
        return Response(serializer.data)
