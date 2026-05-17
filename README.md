# MediaMind AI 🧠

> An AI-powered Document & Multimedia Q&A Web Application

MediaMind AI allows users to upload PDF documents, audio, and video files and interact with an intelligent AI chatbot to ask questions, generate summaries, extract timestamps, and perform semantic search — all powered by Google Gemini and local Whisper transcription.

---

## Table of Contents

- [Features](#features)
- [Tech Stack](#tech-stack)
- [Project Structure](#project-structure)
- [Prerequisites](#prerequisites)
- [Setup & Installation](#setup--installation)
- [Environment Variables](#environment-variables)
- [Running the Application](#running-the-application)
- [API Documentation](#api-documentation)
- [Frontend Guide](#frontend-guide)
- [Testing](#testing)
- [CI/CD Pipeline](#cicd-pipeline)
- [Docker Configuration](#docker-configuration)
- [Architecture Overview](#architecture-overview)

---

## Features

- **PDF Upload & Q&A** — Upload PDF documents and ask natural language questions about the content
- **Audio Transcription** — Automatic transcription of MP3, WAV, M4A files using faster-whisper (local, free)
- **Video Transcription** — Extract and query video content (MP4, AVI, MOV, MKV) with timestamp support
- **AI-Powered Chatbot** — Google Gemini 2.5 Flash answers questions based strictly on uploaded content
- **Smart Summarization** — AI-generated structured summaries with key points, topics, and word count
- **Timestamp Extraction** — Find exact timestamps in audio/video for specific topics or questions
- **File Serving** — Stream original uploaded files directly from the API
- **Semantic Vector Search** — pgvector-powered similarity search across all uploaded documents
- **Chat History** — Persistent conversation sessions stored per document
- **Background Processing** — File processing happens asynchronously so uploads return instantly
- ⚡ **Real-time Streaming** — Word-by-word streaming responses via Server-Sent Events (SSE)
- 🔐 **Google OAuth Authentication** — Secure login with Google, JWT-protected endpoints, per-user data isolation

---

## Tech Stack

### Backend
| Component | Technology | Purpose |
|---|---|---|
| Framework | FastAPI (Python 3.11) | REST API |
| LLM | Google Gemini 2.5 Flash | Q&A, Summarization, Streaming |
| LLM Framework | LangChain | LLM integration |
| Transcription | faster-whisper (local) | Audio/Video to text |
| PDF Extraction | pdfplumber + PyPDF2 | Text extraction from PDFs |
| Embeddings | sentence-transformers (all-MiniLM-L6-v2) | Vector embeddings |
| Database | PostgreSQL 16 + pgvector | Data + vector storage |
| ORM | SQLAlchemy (async) | Database interactions |
| Server | Uvicorn | ASGI server |
| Streaming | Server-Sent Events (SSE) | Real-time word-by-word responses |
| Authentication | Google OAuth 2.0 + JWT | Secure user authentication |

### Frontend
| Component | Technology | Purpose |
|---|---|---|
| Framework | React + Vite | UI |
| Styling | Tailwind CSS | Design system |
| HTTP Client | Axios + Fetch API | API calls + SSE streaming |
| Routing | React Router DOM | Page navigation |
| Icons | Lucide React | Icon library |
| Media Player | HTML5 native | Audio/Video playback |
| Auth | Google OAuth + localStorage | Token management |

### Infrastructure
| Component | Technology | Purpose |
|---|---|---|
| Containerization | Docker | Application packaging |
| Orchestration | Docker Compose | Multi-container setup |
| CI/CD | GitHub Actions | Automated testing & build |
| Vector DB | pgvector (PostgreSQL extension) | Semantic search |

---

## Project Structure

```
MediaMind-AI/
│
├── .github/
│   └── workflows/
│       └── ci.yml                      # GitHub Actions CI/CD pipeline
│
├── backend/
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py                     # FastAPI app entry point, lifespan, routers
│   │   │
│   │   ├── api/
│   │   │   ├── __init__.py
│   │   │   └── routes/
│   │   │       ├── __init__.py
│   │   │       ├── upload.py           # File upload, list, get, delete, serve, search
│   │   │       ├── chat.py             # Q&A, summarize, stream, chat history endpoints
│   │   │       └── auth.py             # Google OAuth login, callback, me, logout
│   │   │
│   │   ├── core/
│   │   │   ├── __init__.py
│   │   │   ├── config.py               # Settings, env vars (pydantic-settings)
│   │   │   ├── database.py             # Async PostgreSQL engine, session, Base
│   │   │   └── security.py             # JWT creation/verification, auth dependencies
│   │   │
│   │   ├── models/
│   │   │   ├── __init__.py
│   │   │   ├── user.py                 # User model (Google OAuth users)
│   │   │   ├── document.py             # Document model (files, embeddings, status)
│   │   │   └── chat.py                 # ChatSession and ChatMessage models
│   │   │
│   │   ├── services/
│   │   │   ├── __init__.py
│   │   │   ├── pdf_service.py          # PDF text extraction (pdfplumber + PyPDF2)
│   │   │   ├── whisper_service.py      # Audio/video transcription + timestamps
│   │   │   ├── gemini_service.py       # LangChain + Gemini Q&A, summarization, streaming
│   │   │   └── vector_service.py       # Embeddings, chunking, pgvector search
│   │   │
│   │   └── tests/
│   │       ├── __init__.py
│   │       ├── conftest.py             # Shared fixtures, isolated test DB per test
│   │       ├── test_upload.py          # Upload, list, get, delete, serve endpoints
│   │       ├── test_chat.py            # Q&A, summarize, session endpoints
│   │       ├── test_auth.py            # OAuth flow, JWT, user endpoints
│   │       ├── test_gemini_service.py  # Gemini Q&A, summarize, timestamps, streaming
│   │       ├── test_pdf_service.py     # PDF extraction, validation
│   │       ├── test_whisper_service.py # Transcription, timestamps, save/load
│   │       ├── test_vector_service.py  # Embeddings, chunking, search
│   │       ├── test_models.py          # DB models, enums, settings
│   │       └── test_process_document.py # Background processing task
│   │
│   ├── uploads/                        # Uploaded files (Docker volume)
│   ├── .env                            # Environment variables (not committed)
│   ├── .env.example                    # Template for environment variables
│   ├── .coveragerc                     # Coverage configuration
│   ├── pytest.ini                      # Pytest configuration
│   ├── requirements.txt                # Python dependencies
│   └── Dockerfile                      # Backend container definition
│
├── frontend/
│   └── frontend/
│       ├── src/
│       │   ├── components/
│       │   │   ├── Chat/
│       │   │   │   ├── ChatInput.jsx       # Message input box
│       │   │   │   ├── ChatMessage.jsx     # Individual chat bubble + streaming cursor
│       │   │   │   ├── ChatWindow.jsx      # Full chat interface with SSE streaming
│       │   │   │   └── TimestampCard.jsx   # Clickable timestamp for audio/video
│       │   │   ├── Document/
│       │   │   │   ├── DocumentCard.jsx    # Single document card
│       │   │   │   ├── DocumentList.jsx    # Grid of all documents
│       │   │   │   └── SummaryPanel.jsx    # Summary display panel
│       │   │   ├── Layout/
│       │   │   │   ├── Navbar.jsx          # Top navigation + search + user avatar + logout
│       │   │   │   └── Sidebar.jsx         # Side navigation
│       │   │   ├── Player/
│       │   │   │   └── MediaPlayer.jsx     # Audio/video player with seek
│       │   │   ├── Upload/
│       │   │   │   ├── UploadProgress.jsx  # Upload + processing status
│       │   │   │   └── UploadZone.jsx      # Drag & drop upload area
│       │   │   └── ProtectedRoute.jsx      # Redirects to login if not authenticated
│       │   ├── pages/
│       │   │   ├── Home.jsx                # Landing + upload page
│       │   │   ├── Library.jsx             # All documents page
│       │   │   ├── DocumentView.jsx        # Single document + chat page
│       │   │   ├── Login.jsx               # Google OAuth login page
│       │   │   └── AuthCallback.jsx        # Handles OAuth redirect, saves token
│       │   ├── services/
│       │   │   ├── api.js                  # All Axios API calls + streaming fetch
│       │   │   └── auth.js                 # Token management (get/set/remove/login/logout)
│       │   ├── App.jsx                     # Router setup with protected routes
│       │   ├── main.jsx                    # React entry point
│       │   └── index.css                   # Global styles + Tailwind
│       ├── Dockerfile                      # Frontend container
│       ├── nginx.conf                      # Nginx config for production
│       ├── package.json
│       ├── tailwind.config.js
│       └── vite.config.js
│
├── docker-compose.yml                  # Multi-container orchestration
├── .gitignore
└── README.md
```

---

## Prerequisites

- **Docker Desktop** — [Download here](https://www.docker.com/products/docker-desktop/)
- **Docker Compose** — Included with Docker Desktop
- **Google Gemini API Key** — Free at [Google AI Studio](https://aistudio.google.com/apikey)
- **Google OAuth Credentials** — Free at [Google Cloud Console](https://console.cloud.google.com)
- **Git** — For cloning the repository

---

## Setup & Installation

### 1. Clone the Repository

```bash
git clone https://github.com/fuzail-pixel/MediaMind-AI-.git
cd MediaMind-AI-
```

### 2. Set Up Google OAuth

1. Go to [Google Cloud Console](https://console.cloud.google.com)
2. Create a new project
3. Go to **APIs & Services** → **OAuth consent screen** → External
4. Go to **Credentials** → **Create Credentials** → **OAuth 2.0 Client ID**
5. Application type: **Web application**
6. Add Authorized redirect URI: `http://localhost:8000/api/v1/auth/callback`
7. Copy the **Client ID** and **Client Secret**

### 3. Configure Environment Variables

Create the `.env` file inside the `backend/` folder:

```bash
cp backend/.env.example backend/.env
```

Edit `backend/.env` with your values:

```env
GEMINI_API_KEY=your_gemini_api_key_here
DATABASE_URL=postgresql://mediamind:mediamind123@db:5432/mediamind_db
UPLOAD_DIR=uploads
MAX_FILE_SIZE_MB=50

# Google OAuth
GOOGLE_CLIENT_ID=your_google_client_id
GOOGLE_CLIENT_SECRET=your_google_client_secret
SECRET_KEY=your_random_secret_key_here
FRONTEND_URL=http://localhost:3000
```

Generate a secure SECRET_KEY:
```bash
python -c "import secrets; print(secrets.token_hex(32))"
```

### 4. Build and Start

```bash
docker-compose up --build
```

First build takes 10-15 minutes (downloads Whisper model, installs ML dependencies).
Subsequent starts take ~30 seconds.

### 5. Verify

- Backend API: http://localhost:8000/health
- Interactive Docs: http://localhost:8000/docs
- Frontend: http://localhost:3000

---

## Environment Variables

| Variable | Description | Example |
|---|---|---|
| `GEMINI_API_KEY` | Google Gemini API key | `AIza...` |
| `DATABASE_URL` | PostgreSQL connection string | `postgresql://user:pass@db:5432/dbname` |
| `UPLOAD_DIR` | Directory for uploaded files | `uploads` |
| `MAX_FILE_SIZE_MB` | Maximum upload file size | `50` |
| `GOOGLE_CLIENT_ID` | Google OAuth client ID | `123...apps.googleusercontent.com` |
| `GOOGLE_CLIENT_SECRET` | Google OAuth client secret | `GOCSPX-...` |
| `SECRET_KEY` | JWT signing secret (random, secure) | `a3f8...` |
| `FRONTEND_URL` | Frontend URL for OAuth redirect | `http://localhost:3000` |

---

## Running the Application

### Development (with hot reload)

```bash
docker-compose up
```

The backend automatically reloads on file changes thanks to uvicorn `--reload` flag.

### Stop the Application

```bash
docker-compose down
```

### Stop and Remove All Data (including database)

```bash
docker-compose down -v
```

### Rebuild After Dependency Changes

```bash
docker-compose build --no-cache
docker-compose up
```

---

## API Documentation

Full interactive documentation: **http://localhost:8000/docs**

Base URL: `http://localhost:8000/api/v1`

> **Note:** All endpoints except `/auth/login`, `/auth/callback`, `/auth/logout`, and `/health` require a valid JWT token in the Authorization header:
> ```
> Authorization: Bearer eyJ...your_token...
> ```

### Auth Endpoints

#### Login with Google
```
GET /auth/login
→ Redirects to Google OAuth login page (no token required)
```

#### OAuth Callback
```
GET /auth/callback?code=...
→ Exchanges Google code for user info
→ Creates/updates user in DB
→ Returns JWT token
→ Redirects to: http://localhost:3000/auth/callback?token=eyJ...
```

#### Get Current User
```
GET /auth/me
Authorization: Bearer {token}

Response 200:
{
  "id": "uuid",
  "email": "user@gmail.com",
  "full_name": "Fuzail Rehman",
  "avatar_url": "https://lh3.googleusercontent.com/...",
  "is_active": true,
  "created_at": "2026-05-15T10:00:00Z"
}
```

#### Logout
```
POST /auth/logout

Response 200:
{
  "message": "Logged out successfully. Please delete your token."
}
```

### Upload Endpoints

#### Upload a File
```
POST /upload
Authorization: Bearer {token}
Content-Type: multipart/form-data
Body: file (PDF, MP3, MP4, WAV, M4A, AVI, MOV, MKV — max 50MB)

Response 201:
{
  "message": "File uploaded. Processing started in background.",
  "document_id": "uuid",
  "filename": "document.pdf",
  "file_type": "pdf",
  "file_size_kb": 125.5,
  "status": "pending"
}
```

#### List All Documents
```
GET /documents
Authorization: Bearer {token}

Response 200:
{
  "total": 3,
  "documents": [
    {
      "id": "uuid",
      "filename": "document.pdf",
      "file_type": "pdf",
      "file_size_kb": 125.5,
      "status": "completed",
      "created_at": "2026-05-12T10:00:00Z"
    }
  ]
}
```

#### Get Document Details
```
GET /documents/{document_id}
Authorization: Bearer {token}

Response 200:
{
  "id": "uuid",
  "filename": "document.pdf",
  "file_type": "pdf",
  "file_size_kb": 125.5,
  "status": "completed",
  "summary": "AI generated summary...",
  "extracted_text": "First 500 chars...",
  "duration": null,
  "created_at": "2026-05-12T10:00:00Z"
}
```

#### Delete Document
```
DELETE /documents/{document_id}
Authorization: Bearer {token}

Response 200:
{
  "message": "Document 'document.pdf' deleted successfully"
}
```

#### Serve/Stream File
```
GET /documents/{document_id}/file
Authorization: Bearer {token}

Response 200: File stream with correct MIME type
```

#### Semantic Search
```
GET /search?q=your search query
Authorization: Bearer {token}

Response 200:
{
  "query": "machine learning",
  "total": 2,
  "results": [
    {
      "document_id": "uuid",
      "filename": "ml_paper.pdf",
      "file_type": "PDF",
      "similarity": 0.89,
      "excerpt": "First 300 chars of relevant content..."
    }
  ]
}
```

### Chat Endpoints

#### Ask a Question
```
POST /chat/ask
Authorization: Bearer {token}
Content-Type: application/json

Body:
{
  "document_id": "uuid",
  "question": "What is the main topic?",
  "session_id": "uuid"  (optional — omit for new session)
}

Response 200:
{
  "session_id": "uuid",
  "question": "What is the main topic?",
  "answer": "The main topic is...",
  "confidence": 0.95,
  "excerpt": "Relevant text from document...",
  "timestamps": [],
  "document": {
    "id": "uuid",
    "filename": "document.pdf",
    "file_type": "pdf"
  }
}

For audio/video, timestamps field contains:
"timestamps": [
  {
    "start": 12.5,
    "end": 24.0,
    "text": "Segment text here",
    "relevance": "Why this matches",
    "timestamp_formatted": "00:00:12"
  }
]
```

#### Stream Answer (Real-time) ⚡
```
POST /chat/stream
Authorization: Bearer {token}
Content-Type: application/json

Body:
{
  "document_id": "uuid",
  "question": "What is the main topic?",
  "session_id": "uuid"  (optional)
}

Response: Server-Sent Events (text/event-stream)
data: {"type": "session", "session_id": "uuid"}
data: {"type": "token", "content": "The "}
data: {"type": "token", "content": "main "}
data: {"type": "token", "content": "topic "}
data: {"type": "done", "full_answer": "The main topic is..."}

Event types:
- session → contains session_id for conversation continuity
- token   → single word to append to UI in real time
- done    → streaming complete, full answer saved to DB
- error   → something went wrong
```

#### Summarize Document
```
POST /chat/summarize
Authorization: Bearer {token}
Content-Type: application/json

Body:
{
  "document_id": "uuid"
}

Response 200:
{
  "document_id": "uuid",
  "filename": "document.pdf",
  "cached": false,
  "summary_data": {
    "summary": "Full 2-3 paragraph summary...",
    "key_points": ["Point 1", "Point 2", "Point 3"],
    "topics": ["Topic 1", "Topic 2"],
    "word_count_estimate": 500
  }
}
```

#### Get Chat History
```
GET /chat/sessions/{document_id}
Authorization: Bearer {token}

Response 200:
{
  "sessions": [
    {
      "session_id": "uuid",
      "title": "First question asked",
      "created_at": "2026-05-12T10:00:00Z",
      "messages": [
        {
          "role": "user",
          "content": "What is this about?",
          "timestamps": null,
          "confidence": null,
          "created_at": "2026-05-12T10:00:00Z"
        },
        {
          "role": "assistant",
          "content": "This document is about...",
          "timestamps": null,
          "confidence": 0.95,
          "created_at": "2026-05-12T10:00:00Z"
        }
      ]
    }
  ]
}
```

#### Get All Sessions
```
GET /chat/sessions
Authorization: Bearer {token}

Response 200:
{
  "total": 5,
  "sessions": [
    {
      "session_id": "uuid",
      "title": "Session title",
      "document_id": "uuid",
      "created_at": "2026-05-12T10:00:00Z"
    }
  ]
}
```

### Health Check
```
GET /health (no prefix, no auth required)

Response 200:
{
  "status": "healthy",
  "app": "MediaMind AI",
  "version": "1.0.0"
}
```

---

## Frontend Guide

### Authentication Flow

1. User visits app → redirected to `/login` if not authenticated
2. Clicks **"Continue with Google"**
3. Redirected to Google login page
4. After login, Google redirects to backend callback
5. Backend creates/finds user, generates JWT token
6. Redirected to `http://localhost:3000/auth/callback?token=eyJ...`
7. Frontend saves token to localStorage
8. User avatar and name appear in navbar
9. Token included automatically in all API requests via axios interceptor

### Pages

**Login (`/login`)** — Google OAuth login page with feature highlights.

**Home (`/`)** — Upload page with drag & drop zone. Supports PDF, MP3, MP4, WAV, M4A, AVI, MOV, MKV files up to 50MB. Shows upload progress and polls for processing completion every 3 seconds.

**Library (`/library`)** — Grid view of all uploaded documents with file type icons, processing status badges, and quick actions (view, delete). Only shows documents belonging to the logged-in user.

**Document View (`/document/:id`)** — Split panel layout:
- Left panel: Document info, AI summary with key points, media player for audio/video
- Right panel: Chat interface with real-time streaming responses, confidence scores, and timestamp cards

### Key Interactions

**Uploading a File:**
1. Drag & drop or click to select file
2. Upload progress bar appears
3. Status polls from `pending` → `processing` → `completed`
4. Redirects to document view when ready

**Asking a Question (Streaming):**
1. Type question in chat input
2. Words appear one by one in real time as Gemini generates them
3. Blinking `|` cursor shows while streaming is active
4. Cursor disappears and confidence score appears when done
5. For audio/video: timestamp cards appear below the completed answer
6. Click **▶ Play** on timestamp card to seek media player to that moment

**Semantic Search:**
1. Type in navbar search bar (min 3 characters)
2. Dropdown shows matching documents with similarity scores
3. Click result to open that document's chat page

**Logout:**
- Click logout button in navbar
- Token deleted from localStorage
- Redirected to login page

### Streaming Implementation

The frontend uses the native `fetch` API with `ReadableStream` and manually adds the JWT token:

```javascript
const token    = localStorage.getItem('mediamind_token')
const response = await fetch('http://localhost:8000/api/v1/chat/stream', {
  method : 'POST',
  headers: {
    'Content-Type' : 'application/json',
    'Authorization': `Bearer ${token}`
  },
  body: JSON.stringify({ document_id, question, session_id })
})
const reader = response.body.getReader()
// Reads token events and appends words to message bubble in real time
```

An `AbortController` cancels the stream cleanly if the user navigates away mid-answer.

### Running the Frontend Locally

```bash
cd frontend/frontend
npm install
npm run dev
```

Frontend runs at: http://localhost:5173 (development) or http://localhost:3000 (Docker)

---

## Testing

### Run All Tests

```bash
docker exec mediamind_backend pytest app/tests/
```

### Run with Coverage Report

```bash
docker exec mediamind_backend pytest app/tests/ --cov=app --cov-report=term-missing
```

### Run Specific Test File

```bash
docker exec mediamind_backend pytest app/tests/test_upload.py -v
```

### Test Results

- **123 tests** across 9 test files
- **97% code coverage** (above the 95% requirement)
- All tests use isolated SQLite databases — no real PostgreSQL needed for testing
- External services (Gemini, Whisper, Google OAuth) are mocked in all tests
- Streaming methods tested with async generators
- Auth tests use a separate unauthenticated client to test real auth behavior

### Test Files

| File | What it tests |
|---|---|
| `test_upload.py` | File upload, listing, retrieval, deletion, serving, search |
| `test_chat.py` | Q&A, summarization, chat sessions, history |
| `test_auth.py` | Google OAuth flow, JWT creation/verification, user endpoints |
| `test_gemini_service.py` | LLM responses, JSON parsing, timestamps, streaming |
| `test_whisper_service.py` | Transcription, timestamp search, save/load |
| `test_pdf_service.py` | PDF text extraction, validation, page count |
| `test_vector_service.py` | Embeddings, chunking, similarity search |
| `test_models.py` | Database models, enums, settings |
| `test_process_document.py` | Background processing task |

---

## CI/CD Pipeline

GitHub Actions automatically runs on every push and pull request to `main`/`master`.

### Pipeline Steps

1. **Checkout** — Clone the repository
2. **Setup Python 3.11** — Install Python environment
3. **Install system dependencies** — ffmpeg, libmagic (required for Whisper and file detection)
4. **Install Python dependencies** — faster-whisper + requirements.txt
5. **Run tests** — pytest with 95% coverage requirement
6. **Build Docker image** — Verify Dockerfile builds successfully

### Secrets Required

Add these secrets in GitHub repo settings → Secrets → Actions:

| Secret | Value |
|---|---|
| `GEMINI_API_KEY` | Your Google Gemini API key |
| `GOOGLE_CLIENT_ID` | Your Google OAuth client ID |
| `GOOGLE_CLIENT_SECRET` | Your Google OAuth client secret |
| `SECRET_KEY` | Your JWT signing secret |

---

## Docker Configuration

### docker-compose.yml Services

**`db`** — PostgreSQL 16 with pgvector extension
- Image: `pgvector/pgvector:pg16`
- Port: `5432`
- Volume: `postgres_data` (persistent)
- Health check: `pg_isready` every 5 seconds

**`backend`** — FastAPI application
- Built from `./backend/Dockerfile`
- Port: `8000`
- Depends on `db` (waits for healthy status)
- Volume: `./backend:/app` (live reload in development)
- Restarts on failure

### Backend Dockerfile

```
python:3.11-slim base image
→ Install system deps (ffmpeg, libmagic, gcc, git)
→ Upgrade pip + setuptools
→ Install faster-whisper separately (build isolation fix)
→ Install requirements.txt
→ Copy application code
→ Expose port 8000
→ Run uvicorn
```

### Data Persistence

| Data | Storage |
|---|---|
| Database | Docker volume `mediamindai_postgres_data` |
| Uploaded files | Docker volume `mediamindai_uploads_data` |
| Whisper model | Downloaded on first transcription, cached in container |

---

## Architecture Overview

```
User Browser
     │
     ├──► Regular HTTP/REST (axios + JWT token)
     │
     └──► SSE Streaming (fetch + ReadableStream + JWT token) ⚡
          │
          ▼
React Frontend (Port 3000)
          │
          ▼
FastAPI Backend (Port 8000)
     │
     ├──► Auth Service (Google OAuth + JWT)
     │         └── Google OAuth flow
     │         └── JWT token creation/verification
     │         └── User management
     │
     ├──► PDF Service (pdfplumber/PyPDF2)
     │         └── Extracts text from PDFs
     │
     ├──► Whisper Service (faster-whisper)
     │         └── Transcribes audio/video locally
     │
     ├──► Vector Service (sentence-transformers)
     │         └── Creates embeddings, chunks text
     │         └── Semantic search via pgvector
     │
     ├──► Gemini Service (LangChain + Google Gemini)
     │         └── Answers questions (regular + streaming)
     │         └── Generates summaries
     │         └── Finds relevant timestamps
     │         └── Streams word-by-word via async generator ⚡
     │
     └──► PostgreSQL + pgvector (Port 5432)
               └── Users table (Google OAuth users)
               └── Documents table (text, embeddings, metadata, user_id)
               └── ChatSessions table (user_id)
               └── ChatMessages table (with timestamps JSON)
```

### Request Flow — Authentication

```
1. User clicks "Login with Google"
2. Frontend redirects to GET /api/v1/auth/login
3. Backend redirects to Google OAuth page
4. User logs in with Google
5. Google redirects to GET /api/v1/auth/callback?code=...
6. Backend exchanges code for Google user info
7. Backend creates/updates user in DB
8. Backend generates JWT token
9. Backend redirects to http://localhost:3000/auth/callback?token=eyJ...
10. Frontend saves token to localStorage
11. All subsequent requests include: Authorization: Bearer eyJ...
```

### Request Flow — File Upload

```
1. User uploads file → POST /api/v1/upload (with JWT token)
2. Backend verifies token → identifies user
3. File saved to disk → UUID filename generated
4. Document record created with user_id in DB (status: pending)
5. Response returned immediately to user
6. Background task starts:
   - PDF: extract text → store embedding
   - Audio/Video: whisper transcribe → save JSON → store embedding
7. Document status updated to completed
8. Frontend polls GET /documents/{id} every 3s until completed
```

### Request Flow — Streaming Answer ⚡

```
1. User asks question → POST /api/v1/chat/stream (with JWT token)
2. Backend verifies token → identifies user
3. Document fetched — verified to belong to this user
4. Vector service finds relevant text chunks
5. FastAPI opens SSE connection to frontend
6. Gemini starts generating → words yielded one by one (40ms delay)
7. Each word sent as SSE event: data: {"type": "token", "content": "word "}
8. Frontend appends each word to message bubble in real time
9. Blinking cursor shows while streaming active
10. done event fires → full answer saved to DB → cursor disappears
```

---

## Bonus Features Implemented

| Bonus | Status | Implementation |
|---|---|---|
| Vector search (FAISS/Pinecone) | ✅ | pgvector with sentence-transformers embeddings |
| Real-time streaming responses | ✅ | SSE word-by-word streaming via async generator |
| Multi-user authentication | ✅ | Google OAuth 2.0 + JWT tokens + per-user data isolation |
| Rate limiting + Redis | ❌ | Not implemented |

---

## Supported File Types

| Type | Extensions | Processing |
|---|---|---|
| PDF | `.pdf` | Text extraction via pdfplumber/PyPDF2 |
| Audio | `.mp3`, `.wav`, `.m4a` | Whisper transcription + timestamps |
| Video | `.mp4`, `.avi`, `.mov`, `.mkv` | Whisper transcription + timestamps |

Maximum file size: **50MB**

---

## Known Limitations

- Whisper model downloads on first use (~150MB for `base` model)
- Gemini free tier has rate limits (20 requests/day on free tier)
- Large files (>10min audio) may take several minutes to transcribe
- Vector embeddings use 384-dimension model padded to 1536 for pgvector compatibility
- Google OAuth redirect URI must exactly match what's configured in Google Cloud Console

---

## License

MIT License — feel free to use, modify, and distribute.

---

## Author

**Fuzail Rehman**
- GitHub: [@fuzail-pixel](https://github.com/fuzail-pixel)
- LinkedIn: [fuzail-rehman](https://linkedin.com/in/fuzail-rehman-31a755241)
