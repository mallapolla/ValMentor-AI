import logging
from django.db import models
from django.utils import timezone
from django.conf import settings
import requests
from .models import MemoryEntry, UserGoal, SkillRecord, LearningEvent

logger = logging.getLogger(__name__)

class BreethRetriever:
    """
    Builds a retrieval context of the user's long-term history before each AI generation.
    Matches queries by keyword locally, retrieves graph memories from the Breeth API if configured, and formats text context.
    """
    def __init__(self, user):
        self.user = user

    def retrieve_context(self, current_query: str = "") -> str:
        """
        Retrieves relevant historical facts, active goals, skill metrics, and activities.
        Also retrieves cognitive intent memories from the cloud Breeth API if available.
        Compiles a structured prompt context block for injection.
        """
        context_parts = []
        
        # 1. Retrieve Active Goals
        goals = UserGoal.objects.filter(user=self.user, status__in=['active', 'pending']).order_by('-priority')
        if goals.exists():
            context_parts.append("USER'S CURRENT GOALS:")
            for g in goals:
                target_str = f" by {g.target_date}" if g.target_date else ""
                context_parts.append(f"- {g.title} ({g.get_priority_display()} priority){target_str}: {g.description}")
            context_parts.append("")

        # 2. Retrieve Skills & Proficiencies
        skills = SkillRecord.objects.filter(user=self.user).order_by('-proficiency_level')
        if skills.exists():
            context_parts.append("USER'S SKILLS:")
            skills_str = [f"{s.skill_name} (Level {s.proficiency_level}/5)" for s in skills]
            context_parts.append(", ".join(skills_str))
            context_parts.append("")

        # 3. Retrieve Intent-Aware Memories from Remote Breeth API
        remote_memories = []
        api_key = getattr(settings, 'BREETH_API_KEY', '')
        if api_key and api_key != 'your-breeth-api-key' and current_query:
            try:
                url = "https://api.thebreeth.com/v1/search"
                headers = {
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json"
                }
                payload = {
                    "query": current_query
                }
                response = requests.post(url, json=payload, headers=headers, timeout=3)

                if response.status_code == 200:
                    data = response.json()
                    # Robust parsing for multiple potential return formats (lists vs dictionaries)
                    if isinstance(data, list):
                        for item in data:
                            if isinstance(item, dict) and "content" in item:
                                remote_memories.append(item["content"])
                            elif isinstance(item, str):
                                remote_memories.append(item)
                    elif isinstance(data, dict):
                        items = data.get("results") or data.get("data") or data.get("memories")
                        if isinstance(items, list):
                            for item in items:
                                if isinstance(item, dict) and "content" in item:
                                    remote_memories.append(item["content"])
                                elif isinstance(item, str):
                                    remote_memories.append(item)
                        elif "content" in data:
                            remote_memories.append(data["content"])
                else:
                    logger.warning(f"Breeth query API returned error status: {response.status_code} - {response.text}")
            except Exception as e:
                logger.error(f"Failed to query Breeth API: {e}")

        if remote_memories:
            context_parts.append("COGNITIVE & INTENT MEMORIES FROM BREETH CLOUD:")
            for rm in remote_memories[:5]:
                context_parts.append(f"- {rm}")
            context_parts.append("")

        # 4. Retrieve Relevant Factual Memory Entries locally
        memories = MemoryEntry.objects.filter(user=self.user)
        if current_query:
            words = [w.lower() for w in current_query.split() if len(w) > 3]
            if words:
                query_filter = models.Q()
                for word in words:
                    query_filter |= models.Q(content__icontains=word)
                memories = memories.filter(query_filter)
        
        # Get recent 5 memories anyway if keyword filters returned too few
        if memories.count() < 3:
            memories = MemoryEntry.objects.filter(user=self.user).order_by('-created_at')[:5]
        else:
            memories = memories.order_by('-relevance_score', '-created_at')[:5]

        if memories.exists():
            context_parts.append("KNOWN FACTS & BACKGROUND ABOUT USER:")
            for m in memories:
                # Update last accessed timestamp
                try:
                    m.last_accessed = timezone.now()
                    m.save(update_fields=['last_accessed'])
                except Exception:
                    pass
                context_parts.append(f"- {m.content}")
            context_parts.append("")

        # 5. Recent Learning History
        recent_events = LearningEvent.objects.filter(user=self.user).order_by('-occurred_at')[:3]
        if recent_events.exists():
            context_parts.append("RECENT ACTIVITY SUMMARY:")
            for e in recent_events:
                context_parts.append(f"- Completed {e.get_event_type_display()} on topic '{e.topic}'")
            context_parts.append("")

        # Compile final prompt block
        if not context_parts:
            return "No previous background memory available for this user yet."
            
        return "\n".join(context_parts)
