from strands import tool
from django.contrib.auth import get_user_model
from services.breeth.memory import BreethMemoryManager
from services.breeth.retrieval import BreethRetriever

User = get_user_model()

@tool
def retrieve_user_memory(user_id: int, current_query: str) -> str:
    """
    Retrieves the long-term context facts, goals, and skill records for the user.
    Use this to pull background details before answering a user question.
    """
    try:
        user = User.objects.get(id=user_id)
        retriever = BreethRetriever(user)
        return retriever.retrieve_context(current_query)
    except User.DoesNotExist:
        return "User not found."

@tool
def save_user_memory(user_id: int, content: str, memory_type: str) -> str:
    """
    Saves a newly extracted long-term fact, preference, strength, or weakness about the user.
    Use this when the user shares new details about their career, experience, target job, or skillset.
    """
    try:
        user = User.objects.get(id=user_id)
        manager = BreethMemoryManager(user)
        manager.add_memory(content=content, memory_type=memory_type)
        return f"Successfully saved new long-term memory of type '{memory_type}'."
    except User.DoesNotExist:
        return "User not found."

@tool
def update_user_skill(user_id: int, skill_name: str, level: int, category: str) -> str:
    """
    Updates or adds a technical skill proficiency level for the user (scale 1-5).
    Use this when the user demonstrates or mentions a technical skill or when graded in interviews.
    """
    try:
        user = User.objects.get(id=user_id)
        manager = BreethMemoryManager(user)
        manager.update_skill_proficiency(skill_name=skill_name, level=level, category=category)
        return f"Successfully updated skill '{skill_name}' to level {level}/5."
    except User.DoesNotExist:
        return "User not found."
