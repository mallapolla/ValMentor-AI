import json
import logging
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.urls import reverse
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions

from .models import InterviewSession, InterviewQuestion
from .serializers import InterviewSessionSerializer
from services.ai.agents import InterviewAgent
from services.breeth.memory import BreethMemoryManager
from services.valkey.leaderboard import LeaderboardManager
from apps.gamification.signals import award_xp_and_streak

logger = logging.getLogger(__name__)

# Constants
MAX_QUESTIONS_PER_SESSION = 5

# ──────────────────────────────────────────────────────────
# Django Template Views
# ──────────────────────────────────────────────────────────

@login_required
def interview_home(request):
    """Lists completed interviews and lets user configure a new mock session."""
    sessions = InterviewSession.objects.filter(user=request.user)
    
    categories = [
        ('python', 'Python Programming'),
        ('django', 'Django Framework'),
        ('rest_apis', 'REST APIs & Web Services'),
        ('sql', 'SQL & Databases'),
        ('postgresql', 'PostgreSQL Internals'),
        ('machine_learning', 'Machine Learning'),
        ('data_structures', 'Data Structures & Algorithms'),
        ('system_design', 'System Design')
    ]
    
    return render(request, 'interviews/home.html', {
        'sessions': sessions,
        'categories': categories
    })

@login_required
def start_interview(request):
    """Configures and boots a new mock interview session, generating Q1."""
    if request.method == 'POST':
        category = request.POST.get('category', 'python')
        difficulty = request.POST.get('difficulty', 'mid')
        
        # Create session
        session = InterviewSession.objects.create(
            user=request.user,
            category=category,
            difficulty=difficulty
        )
        
        # Generate the first question using AI
        agent = InterviewAgent()
        prompt = (
            f"Generate a mock interview question for a candidate. "
            f"Category: {category}. Difficulty: {difficulty}. "
            f"Make it clear, challenging, and technical."
        )
        question_text = agent.run(prompt)
        
        # Save first question
        InterviewQuestion.objects.create(session=session, question_text=question_text)
        
        return redirect('interviews:session', session_id=session.id)
    return redirect('interviews:home')

@login_required
def interview_session(request, session_id):
    """Main interview workspace where user views and answers the current active question."""
    session = get_object_or_404(InterviewSession, id=session_id, user=request.user, is_completed=False)
    
    # Fetch active question (unanswered)
    active_question = session.questions.filter(user_answer="").first()
    
    # If no unanswered question, generate another one or complete
    if not active_question:
        questions_count = session.questions.count()
        if questions_count >= MAX_QUESTIONS_PER_SESSION:
            # End session
            return complete_interview_session(session, request)
        
        # Generate next question
        agent = InterviewAgent()
        prompt = (
            f"Generate the next mock interview question for this candidate session. "
            f"Category: {session.category}. Difficulty: {session.difficulty}. "
            f"Avoid duplicating previous questions: "
            f"{[q.question_text for q in session.questions.all()]}."
        )
        question_text = agent.run(prompt)
        active_question = InterviewQuestion.objects.create(session=session, question_text=question_text)

    # Progress fraction helper
    progress_index = session.questions.count()

    return render(request, 'interviews/session.html', {
        'session': session,
        'question': active_question,
        'progress_index': progress_index,
        'max_questions': MAX_QUESTIONS_PER_SESSION
    })

@login_required
def submit_answer(request, session_id):
    """Grades the current answer and updates session state."""
    session = get_object_or_404(InterviewSession, id=session_id, user=request.user, is_completed=False)
    question = session.questions.filter(user_answer="").first()
    
    if not question:
        return redirect('interviews:session', session_id=session.id)

    if request.method == 'POST':
        user_answer = request.POST.get('answer', '').strip()
        
        if not user_answer:
            messages.warning(request, "Please enter an answer before submitting.")
            return redirect('interviews:session', session_id=session.id)

        # Grade the answer using AI
        agent = InterviewAgent()
        prompt = (
            f"Review this interview question and answer. Grade it and output exactly in JSON format:\n"
            f"{{\n"
            f"  \"feedback\": \"detailed feedback here\",\n"
            f"  \"score\": 85\n"
            f"}}\n"
            f"Score must be an integer between 0 and 100.\n\n"
            f"Question: {question.question_text}\n"
            f"Answer: {user_answer}"
        )
        
        ai_res = agent.run(prompt)
        
        # Clean JSON wrappers if LLM returned them
        if "```json" in ai_res:
            ai_res = ai_res.split("```json")[1].split("```")[0].strip()
        elif "```" in ai_res:
            ai_res = ai_res.split("```")[1].split("```")[0].strip()

        # Parse AI response
        score = 60  # fallback
        feedback = "Response parsed. Evaluated by ValMentor AI."
        try:
            parsed = json.loads(ai_res)
            score = int(parsed.get('score', 60))
            feedback = parsed.get('feedback', feedback)
        except Exception:
            # Fallback parsing in case JSON format was ignored by LLM
            if "score" in ai_res.lower():
                try:
                    score = int(''.join(filter(str.isdigit, ai_res)))
                except:
                    pass
            feedback = ai_res

        # Save question details
        question.user_answer = user_answer
        question.ai_feedback = feedback
        question.score = score
        question.save()
        
        # Move forward
        return redirect('interviews:session', session_id=session.id)
        
    return redirect('interviews:session', session_id=session.id)

def complete_interview_session(session, request):
    """Calculates final scores, updates Valkey and Breeth memory, and closes session."""
    session.is_completed = True
    
    # Calculate average score
    questions = session.questions.all()
    total_score = sum([q.score for q in questions])
    session.score = total_score // questions.count() if questions.exists() else 0
    
    # Ask AI for overall feedback and weak areas detection
    agent = InterviewAgent()
    prompt = (
        f"Analyze this complete interview session. Categorize weak areas and provide suggestions. "
        f"Format output as JSON with keys 'feedback' (text) and 'weak_areas' (list of strings).\n\n"
        f"Questions and Answers:\n"
        + "\n".join([f"Q: {q.question_text}\nA: {q.user_answer}\nScore: {q.score}/100" for q in questions])
    )
    
    ai_summary = agent.run(prompt)
    if "```json" in ai_summary:
        ai_summary = ai_summary.split("```json")[1].split("```")[0].strip()
    
    try:
        parsed = json.loads(ai_summary)
        session.feedback = parsed.get('feedback', 'Well done.')
        session.weak_areas = parsed.get('weak_areas', [])
    except Exception:
        session.feedback = ai_summary
        session.weak_areas = ["General topics"]
        
    session.save()

    # 1. Update Breeth Long-term Memory
    breeth_manager = BreethMemoryManager(request.user)
    breeth_manager.record_learning_activity(
        event_type='interview_session',
        topic=session.category,
        details={"score": session.score, "weak_areas": session.weak_areas}
    )
    
    # Create database memory entries for identified weaknesses
    for weak in session.weak_areas:
        breeth_manager.add_memory(
            content=f"User showed room for improvement in '{weak}' during a mock interview for category '{session.category}'.",
            memory_type='weakness'
        )

    # 2. Update Valkey Global Leaderboard
    leaderboard = LeaderboardManager()
    leaderboard.increment_score(request.user.username, session.score * 10)  # XP formula: score * 10

    # 3. Award Gamification XP and Streaks
    award_xp_and_streak(request.user, session.score * 10)

    messages.success(request, f"Mock interview completed! You scored {session.score}%. +{session.score * 10} XP earned!")
    return redirect('interviews:results', session_id=session.id)

@login_required
def interview_results(request, session_id):
    """Display final grading summary for completed interview session."""
    session = get_object_or_404(InterviewSession, id=session_id, user=request.user, is_completed=True)
    return render(request, 'interviews/results.html', {
        'session': session,
        'questions': session.questions.all()
    })


# ──────────────────────────────────────────────────────────
# Django REST API Views (for external clients)
# ──────────────────────────────────────────────────────────

class APIInterviewSessionView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, session_id):
        session = get_object_or_404(InterviewSession, id=session_id, user=request.user)
        return Response(InterviewSessionSerializer(session).data)
