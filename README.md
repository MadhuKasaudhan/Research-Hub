# ResearchHub AI

Intelligent Research Paper Management and Analysis System powered by Agentic AI.

Upload, discover, analyze, and converse with academic papers using autonomous AI agents backed by Groq's Llama 3.3 70B model, vector embeddings for semantic search, and persistent conversational context across sessions.

## Tech Stack

| Layer | Technologies |
|-------|-------------|
| Frontend | React 18, TypeScript, Vite, TailwindCSS, Zustand, React Query |
| Backend | FastAPI (Python 3.12), async SQLAlchemy, Pydantic |
| LLM | Groq API (llama-3.3-70b-versatile) |
| Vector DB | ChromaDB (local, default embeddings) |
| Database | SQLite via aiosqlite |
| Auth | JWT (access + refresh tokens, bcrypt) |
| File Storage | Local filesystem (UUID-based naming) |

## Architecture

```
researchhub-ai/
  backend/
    app/
      agents/          # AI agent layer (research, analysis, synthesis)
      models/          # SQLAlchemy ORM models
      routers/         # FastAPI route handlers
      schemas/         # Pydantic request/response schemas
      services/        # Business logic (auth, papers, embeddings, processing)
      utils/           # Dependencies, exception handlers
      config.py        # pydantic-settings configuration
      database.py      # Async engine + session factory
      main.py          # FastAPI app entry point
  frontend/
    src/
      components/      # Reusable UI components
      components/ui/   # Primitives (Button, Input, Card, Badge, Spinner, etc.)
      hooks/           # Custom React hooks (useChat, usePolling)
      pages/           # Route-level page components
      services/        # Axios API clients
      store/           # Zustand state stores
      types/           # TypeScript interfaces
```

## AI Agent System

The platform uses a 3-agent architecture:

- **ResearchAgent** - RAG-powered conversational agent. Retrieves relevant paper chunks via ChromaDB semantic search, builds context, and generates informed responses with source citations.
- **AnalysisAgent** - Deep single-paper analysis. Supports 5 analysis types: summary, key_findings, methodology, critique, and concepts.
- **SynthesisAgent** - Cross-paper synthesis. Supports 4 synthesis types: compare, themes, timeline, and gaps. Requires 2+ papers.

All agents use Groq's Llama 3.3 70B with 3-retry logic and meaningful fallbacks.

## Quick Start

### Prerequisites

- Python 3.12+
- Node.js 18+
- A Groq API key (console.groq.com)

### 1. Clone and configure

```bash
git clone <repo-url> && cd researchhub-ai
cp backend/.env.example backend/.env
# Edit backend/.env and set GROQ_API_KEY and SECRET_KEY
```

### 2. Backend setup

```bash
cd backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

Backend runs at http://localhost:8000. Health check: GET /health.

### 3. Frontend setup

```bash
cd frontend
npm install
npm run dev
```

Frontend runs at http://localhost:5173.

## API Reference

### Authentication

- `POST /api/v1/auth/register` - Create account
- `POST /api/v1/auth/login` - Get tokens
- `POST /api/v1/auth/refresh` - Refresh access token
- `GET /api/v1/auth/me` - Get profile
- `PUT /api/v1/auth/me` - Update profile

### Workspaces

- `GET /api/v1/workspaces` - List workspaces
- `POST /api/v1/workspaces` - Create workspace
- `GET /api/v1/workspaces/:id` - Get workspace
- `PUT /api/v1/workspaces/:id` - Update workspace
- `DELETE /api/v1/workspaces/:id` - Delete workspace
- `GET /api/v1/workspaces/:id/stats` - Get workspace stats

### Papers

- `GET /api/v1/workspaces/:id/papers` - List papers
- `POST /api/v1/workspaces/:id/papers/upload` - Upload paper
- `GET /api/v1/papers/:id` - Get paper
- `PUT /api/v1/papers/:id` - Update paper metadata
- `DELETE /api/v1/papers/:id` - Delete paper
- `GET /api/v1/papers/:id/status` - Processing status
- `GET /api/v1/papers/:id/chunks` - Get text chunks

### Chat

- `POST /api/v1/workspaces/:id/conversations` - Create conversation
- `GET /api/v1/workspaces/:id/conversations` - List conversations
- `GET /api/v1/conversations/:id` - Get conversation with messages
- `DELETE /api/v1/conversations/:id` - Delete conversation
- `POST /api/v1/conversations/:id/messages` - Send message and get AI response

### Analysis and Synthesis

- `POST /api/v1/papers/:id/analyze` - AI paper analysis
- `POST /api/v1/workspaces/:id/synthesize` - Cross-paper synthesis

### Search

- `GET /api/v1/workspaces/:id/search?q=` - Semantic search
- `GET /api/v1/workspaces/:id/search/papers?q=` - Metadata search

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `GROQ_API_KEY` | *(required)* | Groq API key for LLM access |
| `SECRET_KEY` | `dev-secret-key-change-me` | JWT signing secret |
| `DATABASE_URL` | `sqlite+aiosqlite:///./researchhub.db` | Async database connection string |
| `CHROMA_PERSIST_DIR` | `./chroma_db` | ChromaDB persistence directory |
| `UPLOAD_DIR` | `./uploads` | Uploaded file storage directory |
| `MAX_FILE_SIZE_MB` | `50` | Maximum upload file size in megabytes |
| `CORS_ORIGINS` | `http://localhost:5173` | Allowed CORS origins |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | `30` | Access token TTL in minutes |
| `REFRESH_TOKEN_EXPIRE_DAYS` | `7` | Refresh token TTL in days |

## Docker

```bash
docker-compose up --build
```

## License

MIT
