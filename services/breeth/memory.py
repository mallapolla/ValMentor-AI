import logging
import threading
from typing import List, Dict, Any
from django.utils import timezone
from django.conf import settings
import requests
from .models import MemoryEntry, UserGoal, SkillRecord, LearningEvent

logger = logging.getLogger(__name__)

class BreethMemoryManager:
    """
    CRUD operation handlers to persist long term records in PostgreSQL.
    Maintains information structures for users' profile history, skill profiles, and goals.
    Also synchronizes these facts to the cloud Breeth memory API if configured.
    """
    def __init__(self, user):
        self.user = user

    def _sync_to_breeth(self, text: str):
        """Helper to post memory episodes to the remote Breeth API in a background thread."""
        api_key = getattr(settings, 'BREETH_API_KEY', '')
        if api_key and api_key != 'your-breeth-api-key':
            def target():
                try:
                    url = "https://api.thebreeth.com/v1/episodes"
                    headers = {
                        "Authorization": f"Bearer {api_key}",
                        "Content-Type": "application/json"
                    }
                    payload = {
                        "content": text.strip(),
                        "extract_intent": True
                    }
                    # Increase timeout to 30s since this is processed asynchronously by the LLM
                    response = requests.post(url, json=payload, headers=headers, timeout=30)
                    if response.status_code not in [200, 201]:
                        logger.warning(f"Breeth API returned error status: {response.status_code} - {response.text}")
                    else:
                        logger.info("Successfully synced memory episode to Breeth API.")
                except Exception as e:
                    logger.error(f"Failed to post memory episode to Breeth API: {e}")

            threading.Thread(target=target, daemon=True).start()


    def add_memory(self, content: str, memory_type: str = 'general', metadata: dict = None) -> MemoryEntry:
        """Stores a long-term fact or preference about the user."""
        entry = MemoryEntry.objects.create(
            user=self.user,
            content=content.strip(),
            memory_type=memory_type,
            metadata=metadata or {}
        )
        # Sync to Breeth API
        self._sync_to_breeth(f"Known Fact ({memory_type}): {content}")
        return entry

    def upsert_goal(self, title: str, description: str = '', priority: str = 'medium', target_date=None, status: str = 'active') -> UserGoal:
        """Saves a career path roadmap goal."""
        goal, created = UserGoal.objects.update_or_create(
            user=self.user,
            title=title.strip(),
            defaults={
                'description': description,
                'priority': priority,
                'target_date': target_date,
                'status': status
            }
        )
        # Sync to Breeth API
        self._sync_to_breeth(f"Study Goal: {title} - {description} (Priority: {priority}, Target Date: {target_date})")
        return goal

    def record_learning_activity(self, event_type: str, topic: str, duration_minutes: int = 0, details: dict = None) -> LearningEvent:
        """Appends an event audit log to the user's historical feed."""
        event = LearningEvent.objects.create(
            user=self.user,
            event_type=event_type,
            topic=topic,
            duration_minutes=duration_minutes,
            details=details or {}
        )
        # Sync learning activity to Breeth API
        self._sync_to_breeth(f"Completed learning activity of type '{event_type}' on topic '{topic}'. Duration: {duration_minutes} mins.")
        return event

    def update_skill_proficiency(self, skill_name: str, level: int, category: str = '', evidence: dict = None) -> SkillRecord:
        """Updates or registers a technological skill entry."""
        level = max(1, min(5, level))  # force 1-5 scale
        
        # Merge evidence details
        record, created = SkillRecord.objects.get_or_create(
            user=self.user,
            skill_name=skill_name.strip(),
            defaults={'category': category, 'proficiency_level': level, 'evidence': evidence or {}, 'last_assessed': timezone.now()}
        )
        if not created:
            record.proficiency_level = level
            if evidence:
                record.evidence.update(evidence)
            record.last_assessed = timezone.now()
            record.save()
            
        # Sync skill updates to Breeth API
        self._sync_to_breeth(f"Skill Proficiency Level: User skill '{skill_name}' is assessed at level {level}/5 (Category: {category}).")
        return record

    def get_user_skills(self) -> List[Dict[str, Any]]:
        """Returns users registered skills list."""
        return list(SkillRecord.objects.filter(user=self.user).values(
            'skill_name', 'category', 'proficiency_level', 'last_assessed'
        ))

    def get_active_goals(self) -> List[UserGoal]:
        """Returns all in-progress user goals."""
        return list(UserGoal.objects.filter(user=self.user, status__in=['active', 'pending']))
