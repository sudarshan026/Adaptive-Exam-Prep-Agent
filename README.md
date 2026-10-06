# Adaptive AI Exam Prep Agent

An intelligent, AI-powered exam preparation platform that adapts to your learning pace. It features a robust Python FastAPI backend for AI processing and data management, and a dynamic React (Vite) frontend for an interactive learning experience.

## Features

- **Syllabus Management & Parsing:** Upload syllabus PDFs which are parsed into subjects and topics automatically using AI or heuristic fallbacks.
- **Adaptive Study Plans:** Generates dynamic study plans based on available hours and learning goals.
- **AI Content Tutor:** Interactive AI tutor for deep dives into specific topics.
- **Smart Assessments:** Auto-generates quizzes and assessments to test knowledge and adjust difficulty.
- **Analytics & Mastery:** Track your learning progress, topic mastery, and study time through an intuitive dashboard.
- **Multi-Agent Orchestration:** Powered by LangGraph/LangChain agents (Orchestrator, Content Tutor, Coaching Advisor, Profile Analyzer).

## Tech Stack

### Backend
- **Framework:** FastAPI
- **Database:** SQLite (with SQLAlchemy and AsyncSession)
- **AI/LLM:** LangChain, LangGraph, OpenAI (configurable)
- **PDF Parsing:** PyMuPDF (`fitz`)

### Frontend
- **Framework:** React + Vite
- **Styling:** Vanilla CSS with custom modern glassmorphic design and CSS variables
- **Routing:** React Router DOM

## Prerequisites

- Node.js (v18+ recommended)
- Python (v3.10+ recommended)
- Git

## Getting Started

### 1. Clone the repository

```bash
git clone https://github.com/sudarshan026/Adaptive-Exam-Prep-Agent.git
cd Adaptive-Exam-Prep-Agent
```

### 2. Backend Setup

```bash
cd backend
# Create virtual environment (optional but recommended)
python -m venv venv
# Activate virtual environment (Windows)
venv\Scripts\activate
# Activate virtual environment (Mac/Linux)
# source venv/bin/activate

# Install requirements
pip install -r requirements.txt

# Environment variables
cp .env.example .env
# Edit .env and add your OPENAI_API_KEY if needed.

# Run the backend
python -m uvicorn app.main:app --reload --port 8000
```
The backend API will run at `http://localhost:8000`. You can view the API documentation at `http://localhost:8000/docs`.

### 3. Frontend Setup

Open a new terminal window:

```bash
cd frontend

# Install dependencies
npm install

# Run the frontend
npm run dev
```
The frontend will typically run at `http://localhost:5173`.

## Application Structure

- `/backend/app/agents`: Contains the AI agents (Coaching Advisor, Content Tutor, Profile Analyzer, Syllabus Manager).
- `/backend/app/api`: FastAPI route handlers (auth, syllabus, study plans, tutor, assessments).
- `/backend/app/models`: SQLAlchemy database models.
- `/backend/app/services`: Business logic (LLM service, mastery calculator).
- `/frontend/src/pages`: React pages (Dashboard, Syllabus, Tutor, Practice, Analytics).
- `/frontend/src/components`: Reusable React components.

## Demo Data

If you need a demo syllabus to test the PDF upload feature, you can run the provided script in the backend to generate mock syllabus PDFs:
```bash
cd backend
pip install reportlab
python generate_demo_syllabus.py
```
This will generate `demo_cs_syllabus.pdf` and `demo_ml_syllabus.pdf` that you can upload in the Syllabus page.

## License

MIT License
