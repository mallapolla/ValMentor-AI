# ValMentor AI — Your AI Career & Interview Mentor

ValMentor AI is a production-ready AI agent platform designed to help software engineers prepare for technical careers, mock interviews, and personalized study roadmaps. The platform uses a tiered memory architecture composed of Valkey (short-term cached sessions) and Breeth (long-term database configurations).

---

## Technical Stack

*   **Backend:** Python 3.11, Django 5+, Django REST Framework (DRF), Celery, Docker
*   **Databases:** PostgreSQL 16, Valkey 8 (Redis-compatible client)
*   **Frontend:** Django Templates + Tailwind CSS, HTMX, Alpine.js, Chart.js
*   **AI:** Strands Agents SDK, Fallback LiteLLM models support (Claude / Gemini APIs)

---

## Core Architecture & Memory Flow

```
User Query
    ↓
1. Retrieve Session Context (Valkey user:{id}:session)
    ↓
2. Retrieve Chat History Cache (Valkey user:{id}:chat_history)
    ↓
3. Retrieve Long-term Memory Logs (Breeth PostgreSQL models)
    ↓
4. Assemble Context Prompt Block
    ↓
5. Invoke Strands AI Agent (Claude / Gemini fallback)
    ↓
6. Update Caches (Valkey) & Write Long-term Memory Logs (Breeth)
    ↓
Response Returned to User (HTMX/SSE Streaming)
```

---

## Project Structure

```
valmentor/
├── docker/                          # Docker Configuration files
├── config/                          # Django Settings (development/production)
├── apps/
│   ├── accounts/                    # Custom User profiles & JWT Authentication
│   ├── chat/                        # AI Coach Conversation threads
│   ├── interviews/                  # Interactive technical Mock Sessions
│   ├── roadmaps/                    # Tech Milestone learning paths
│   └── resume/                      # PDF upload and ATS parser
├── services/
│   ├── ai/                          # Strands agents and LiteLLM wrappers
│   ├── valkey/                      # Connection pooler, sliding windows, sorted sets
│   └── breeth/                      # PostgreSQL background memory logs
└── templates/                       # Glassmorphic dark layouts
```

---

## Local Setup & Docker Launch

### 1. Configure Environment Variables
Copy `.env.example` into `.env` and fill in your AI API credentials:
```bash
cp .env.example .env
```
Ensure you provide at least one of:
*   `ANTHROPIC_API_KEY` (for Claude models)
*   `GOOGLE_API_KEY` (for Gemini models)

### 2. Boot the Application Stack
Execute the docker-compose orchestrator to start PostgreSQL, Valkey, Django, Nginx, and Celery workers:
```bash
docker-compose up --build
```
This boots 6 Docker services:
*   `postgres`: Storing user profiles and Breeth long-term logs.
*   `valkey`: Managing sliding rate limits, response caches, and sorted set scoreboards.
*   `django`: Servicing Gunicorn processes.
*   `nginx`: Proxying HTTP static assets and supporting SSE streams.
*   `celery_worker` & `celery_beat`: Parsing PDFs asynchronously.

### 3. Initialize Databases
Once docker containers are healthy, migrate databases and load initial achievements databases:
```bash
docker-compose exec django python manage.py migrate
docker-compose exec django python manage.py createsuperuser
```

Open `http://localhost/` in your browser.

---

## Running Automated Tests

Run the test suite using standard Django test execution commands:
```bash
python manage.py test apps/ services/ --verbosity=2
```
This executes accounts profile signals verification, Valkey trimming tests, rate limits validations, and Breeth context retrieval checks.
