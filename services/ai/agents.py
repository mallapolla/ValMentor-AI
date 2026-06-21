import logging
from strands import Agent
from .providers import AIProviderFactory, LitellmModelWrapper
from .tools import retrieve_user_memory, save_user_memory, update_user_skill

logger = logging.getLogger(__name__)

class ValMentorAgentBase:
    """Base class for ValMentor AI agents handling fallback options dynamically."""
    def __init__(self, system_prompt: str, use_tools: bool = True):
        self.system_prompt = system_prompt
        self.model = AIProviderFactory.get_model()
        self.use_tools = use_tools
        self.tools = [retrieve_user_memory, save_user_memory, update_user_skill] if use_tools else []
        
        # Instantiate strands Agent if model is not the fallback wrapper
        if not isinstance(self.model, LitellmModelWrapper):
            try:
                self.agent = Agent(
                    model=self.model,
                    tools=self.tools,
                    system_prompt=system_prompt
                )
            except Exception as e:
                logger.error(f"Failed to initialize Strands Agent: {e}. Using fallback client.")
                self.agent = None
        else:
            self.agent = None

    def run(self, prompt: str, user_id: int = None) -> str:
        """Executes agent logic, handling tools and fallback wrapper automatically."""
        # Inject user context into the prompt if user_id is provided and we aren't using tools directly
        if user_id and not self.use_tools:
            try:
                from django.contrib.auth import get_user_model
                from services.breeth.retrieval import BreethRetriever
                User = get_user_model()
                user = User.objects.get(id=user_id)
                retriever = BreethRetriever(user)
                mem_context = retriever.retrieve_context(prompt)
                prompt = f"Background Memory context:\n{mem_context}\n\nUser Query: {prompt}"
            except Exception as e:
                logger.error(f"Error fetching memory for prompt context: {e}")

        # Check if the keys are placeholders or not configured. If so, fallback to mock directly.
        use_mock = False
        from django.conf import settings
        provider = settings.AI_PROVIDER.lower()
        if provider == 'anthropic' and (not settings.ANTHROPIC_API_KEY or 'your-anthropic-api-key' in settings.ANTHROPIC_API_KEY):
            use_mock = True
        elif provider != 'anthropic' and (not settings.GOOGLE_API_KEY or 'your-google-api-key' in settings.GOOGLE_API_KEY):
            use_mock = True

        if not use_mock and self.agent:
            try:
                # Strands Agent call
                response = self.agent(prompt)
                return str(response)
            except Exception as e:
                logger.error(f"Strands Agent execution failed: {e}. Falling back.")
        
        # Fallback to direct client
        if not use_mock and isinstance(self.model, LitellmModelWrapper):
            try:
                return self.model(prompt=prompt, system_prompt=self.system_prompt)
            except Exception as e:
                logger.error(f"LiteLLM invocation failed: {e}. Falling back to mock data.")

        # Absolute fallback to mock data
        return self.get_mock_response(prompt)

    def get_mock_response(self, prompt: str) -> str:
        """Generates a realistic mock response for each agent type when API keys are missing or invalid."""
        # Extract actual user query if it's a structured prompt from MemoryFlowOrchestrator
        if "User Query: " in prompt:
            prompt_query = prompt.split("User Query: ")[-1].strip()
        else:
            prompt_query = prompt.strip()

        class_name = self.__class__.__name__
        if class_name == 'ResumeAnalyzerAgent':
            import json
            score = 75
            if "python" in prompt_query.lower() or "django" in prompt_query.lower():
                score = 85
            return json.dumps({
                "ats_score": score,
                "missing_skills": ["Docker", "Valkey/Redis", "Kubernetes", "CI/CD Pipeline"],
                "suggestions": [
                    "Incorporate specific projects using containerization (Docker) to show production-readiness.",
                    "Highlight cache optimization and session management experiences using Redis or Valkey.",
                    "Provide quantitative metrics of your accomplishments (e.g., 'improved query performance by 30%')."
                ],
                "job_matches": {
                    "Python/Django Developer": score + 5,
                    "Backend Systems Engineer": score,
                    "AI/ML Engineer": score - 15
                }
            })
        elif class_name == 'RoadmapAgent':
            import json
            return json.dumps({
                "title": "Backend Engineering Masterclass",
                "description": "Step-by-step roadmap to mastering backend development with a focus on databases, scaling, and robust frameworks.",
                "difficulty": "Intermediate to Advanced",
                "estimated_weeks": 10,
                "milestones": [
                    {
                        "title": "Django Deep Dive & API Design",
                        "description": "Master advanced Django concepts, ORM optimizations, REST Framework, and custom authentication.",
                        "topics": ["Django ORM Optimization", "DRF Serializers & Viewsets", "JWT & Custom Middleware", "Unit Testing Django Apps"]
                    },
                    {
                        "title": "Caching & Session Stores",
                        "description": "Implement caching architectures and real-time stores using Redis and Valkey.",
                        "topics": ["Valkey Data Structures", "Cache-Aside Pattern", "Session & Token Caching", "Pub/Sub Systems"]
                    },
                    {
                        "title": "Deployment, Containership & CI/CD",
                        "description": "Deploy backend systems using modern DevOps tools and cloud providers.",
                        "topics": ["Docker & Containerization", "Nginx Reverse Proxy", "GitHub Actions CI/CD", "AWS/GCP Hosting"]
                    }
                ]
            })
        elif class_name == 'InterviewAgent':
            prompt_lower = prompt_query.lower()
            if "hello" in prompt_lower or "start" in prompt_lower:
                return "Welcome to the ValMentor AI Mock Interview! I will be your interviewer. Let's start with a foundational backend question. Can you explain how Django's middleware works, and how it handles request/response flows?"
            elif "middleware" in prompt_lower or "request" in prompt_lower or "response" in prompt_lower:
                return "Excellent explanation! That shows you understand the onion architecture of Django's middleware. Let's move on to databases. In a high-traffic environment, how would you design a caching strategy using Redis/Valkey for user profile retrieval to reduce DB load? (Your score so far: 85/100)"
            else:
                return "Great response! You're demonstrating a strong grasp of backend engineering. Let's touch upon system design: how would you handle horizontal scaling for a Django application with a relational database? (Your score so far: 80/100)"
        else:
            p_lower = prompt_query.lower()
            if "python" in p_lower:
                return "Python is a versatile, high-level programming language known for its readability and massive ecosystem. In backend development, it powers robust frameworks like Django and FastAPI. It's also the industry standard for AI, machine learning, and data engineering. To accelerate your career, I recommend mastering object-oriented programming (OOP), decorators, generators, and memory management in Python."
            elif "django" in p_lower:
                return "Django is a high-level Python web framework that encourages rapid development and clean, pragmatic design. It follows the 'batteries-included' philosophy, providing built-in ORM, authentication, admin panel, and security out-of-the-box. For a backend engineering role, you should focus on database query optimization (select_related/prefetch_related), middleware, and REST API design using Django REST Framework."
            elif "valkey" in p_lower or "redis" in p_lower:
                return "Valkey (and Redis) is an open-source, in-memory key-value data store used as a database, cache, and message broker. In our ValMentor architecture, we use Valkey to store user session cache, sliding-window rate limit checks, and real-time leaderboard scores. Knowing how to design caching strategies (like Cache-Aside or Write-Through) and structuring data types (String, Hash, Sorted Sets) is a highly valued backend skill."
            elif "docker" in p_lower:
                return "Docker is a platform that uses containerization to package an application and all its dependencies together into a standardized container. This ensures that the application runs reliably across different environments (local development, staging, production). It's a critical DevOps skill to understand Dockerfiles, docker-compose orchestration, and container networking."
            elif "system design" in p_lower or "scale" in p_lower:
                return "System Design is the process of defining the architecture, interfaces, and data for a system to satisfy specified requirements. To build scalable web apps, you need to think about horizontal scaling, load balancers, caching layers (Valkey/Redis), database replication/sharding, and message queues (Celery/RabbitMQ) for background tasks."
            elif "chatgpt" in p_lower or "openai" in p_lower:
                return "ChatGPT, developed by OpenAI, is a state-of-the-art conversational AI model based on the GPT architecture. In system design, OpenAI provides REST APIs that let you integrate natural language understanding, embeddings, and code generation into applications. As an AI career coach, I recommend learning how to handle OpenAI API rate limits, structure system/user prompts, and optimize context windows."
            elif "claude" in p_lower or "anthropic" in p_lower:
                return "Claude is a family of large language models developed by Anthropic, designed to be helpful, harmless, and honest. Known for its massive context windows (up to 200k tokens) and advanced reasoning, Claude is excellent at code synthesis and complex analyses. In ValMentor, Claude is our default Strands Agent provider for conducting system design reviews, mock interviews, and personalized study roadmaps."
            elif "gemini" in p_lower or "google" in p_lower:
                return "Google Gemini is a highly capable multimodal AI model family. Unlike text-only models, Gemini was built from the ground up to be natively multimodal, processing text, images, audio, video, and code seamlessly. The Strands SDK supports Gemini natively via our updated google-genai integration. It's a great option for low-cost, high-context AI workloads."
            elif "llm" in p_lower or "large language model" in p_lower or "gpt" in p_lower:
                return "Large Language Models (LLMs) are deep learning algorithms trained on massive datasets to recognize, summarize, translate, predict, and generate content. As a backend or AI engineer, key skills include Prompt Engineering, Retrieval-Augmented Generation (RAG) architecture, context optimization, function calling (tool use), and vector database integrations."
            elif "agent" in p_lower or "strands" in p_lower:
                return "AI Agents are autonomous systems that use large language models as their core reasoning engine to plan tasks, execute actions using tools, and remember history. The Strands Agents SDK provides a model-driven framework to build these agents. In ValMentor, our agents use tool bindings (like retrieve_user_memory) to dynamically adjust career advice based on your profile database."
            elif "ai" in p_lower or "machine learning" in p_lower or "ml" in p_lower or "artificial intelligence" in p_lower:
                return "Artificial Intelligence and Machine Learning are revolutionary forces in tech. For software engineers pivoting to AI, you don't need a PhD in math; instead, focus on practical engineering: learn to build RAG pipelines, manage agent states, design memory systems (like our Breeth log layer), and implement semantic search using embeddings."
            elif "resume" in p_lower:
                return "A strong resume is crucial to getting past the ATS (Applicant Tracking System). I highly recommend going to our **ATS Resume Optimizer** section on the left sidebar to upload your PDF resume. I will run a keyword compliance check and score your resume, highlighting matching weaknesses and skills to add!"
            elif "interview" in p_lower:
                return "Technical interviews test your problem-solving, coding, database, and system architecture skills. Go to our **Grids & Interviews** section in the sidebar to start a real-time mock interview. I will guide you question-by-question, evaluate your answers, and provide detailed grading!"
            elif "roadmap" in p_lower:
                return "To structure your study path, check out our **Study Roadmaps** tab in the sidebar. You can enroll in pre-designed developer paths (like Python Developer or Django Expert), complete milestones, and watch your skills and leveling points grow!"
            else:
                return "I am your ValMentor AI Career Coach. Let's discuss your goals! We can plan your next career steps, practice system design interviews, or refine your resume. What would you like to focus on today?"





class CareerMentorAgent(ValMentorAgentBase):
    def __init__(self):
        super().__init__(
            system_prompt=(
                "You are ValMentor AI, a world-class Principal Software Engineer, UI/UX Designer, and Career Coach. "
                "Your goal is to guide the user in software engineering, backend systems, database designs (like PostgreSQL/Valkey), "
                "and cloud systems. Use your tools to retrieve the user's background details and save new facts. "
                "Always be supportive, clear, actionable, and detail-oriented. Suggest relevant technical milestones."
            ),
            use_tools=True
        )

class InterviewAgent(ValMentorAgentBase):
    def __init__(self):
        super().__init__(
            system_prompt=(
                "You are the Mock Interviewer for ValMentor AI. "
                "Conduct highly professional software engineering mock interviews. "
                "Present code snippets, design problems, database questions (especially SQL, PostgreSQL, Valkey keys structure). "
                "Ask one question at a time. After the user responds, evaluate their answer, suggest improvements, "
                "provide a score (0 to 100), and guide them through their weak areas. Do not go off-topic."
            ),
            use_tools=False  # Keep it conversational and focus on the interview session directly
        )

class RoadmapAgent(ValMentorAgentBase):
    def __init__(self):
        super().__init__(
            system_prompt=(
                "You are a Career Path Roadmap Planner. "
                "Analyze the user's target job role and skill profile. "
                "Generate a highly detailed learning roadmap. "
                "You must respond ONLY with a valid JSON document containing: "
                "'title', 'description', 'difficulty', 'estimated_weeks', and 'milestones'. "
                "Each milestone must have a 'title', 'description', and a list of 'topics'. "
                "Do not include any normal chat markdown wrapper (like ```json), just return raw JSON."
            ),
            use_tools=False
        )

class ResumeAnalyzerAgent(ValMentorAgentBase):
    def __init__(self):
        super().__init__(
            system_prompt=(
                "You are a professional Resume Analyzer & ATS Optimizer. "
                "Analyze the extracted resume text and evaluate its quality. "
                "Calculate an ATS score (0 to 100). Identify missing skills, improvement suggestions, "
                "and match percentage for a target job role. "
                "Respond ONLY with a valid JSON document containing keys: "
                "'ats_score', 'missing_skills', 'suggestions', and 'job_matches'. "
                "Do not include any conversational text or markdown wrappers, just return raw JSON."
            ),
            use_tools=False
        )
