# MediaMind AI — Frontend

React + Vite frontend for the MediaMind AI document Q&A application.

## Quick Start (Development)

```bash
cd frontend
npm install
npm run dev
# → http://localhost:3000
```

Make sure the backend is running on `http://localhost:8000`.

## Environment Variables

Create `frontend/.env.local` to override defaults:

```
VITE_API_URL=http://localhost:8000/api/v1
```

## Docker (Production)

Add the frontend service to your `docker-compose.yml` (see `docker-compose.frontend.yml` for the snippet), then:

```bash
docker compose up --build
```

## Project Structure

```
src/
├── components/
│   ├── Chat/         ChatWindow, ChatMessage, ChatInput, TimestampCard
│   ├── Document/     DocumentCard, DocumentList, SummaryPanel
│   ├── Layout/       Navbar (with search), Sidebar
│   ├── Player/       MediaPlayer (with seekTo)
│   └── Upload/       UploadZone, UploadProgress
├── pages/
│   ├── Home.jsx      Upload page
│   ├── Library.jsx   All documents
│   └── DocumentView.jsx  Left panel (info/summary/player) + Right panel (chat)
└── services/
    └── api.js        All Axios API calls
```

## Notes

- **Media file serving**: `DocumentView` builds a media URL at `/api/v1/documents/{id}/file`. Adjust this in `DocumentView.jsx` if your backend exposes files at a different route.
- **Session continuity**: `session_id` is stored in component state and passed with every follow-up question.
- **Status polling**: After upload, the app polls `GET /documents/{id}` every 3 seconds until status is `completed` or `failed`.
