import os
import json
import logging
from celery import shared_task
import PyPDF2
from django.contrib.auth import get_user_model

from .models import Resume
from services.ai.agents import ResumeAnalyzerAgent
from services.breeth.memory import BreethMemoryManager
from apps.gamification.signals import award_xp_and_streak

logger = logging.getLogger(__name__)
User = get_user_model()

@shared_task
def analyze_resume_task(resume_id):
    """
    Asynchronous Celery task to parse resume PDFs and retrieve AI suggestions.
    Extracts text, submits to ResumeAnalyzerAgent, and caches results.
    """
    try:
        resume = Resume.objects.get(id=resume_id)
        resume.status = 'processing'
        resume.save()
        
        # 1. Extract text from PDF
        pdf_path = resume.file.path
        extracted_text = ""
        
        with open(pdf_path, 'rb') as pdf_file:
            reader = PyPDF2.PdfReader(pdf_file)
            for page_num in range(len(reader.pages)):
                page = reader.pages[page_num]
                extracted_text += page.extract_text() or ""
                
        if not extracted_text.strip():
            raise ValueError("No text could be extracted from the uploaded PDF document.")

        # 2. Call AI Agent
        agent = ResumeAnalyzerAgent()
        prompt = (
            f"Review this software engineering candidate's resume text and calculate its suitability. "
            f"Candidate targets roles like Python/Django Developer, AI Engineer.\n\n"
            f"Resume Content:\n{extracted_text}"
        )
        
        ai_res = agent.run(prompt)
        
        # Strip code markdown block wrappers if present
        if "```json" in ai_res:
            ai_res = ai_res.split("```json")[1].split("```")[0].strip()
        elif "```" in ai_res:
            ai_res = ai_res.split("```")[1].split("```")[0].strip()

        # Parse AI response JSON
        parsed = json.loads(ai_res)
        
        resume.ats_score = int(parsed.get('ats_score', 70))
        resume.missing_skills = parsed.get('missing_skills', [])
        resume.suggestions = parsed.get('suggestions', [])
        resume.job_matches = parsed.get('job_matches', {})
        resume.status = 'completed'
        resume.save()
        
        # 3. Write memory log in Breeth database
        user = resume.user
        breeth_manager = BreethMemoryManager(user)
        
        # Log learning event
        breeth_manager.record_learning_activity(
            event_type='resume_upload',
            topic='Resume Analysis',
            details={"ats_score": resume.ats_score, "missing_skills": len(resume.missing_skills)}
        )
        
        # Log missing skills as weakness facts to focus learning roadmaps
        for skill in resume.missing_skills:
            breeth_manager.add_memory(
                content=f"Candidate lacks or needs to improve skills in: '{skill}' according to resume evaluation.",
                memory_type='weakness'
            )

        # 4. Award XP points
        award_xp_and_streak(user, 100)  # +100 XP for resume check
        logger.info(f"Resume {resume_id} successfully parsed by AI.")

    except Exception as e:
        logger.error(f"Failed to analyze resume {resume_id}: {str(e)}")
        try:
            resume = Resume.objects.get(id=resume_id)
            resume.status = 'failed'
            resume.save()
        except:
            pass
