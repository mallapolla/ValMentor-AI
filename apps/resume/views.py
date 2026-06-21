from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import HttpResponse
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions

from .models import Resume
from .serializers import ResumeSerializer
from .tasks import analyze_resume_task

# ──────────────────────────────────────────────────────────
# Django Template Views
# ──────────────────────────────────────────────────────────

@login_required
def resume_home(request):
    """Lists past resume uploads and accepts new PDF uploads."""
    resumes = Resume.objects.filter(user=request.user)
    
    if request.method == 'POST' and request.FILES.get('resume_file'):
        uploaded_file = request.FILES['resume_file']
        
        # File type validation
        if not uploaded_file.name.endswith('.pdf'):
            messages.error(request, "Only PDF files are supported for resume checks.")
            return redirect('resume:home')
            
        resume = Resume.objects.create(user=request.user, file=uploaded_file)
        
        # Launch Celery background analysis task
        analyze_resume_task.delay(resume.id)
        
        messages.success(request, "Resume uploaded successfully. Analysis started!")
        return redirect('resume:home')
        
    return render(request, 'resume/home.html', {
        'resumes': resumes
    })

@login_required
def resume_status(request, resume_id):
    """
    HTMX status polling endpoint.
    Refreshes analysis widget or prints final report once finished.
    """
    resume = get_object_or_404(Resume, id=resume_id, user=request.user)
    
    if resume.status in ['pending', 'processing']:
        # Poll again in 3 seconds
        html = f"""
        <div hx-get="{reverse_url('resume:status', resume.id)}" 
             hx-trigger="every 3s" 
             hx-swap="outerHTML" 
             class="p-6 rounded-xl border border-slate-700 bg-slate-800/50 flex flex-col items-center justify-center space-y-3">
            <div class="animate-spin rounded-full h-8 w-8 border-b-2 border-cyan-500"></div>
            <p class="text-slate-300 text-sm">AI Agent is analyzing your resume content...</p>
        </div>
        """
        return HttpResponse(html)
        
    # Once complete, render results summary card
    return render(request, 'resume/partials/results_card.html', {
        'resume': resume
    })

def reverse_url(view_name, *args):
    from django.urls import reverse
    return reverse(view_name, args=args)


# ──────────────────────────────────────────────────────────
# Django REST API Views (for external clients)
# ──────────────────────────────────────────────────────────

class APIResumeUploadView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        file = request.FILES.get('resume_file')
        if not file:
            return Response({'error': 'No resume file provided'}, status=status.HTTP_400_BAD_REQUEST)
            
        resume = Resume.objects.create(user=request.user, file=file)
        analyze_resume_task.delay(resume.id)
        
        return Response(ResumeSerializer(resume).data, status=status.HTTP_201_CREATED)
