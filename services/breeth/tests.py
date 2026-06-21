from django.test import TestCase
from django.contrib.auth import get_user_model
from services.breeth.models import MemoryEntry, UserGoal, SkillRecord, LearningEvent
from services.breeth.memory import BreethMemoryManager
from services.breeth.retrieval import BreethRetriever

User = get_user_model()

class BreethMemoryTests(TestCase):
    """Verifies that Breeth memory writes goals, skills, and formats contexts accurately."""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='breeth_candidate',
            email='candidate@breeth.ai',
            password='SecurityPassword456'
        )
        self.manager = BreethMemoryManager(self.user)
        self.retriever = BreethRetriever(self.user)

    def test_goals_and_skills_persistence(self):
        # 1. Add active goal
        self.manager.upsert_goal(
            title="Master Django REST Framework",
            description="Complete all API projects with proper serialization.",
            priority="high"
        )
        goals = UserGoal.objects.filter(user=self.user)
        self.assertEqual(goals.count(), 1)
        self.assertEqual(goals.first().status, 'active')

        # 2. Add skill record
        self.manager.update_skill_proficiency(
            skill_name="Python",
            level=4,
            category="Backend Programming"
        )
        skills = SkillRecord.objects.filter(user=self.user)
        self.assertEqual(skills.count(), 1)
        self.assertEqual(skills.first().proficiency_level, 4)

    def test_retrieval_compiles_valid_prompt_context(self):
        # Add a goal and background facts
        self.manager.upsert_goal("Learn Valkey Keys", "Explore Zset data structures.")
        self.manager.add_memory("Enjoys building backend APIs in Python.", memory_type="preference")
        
        context = self.retriever.retrieve_context("caching API endpoints")
        
        # Verify text format includes elements
        self.assertIn("USER'S CURRENT GOALS:", context)
        self.assertIn("Learn Valkey Keys", context)
        self.assertIn("KNOWN FACTS & BACKGROUND ABOUT USER:", context)
        self.assertIn("Enjoys building backend APIs in Python.", context)
