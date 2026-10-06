# Adaptive AI Exam Prep Agent

An intelligent, multi-agent AI exam preparation platform that acts as a personalized tutor, study planner, and coach. Built with a robust **FastAPI backend** (powered by LangGraph and LangChain) and a dynamic **React + Vite frontend**.

This system adapts dynamically to a student's performance, available study time, and specific exam syllabus to optimize learning outcomes.

## 🚀 How It Works

The platform operates on a **multi-agent architecture**, meaning different AI "agents" communicate with each other to manage your learning journey:

1. **Syllabus Parsing & Management:**
   - **How it works:** You upload your exam syllabus (PDF). The backend uses PyMuPDF to extract text, and the AI agents parse this unstructured text into a structured database of Subjects and Topics, complete with estimated difficulty and time requirements.

2. **Adaptive Study Planning:**
   - **How it works:** You input your target exam date and how many hours you can study per week. The **Orchestrator Agent** assigns work to the **Profile Analyzer** and **Coaching Advisor** to generate a week-by-week, day-by-day study plan. If you fall behind or ace topics quickly, the plan dynamically recalculates.

3. **Interactive AI Content Tutor:**
   - **How it works:** When studying a specific topic, you engage with the **Content Tutor Agent**. This agent operates in a conversational interface, explaining concepts at your level, generating analogies, and answering follow-up questions. It keeps track of your topic context so conversations remain highly relevant.

4. **Smart Assessments & Mastery Tracking:**
   - **How it works:** To test your knowledge, the **Question Generator Agent** creates quizzes tailored to your current mastery level of a topic. If you score well, the system increases the difficulty. Your scores feed into a mastery calculator that updates your overall progress dashboard.

## 🏗️ Project Architecture & Contents

The project is split into two main directories: `backend/` and `frontend/`.

### Backend (Python / FastAPI)
The backend serves as the brain of the application, managing data persistence and AI agent orchestration.

- **`app/agents/`:** The core AI logic built with LangGraph.
  - `orchestrator.py`: The main router that delegates tasks to specialized agents.
  - `content_tutor.py`: Specialized in explaining academic concepts.
  - `coaching_advisor.py`: Generates study strategies and motivational feedback.
  - `profile_analyzer.py`: Analyzes student metrics to adjust study plans.
  - `question_generator.py`: Generates dynamic quizzes.
- **`app/api/`:** RESTful endpoints organized by feature (auth, syllabus, study_plans, assessments, analytics, tutor).
- **`app/models/` & `app/schemas/`:** SQLAlchemy database models and Pydantic validation schemas.
- **`app/services/`:** Business logic, including the LLM abstraction service and mastery calculation algorithms.
- **Database:** SQLite (using AsyncSession) for local, lightweight data management.

### Frontend (React / Vite)
A modern, glassmorphic UI built with React, Vite, and custom CSS.

- **`src/pages/`:** 
  - `DashboardPage`: Overview of progress, upcoming study sessions, and quick actions.
  - `SyllabusPage`: PDF upload and manual topic management.
  - `StudyPlanPage`: View and regenerate adaptive study schedules.
  - `TutorPage`: Chat interface for the AI Content Tutor (supports Markdown rendering).
  - `PracticePage`: Interactive quiz interface.
  - `AnalyticsPage`: Detailed charts (using Recharts) showing mastery over time.
- **`src/context/`:** Manages global state, such as Authentication (JWT).
- **`src/services/api.js`:** Axios interceptors for handling backend communication and auth headers.

## 🛠️ Tech Stack

**Backend:**
- Python 3.10+
- FastAPI
- SQLAlchemy (Async)
- LangChain & LangGraph (Multi-Agent Orchestration)
- PyMuPDF (PDF processing)

**Frontend:**
- React 19 + Vite
- React Router DOM
- Custom CSS (Glassmorphism design system)
- Recharts (Data visualization)
- React-Markdown (Chat rendering)

## 💻 Getting Started

### Prerequisites
- Node.js (v18+ recommended)
- Python (v3.10+ recommended)

### 1. Clone the Repository
```bash
git clone https://github.com/sudarshan026/Adaptive-Exam-Prep-Agent.git
cd Adaptive-Exam-Prep-Agent
```

### 2. Backend Setup
```bash
cd backend
python -m venv venv
# Activate virtual environment (Windows: venv\Scripts\activate | Mac/Linux: source venv/bin/activate)

pip install -r requirements.txt

# Set up environment variables
cp .env.example .env
# Edit .env to add your OPENAI_API_KEY (required for AI features)

# Run the backend server
python -m uvicorn app.main:app --reload --port 8000
```
Backend API will be running at `http://localhost:8000`. API Docs available at `http://localhost:8000/docs`.

### 3. Frontend Setup
Open a new terminal window:
```bash
cd frontend
npm install

# Run the frontend development server
npm run dev
```
Frontend will be running at `http://localhost:5173`.

## 📄 License
MIT License
