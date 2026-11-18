# 🚀 AAIEA Production Deployment Guide

This guide provides step-by-step instructions for deploying the **Adaptive AI Exam Prep Agent (AAIEA)** to **Render** or **Railway** directly from your GitHub repository.

---

## 📋 Pre-Deployment Checklist

Before deploying, ensure you have:
1. Pushed your latest code to your GitHub repository: [`https://github.com/sudarshan026/Adaptive-Exam-Prep-Agent`](https://github.com/sudarshan026/Adaptive-Exam-Prep-Agent)
2. A free account on [Render](https://render.com) or [Railway](https://railway.app)
3. *(Optional)* A **Groq API Key** from [console.groq.com](https://console.groq.com) (if left blank, the app runs in deterministic demo mode)

---

## 🌐 Method 1: Deploying to Render (Recommended)

Render offers free hosting for both the FastAPI web service and the React static site.

### Option A: 1-Click Blueprint Deploy (Fastest)

1. Log in to [Render Dashboard](https://dashboard.render.com).
2. Click **New +** in the top navigation and select **Blueprint**.
3. Connect your GitHub repository: `Adaptive-Exam-Prep-Agent`.
4. Render will automatically detect the [`render.yaml`](render.yaml) file and provision:
   * **`aaiea-backend`** (Python Web Service)
   * **`aaiea-frontend`** (React Static Site)
5. Fill in the optional environment variable `GROQ_API_KEY` if you have one.
6. Click **Apply**.
7. Once deployed, note your backend URL (e.g., `https://aaiea-backend.onrender.com`).
8. Go to the **`aaiea-frontend`** settings → **Environment Variables**, and set:
   * `VITE_API_URL`: `https://aaiea-backend.onrender.com/api`
9. Trigger a **Manual Deploy → Clear build cache & deploy** on the frontend service so Vite bakes in the backend URL.

---

### Option B: Manual Setup on Render

#### Step 1: Deploy the Backend (Web Service)
1. In Render Dashboard, click **New +** → **Web Service**.
2. Connect your GitHub repository.
3. Configure the settings:
   * **Name**: `aaiea-backend`
   * **Root Directory**: `backend`
   * **Language / Runtime**: `Python`
   * **Build Command**: `pip install -r requirements.txt`
   * **Start Command**: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
   * **Instance Type**: `Free`
4. Under **Environment Variables**, add:
   * `APP_ENV`: `production`
   * `APP_DEBUG`: `false`
   * `JWT_SECRET_KEY`: *(Click "Generate" or enter a secure random 32+ character string)*
   * `JWT_ALGORITHM`: `HS256`
   * `JWT_EXPIRATION_MINUTES`: `1440`
   * `CORS_ORIGINS`: `*` *(or your frontend URL after creating it)*
   * `GROQ_API_KEY`: *(Your Groq API key, optional)*
5. Click **Create Web Service**. Wait for the build to complete and copy the backend URL (e.g. `https://aaiea-backend.onrender.com`).

#### Step 2: Deploy the Frontend (Static Site)
1. In Render Dashboard, click **New +** → **Static Site**.
2. Connect the same GitHub repository.
3. Configure the settings:
   * **Name**: `aaiea-frontend`
   * **Root Directory**: `frontend`
   * **Build Command**: `npm install && npm run build`
   * **Publish Directory**: `dist`
4. Under **Environment Variables**, add:
   * `VITE_API_URL`: `https://aaiea-backend.onrender.com/api` *(replace with your backend URL + `/api`)*
5. Under **Redirects / Rewrites**, add:
   * **Type**: `Rewrite`
   * **Source**: `/*`
   * **Destination**: `/index.html`
   *(This ensures client-side routes like `/study-plan` and `/tutor` resolve correctly on page refresh)*
6. Click **Create Static Site**.

---

## 🚂 Method 2: Deploying to Railway

Railway runs both frontend and backend seamlessly with built-in PostgreSQL database support.

### Step 1: Create a New Project on Railway
1. Log in to [Railway](https://railway.app).
2. Click **New Project** → **Deploy from GitHub repo**.
3. Select `sudarshan026/Adaptive-Exam-Prep-Agent`.

### Step 2: Configure the Backend Service
1. In the Railway project canvas, select the newly added service and open its **Settings**:
   * **Service Name**: Rename to `backend`
   * **Root Directory**: Set to `/backend`
2. Open the **Variables** tab and add:
   * `PORT`: `8000`
   * `APP_ENV`: `production`
   * `APP_DEBUG`: `false`
   * `JWT_SECRET_KEY`: `your-random-32-character-secret`
   * `CORS_ORIGINS`: `*`
   * `GROQ_API_KEY`: `your-groq-api-key` *(optional)*
3. In **Settings** → **Networking**, click **Generate Domain** (e.g. `aaiea-backend.up.railway.app`).

*(Optional PostgreSQL Database)*:
* Click **+ New** in your Railway canvas → **Database** → **Add PostgreSQL**.
* Railway will create a database. Click your `backend` service → **Variables** → **Add Reference** → select `DATABASE_URL` from the Postgres database.
* Our backend automatically converts standard `postgres://` URLs to async `postgresql+asyncpg://` without any extra configuration.

### Step 3: Add the Frontend Service
1. In the same Railway project canvas, click **+ New** → **GitHub Repo** → select the same repository again.
2. In the new service **Settings**:
   * **Service Name**: Rename to `frontend`
   * **Root Directory**: Set to `/frontend`
   * **Build Command**: `npm run build`
   * **Start Command**: `npx serve dist -s -p $PORT`
3. In the **Variables** tab, add:
   * `VITE_API_URL`: `https://aaiea-backend.up.railway.app/api` *(your backend domain + `/api`)*
4. In **Settings** → **Networking**, click **Generate Domain**.

---

## 🔑 Environment Variables Reference

| Variable | Service | Required | Default | Description |
| :--- | :---: | :---: | :---: | :--- |
| `DATABASE_URL` | Backend | No | `sqlite+aiosqlite:///./exam_prep.db` | SQLite or PostgreSQL connection string |
| `JWT_SECRET_KEY` | Backend | **Yes (Prod)** | `dev-secret-key...` | Cryptographic secret for signing auth tokens |
| `JWT_ALGORITHM` | Backend | No | `HS256` | JWT signature algorithm |
| `GROQ_API_KEY` | Backend | No | `""` | Groq API key for LLM agents (demo mode if empty) |
| `CORS_ORIGINS` | Backend | No | `*` | Allowed CORS origins (comma-separated or `*`) |
| `VITE_API_URL` | Frontend | **Yes (Prod)** | `/api` | Base URL of the backend API (e.g. `https://api.domain.com/api`) |

---

## 🩺 Verifying Your Deployment

Once deployed, run these quick sanity checks:

1. **Backend Health Check**:
   Open `https://<your-backend-url>/api/health` in your browser.
   Expected response:
   ```json
   {"status": "healthy", "demo_mode": false}
   ```
2. **Interactive API Documentation**:
   Open `https://<your-backend-url>/docs` to view the Swagger UI and test endpoints directly.
3. **Frontend Application**:
   Open `https://<your-frontend-url>/` in your browser:
   * Register a new student account at `/register`.
   * Complete the quick onboarding quiz at `/onboarding`.
   * Test the **AI Tutor** at `/tutor`.
   * Test the **Planner-Reviewer Strategy** on `/study-plan`.
   * Test the **Parallel Remediation Pipeline** on `/analytics`.
