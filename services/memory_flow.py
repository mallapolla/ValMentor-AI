import logging
from django.conf import settings
from services.valkey.session_memory import SessionMemoryManager
from services.valkey.chat_memory import ChatMemoryManager
from services.valkey.response_cache import ResponseCacheManager
from services.breeth.memory import BreethMemoryManager
from services.breeth.retrieval import BreethRetriever
from services.ai.agents import CareerMentorAgent

logger = logging.getLogger(__name__)

class MemoryFlowOrchestrator:
    """
    Coordinates session memory, short-term history, long-term PostgreSQL memory,
    and cache stores to assemble full context prompts for LLM invocation.
    """
    def __init__(self):
        self.session_manager = SessionMemoryManager()
        self.chat_manager = ChatMemoryManager()
        self.cache_manager = ResponseCacheManager()
        self.mentor_agent = CareerMentorAgent()

    def process_user_query(self, user, query: str) -> str:
        """
        Runs the complete Memory Flow pipeline:
        1. Query Response Cache (Valkey)
        2. Retrieve session context (Valkey)
        3. Retrieve short-term history (Valkey)
        4. Retrieve long-term memory (Breeth)
        5. Build prompt context & generate response
        6. Update caches & write long-term logs (Breeth)
        """
        # 1. Check Response Cache
        cached_res = self.cache_manager.get_cached_response(query)
        if cached_res:
            logger.info("Found query response in Valkey cache.")
            return cached_res

        # 2. Retrieve session context (e.g. current topic, session length)
        session_data = self.session_manager.get_all_session_data(user.id) or {}
        current_topic = session_data.get("current_topic", "General Software Engineering")

        # 3. Retrieve short-term chat history
        chat_history = self.chat_manager.get_chat_history(user.id)
        chat_context = ""
        if chat_history:
            chat_context = "\n".join([f"{msg['role']}: {msg['content']}" for msg in chat_history[-6:]])

        # 4. Retrieve long-term memory via Breeth
        retriever = BreethRetriever(user)
        breeth_context = retriever.retrieve_context(query)

        # 5. Build full agent prompt
        full_prompt = (
            f"Active Session Topic: {current_topic}\n\n"
            f"Long-term Background Memory:\n{breeth_context}\n\n"
            f"Recent Conversational Messages:\n{chat_context}\n\n"
            f"User Query: {query}\n"
        )

        # Run the agent
        response_text = self.mentor_agent.run(full_prompt, user_id=user.id)

        # 6. Save message to Valkey short-term history
        self.chat_manager.add_message(user.id, "user", query)
        self.chat_manager.add_message(user.id, "assistant", response_text)

        # Cache response in Valkey
        self.cache_manager.set_cached_response(query, response_text)

        # Add learning event audit log in Breeth long-term memory
        breeth_manager = BreethMemoryManager(user)
        breeth_manager.record_learning_activity(
            event_type='chat_interaction',
            topic=current_topic,
            details={"query": query[:100], "response_length": len(response_text)}
        )

        return response_text
