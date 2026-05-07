# DocuMind AI

DocuMind AI is a full-stack web app for asking questions over PDFs,
audio, and video. It extracts searchable content, stores source metadata, answers with
retrieved context, and links media answers back to playable timestamps.

## Stack

- FastAPI backend
- React + Vite + TypeScript frontend
- Firebase Auth
- PostgreSQL + pgvector
- Gemini for chat, summaries, and embeddings
- Deepgram for audio/video transcription
- Docker Compose for local and EC2 deployment

## Local Setup

1. Copy env files:

```bash
cp .env.example .env
cp backend/.env.example backend/.env
cp frontend/.env.example frontend/.env
```

2. Add keys when available:

```bash
GEMINI_API_KEY=...
DEEPGRAM_API_KEY=...
```

Firebase frontend and service account values can stay blank during development because
`ALLOW_MOCK_AUTH=true` enables a local dev user.

3. Run the app:

```bash
docker compose up --build
```

4. Open:

- Frontend: http://localhost:5173
- Backend docs: http://localhost:8000/docs
- PostgreSQL from host tools: `localhost:5433`

## API Overview

- `GET /api/health`
- `POST /api/files` multipart upload field `upload`
- `GET /api/files`
- `GET /api/files/{file_id}/summary`
- `GET /api/files/{file_id}/content?token=...`
- `POST /api/chat`

## Testing

```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
DATABASE_URL=sqlite+pysqlite:///:memory: pytest
```

The CI target enforces 95% backend coverage.

## AWS EC2 Deployment Path

1. Launch an Ubuntu EC2 instance.
2. Install Docker and Docker Compose.
3. Clone the repository.
4. Create `.env` with production Gemini, Deepgram, and Firebase service account values.
5. Point frontend Firebase config at the same Firebase project.
6. Run `docker compose up -d --build`.
7. Put Nginx or an AWS load balancer in front of ports `5173` and `8000`, or adjust Compose
   to serve the frontend and proxy `/api` through one public domain.

## Demo Script

1. Sign in.
2. Upload a PDF and show the generated summary.
3. Ask a question and show page citations.
4. Upload an audio/video file.
5. Ask for a topic from the media.
6. Click Play on a timestamped source.
7. Briefly show Docker, tests, and CI workflow.
