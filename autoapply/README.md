# AutoApply

> Open-source, self-hostable AI job application agent.

Upload your resume → get AI scoring + improvement suggestions → define job criteria → the tool finds matching jobs, tailors your resume and cover letter for each one, and either auto-applies or queues for human review.

**Everything runs locally via Docker Compose. No data leaves your infrastructure.**

---

## Quick Start

```bash
# 1. Clone
git clone https://github.com/JoeArmageddon/JobAppTool.git
cd JobAppTool/autoapply

# 2. Configure environment
cp .env.example .env
# Edit .env — at minimum set ANTHROPIC_API_KEY and Clerk keys

# 3. Launch
docker compose up -d

# 4. Run database migrations
docker compose exec backend alembic upgrade head

# 5. Open the dashboard
open http://localhost:3000
```

---

## Environment Variables

| Variable | Required | Description |
|---|---|---|
| `ANTHROPIC_API_KEY` | ✓ | Claude API key (get one at console.anthropic.com) |
| `NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY` | ✓ | Clerk publishable key |
| `CLERK_SECRET_KEY` | ✓ | Clerk secret key |
| `CLERK_WEBHOOK_SECRET` | ✓ | Clerk webhook secret |
| `POSTGRES_PASSWORD` | — | Postgres password (default: `autoapply_dev`) |
| `REDIS_URL` | — | Redis URL (default: `redis://redis:6379/0`) |
| `ENVIRONMENT` | — | `development` or `production` |
| `NEXT_PUBLIC_API_URL` | — | Backend URL seen by browser (default: `http://localhost:8000`) |

---

## Services

| Service | Port | Description |
|---|---|---|
| frontend | 3000 | Next.js dashboard |
| backend | 8000 | FastAPI REST API |
| postgres | 5432 | PostgreSQL database |
| redis | 6379 | Redis (Celery broker + result backend) |
| celery_worker | — | Background task processor |
| celery_beat | — | Periodic task scheduler (scrapes every 6h) |
| flower | 5555 | Celery task monitor |

---

## Features

- **AI Resume Scoring** — ATS, Impact, and Completeness scores with actionable suggestions
- **Multi-board Job Scraping** — LinkedIn, Indeed, Glassdoor, ZipRecruiter every 6 hours
- **AI Tailoring** — Gap analysis + keyword-matched rewrites (facts only, no hallucination)
- **Cover Letter Generation** — 3-paragraph, 280 words, specific to each company
- **Auto-Apply** — Playwright adapters for Greenhouse and Lever with stealth mode
- **Kanban Tracker** — Full application lifecycle with analytics
- **PDF Generation** — ATS-safe single-column PDF export via WeasyPrint
- **Hard Daily Limits** — You set the cap, the worker enforces it absolutely

---

## Resume Integrity

AutoApply's AI rewrites are constrained by your actual resume data. The system will **never**:
- Add skills not present in your original resume
- Invent job titles, companies, dates, or responsibilities
- Exaggerate or embellish achievements
- Add certifications or degrees not in the original

Every rewrite prompt includes this constraint verbatim. Your integrity is the product.

---

## Architecture

```
autoapply/
├── frontend/          # Next.js 14 + TypeScript + Tailwind + shadcn/ui
├── backend/
│   ├── main.py        # FastAPI app
│   ├── routers/       # REST endpoints
│   ├── services/      # AI, scraping, apply engine
│   ├── workers/       # Celery tasks
│   ├── models/        # SQLAlchemy ORM + Pydantic schemas
│   ├── db/            # Async database session
│   └── alembic/       # Database migrations
└── docker-compose.yml
```

---

## Tech Stack

| Layer | Choice |
|---|---|
| Frontend | Next.js 14, TypeScript, Tailwind CSS, shadcn/ui |
| Backend | Python 3.11, FastAPI, SQLAlchemy (async) |
| AI | Anthropic Claude API (`claude-sonnet-4-20250514`) |
| Resume Parsing | PyMuPDF, python-docx |
| Job Scraping | jobspy |
| Browser Automation | Playwright + playwright-stealth |
| Database | PostgreSQL + Alembic |
| Queue | Redis + Celery |
| Auth | Clerk |
| PDF Generation | WeasyPrint |
| Deployment | Docker Compose |

---

## Contributing

PRs welcome. Please open an issue first for large changes.

```bash
# Backend dev (hot reload)
docker compose up backend -d
docker compose logs -f backend

# Frontend dev
cd frontend && npm run dev

# Run migrations
docker compose exec backend alembic upgrade head

# Celery task monitor
open http://localhost:5555
```

---

## License

Apache 2.0 — see [LICENSE](LICENSE).
