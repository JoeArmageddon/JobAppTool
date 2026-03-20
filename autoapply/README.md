<div align="center">

<h1>⚡ AutoApply</h1>

<p><strong>The open-source AI agent that finds jobs, tailors your resume, and applies — on your own infrastructure.</strong></p>

<p>
  <a href="https://github.com/JoeArmageddon/JobAppTool/blob/main/LICENSE">
    <img src="https://img.shields.io/badge/license-Apache%202.0-blue.svg" alt="License" />
  </a>
  <img src="https://img.shields.io/badge/python-3.11-blue.svg" alt="Python 3.11" />
  <img src="https://img.shields.io/badge/Next.js-14-black.svg" alt="Next.js 14" />
  <img src="https://img.shields.io/badge/AI-Claude%20Sonnet-orange.svg" alt="Claude AI" />
  <img src="https://img.shields.io/badge/deploy-Docker%20Compose-2496ED.svg" alt="Docker" />
  <img src="https://img.shields.io/badge/status-production--ready-brightgreen.svg" alt="Status" />
</p>

<p>
  <a href="#-quick-start">Quick Start</a> ·
  <a href="#-features">Features</a> ·
  <a href="#-how-it-works">How It Works</a> ·
  <a href="#-configuration">Configuration</a> ·
  <a href="#-contributing">Contributing</a>
</p>

</div>

---

<div align="center">

### Upload resume → AI scores + improves it → Set job criteria → Agent finds jobs, tailors your resume for each, auto-applies or queues for your review.

### **Your data never leaves your machine.**

</div>

---

## 🆓 Free to Run — No Paid AI Required

AutoApply supports **two AI providers**. You can switch with a single environment variable.

| Provider | Cost | Quality | Setup |
|---|---|---|---|
| **Anthropic Claude** ⭐ recommended | Pay-per-token (~$0.003/resume) | Best — especially for structured JSON extraction | [console.anthropic.com](https://console.anthropic.com) |
| **Groq** (free tier) | Free up to rate limits | Great — Llama 3.3 70B performs well on all tasks | [console.groq.com](https://console.groq.com) |

**To use Groq (free):**
```bash
# In your .env file:
LLM_PROVIDER=groq
GROQ_API_KEY=gsk_...   # free at console.groq.com — no credit card needed
```

**To use Anthropic (recommended):**
```bash
LLM_PROVIDER=anthropic
ANTHROPIC_API_KEY=sk-ant-...
```

Groq's free tier gives you **14,400 requests/day** on Llama 3.3 70B — more than enough for personal use. Anthropic Claude produces marginally better structured JSON output, especially for complex resumes, which is why it's the default.

---

## Why AutoApply?

Modern job searching is broken. You manually rewrite your resume for every application, paste the same cover letter into dozens of forms, and lose track of where you applied. AutoApply automates the entire pipeline — without compromising your resume's integrity or your privacy.

| Problem | AutoApply's answer |
|---|---|
| Resume tailoring takes hours per application | AI rewrites in seconds — using only facts you've already stated |
| Cover letters feel generic | Per-company letters citing the actual JD, max 280 words |
| Job boards are fragmented | Scrapes LinkedIn, Indeed, Glassdoor, ZipRecruiter every 6 hours |
| Applied-to trackers are tedious | Kanban board auto-updated by the apply agent |
| Sending data to SaaS tools is risky | 100% self-hosted via Docker Compose — zero telemetry |
| AI might hallucinate skills you don't have | Hard-coded constraint: agent **cannot** invent, exaggerate, or embellish |

---

## ✨ Features

### 🧠 AI Resume Intelligence
- **ATS Score** — how well your resume will pass applicant tracking systems
- **Impact Score** — strength of your achievement language and metrics
- **Completeness Score** — identifies missing sections that cost you interviews
- **Actionable suggestions** — specific, prioritized fixes for every issue found
- **Gap analysis** — exact keyword matches, synonym matches, and missing skills per job

### 🔍 Automated Job Discovery
- Scrapes **LinkedIn, Indeed, Glassdoor, ZipRecruiter** every 6 hours
- Claude parses each JD into structured data for accurate matching
- Match score (0–100) with reasons — filter your feed to only what matters
- Blacklist companies you'll never apply to

### ✍️ Per-Application AI Tailoring
- **Resume rewrite** — reorders sections, incorporates JD keywords naturally, strengthens impact language where numbers already exist
- **Cover letter** — 3 paragraphs, named company, 2–3 mapped achievements, forward-looking closer
- **Integrity constraint** (non-negotiable): the AI cannot add skills, titles, dates, certifications, or achievements not already in your resume

### 🤖 Auto-Apply Engine
Playwright-based adapters for the most common ATS platforms:

| ATS | Status | Notes |
|---|---|---|
| LinkedIn Easy Apply | ✅ Supported | Requires LinkedIn credentials + persistent session |
| Greenhouse | ✅ Supported | |
| Lever | ✅ Supported | |
| Workday | ✅ Supported | Multi-step wizard, assessment detection |
| iCIMS | ✅ Supported | Multi-page form |
| Indeed Easy Apply | 🔜 Roadmap | |

- `playwright-stealth` on every browser session
- Human-like typing delays (40–120ms per keystroke)
- Random pauses between actions (500ms–2500ms)
- Screenshot stored on every successful submission
- Returns `success` / `failed` / `requires_human` — never silently fails
- LinkedIn session cookies are **persisted to disk** — logs in once, reuses the session

### 📋 Application Kanban
Full lifecycle tracking with 7 columns: **Queued → Tailoring → Ready → Applied → Interview → Offer → Rejected**

### 📄 ATS-Safe PDF Export
Single-column, no graphics, WeasyPrint-rendered PDF — optimized to pass ATS parsers.

### 🔒 Hard Daily Limits
You set the cap (e.g. 10 applications/day). The Celery worker enforces it absolutely — the queue pauses, you get notified, nothing silently overflows.

---

## 🚀 Quick Start

**Prerequisites:** Docker + Docker Compose, an [Anthropic API key](https://console.anthropic.com), a [Clerk account](https://clerk.com) (free tier works).

```bash
# 1. Clone
git clone https://github.com/JoeArmageddon/JobAppTool.git
cd JobAppTool/autoapply

# 2. Configure
cp .env.example .env
# Open .env and fill in your AI provider (pick one):
#
#   Option A — Anthropic Claude (recommended, pay-per-token):
#     ANTHROPIC_API_KEY=sk-ant-...
#
#   Option B — Groq (free tier, no credit card):
#     LLM_PROVIDER=groq
#     GROQ_API_KEY=gsk_...
#
# Plus Clerk auth keys:
#   NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY=pk_live_...
#   CLERK_SECRET_KEY=sk_live_...
#   CLERK_WEBHOOK_SECRET=whsec_...

# 3. Launch
docker compose up -d

# 4. Run migrations (first time only)
docker compose exec backend alembic upgrade head

# 5. Open the dashboard
open http://localhost:3000
```

That's it. The scraper will run its first pass within 6 hours, or you can trigger it manually:

```bash
docker compose exec celery_worker celery -A celery_app call workers.scrape_worker.scrape_jobs_for_all_profiles
```

---

## 🏗 How It Works

```
┌─────────────────────────────────────────────────────────────────────┐
│                          Your Browser                               │
│                    http://localhost:3000                             │
└───────────────────────────┬─────────────────────────────────────────┘
                            │ HTTPS
                ┌───────────▼───────────┐
                │   Next.js 14 Frontend  │
                │  TypeScript + Tailwind │
                │   Clerk Auth (v6)      │
                └───────────┬───────────┘
                            │ REST /api/v1/*
                ┌───────────▼───────────┐
                │   FastAPI Backend      │
                │   Python 3.11 async    │
                │   Clerk JWT Middleware │
                └──┬────────────────┬───┘
                   │                │
       ┌───────────▼──┐   ┌────────▼────────────┐
       │  PostgreSQL   │   │   Redis             │
       │  (all data)   │   │   (Celery broker)   │
       └───────────────┘   └────────┬────────────┘
                                    │
                    ┌───────────────▼───────────────┐
                    │        Celery Workers          │
                    │  ┌─────────────────────────┐  │
                    │  │  scrape_worker (6h Beat) │  │
                    │  │  → jobspy → Claude JD    │  │
                    │  │  → match scorer          │  │
                    │  └─────────────────────────┘  │
                    │  ┌─────────────────────────┐  │
                    │  │  apply_worker           │  │
                    │  │  → tailor resume        │  │
                    │  │  → generate cover letter │  │
                    │  │  → Playwright ATS adapter│  │
                    │  └─────────────────────────┘  │
                    └───────────────────────────────┘
                                    │
               ┌────────────────────▼───────────────────┐
               │           Anthropic Claude API          │
               │  • Resume parse  • Resume score         │
               │  • Gap analysis  • Resume rewrite       │
               │  • Cover letter  • JD structured parse  │
               └────────────────────────────────────────┘
```

### The Application Pipeline

```
1. You upload your resume (PDF or DOCX)
        ↓
2. Claude extracts structured JSON — name, skills, experience, education
        ↓
3. Claude scores ATS / Impact / Completeness (0-100 each)
        ↓
4. You configure your hunt profile — titles, locations, salary floor, blacklist
        ↓
5. Celery scrapes jobs every 6h → Claude scores each against your resume
        ↓
6. You review your job feed (filtered by match score)
        ↓
7. For each job: Claude runs gap analysis → rewrites resume → generates cover letter
        ↓
8. You review the tailored materials (or set to auto-approve)
        ↓
9. Playwright adapter fills + submits the ATS form
        ↓
10. Application status auto-updated in Kanban → screenshot stored as proof
```

---

## ⚠️ Resume Integrity — Non-Negotiable

This is the most important constraint in the entire system.

Every resume rewrite prompt contains this hard constraint:

> *"You MUST use ONLY facts present in the original resume. Never invent, never exaggerate, never hallucinate. Do NOT add skills not in the original. Do NOT invent job titles, companies, dates, or responsibilities. Do NOT add certifications or degrees not explicitly stated."*

The AI **may** reorder sections, reframe bullets using JD language, and strengthen impact language where numbers already exist. It may not fabricate anything.

This is enforced in code and verified in the test suite. Violation is a product failure.

---

## 🔧 Configuration

### AI Provider (pick one)

| Variable | Description |
|---|---|
| `LLM_PROVIDER` | `anthropic` (default, recommended) or `groq` (free) |
| `ANTHROPIC_API_KEY` | Required when `LLM_PROVIDER=anthropic` — [console.anthropic.com](https://console.anthropic.com) |
| `GROQ_API_KEY` | Required when `LLM_PROVIDER=groq` — free at [console.groq.com](https://console.groq.com) |
| `ANTHROPIC_MODEL` | Optional override — default: `claude-sonnet-4-20250514` |
| `GROQ_MODEL` | Optional override — default: `llama-3.3-70b-versatile` |

### Auth (required)

| Variable | Description |
|---|---|
| `NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY` | Clerk dashboard → API Keys |
| `CLERK_SECRET_KEY` | Clerk dashboard → API Keys |
| `CLERK_WEBHOOK_SECRET` | Clerk dashboard → Webhooks → your endpoint secret |

### Optional Variables

| Variable | Default | Description |
|---|---|---|
| `POSTGRES_PASSWORD` | `autoapply_dev` | Database password |
| `REDIS_URL` | `redis://redis:6379/0` | Redis connection string |
| `NEXT_PUBLIC_API_URL` | `http://localhost:8000` | Backend URL seen by the browser |
| `ENVIRONMENT` | `development` | `development` or `production` |
| `UPLOADS_DIR` | `/app/uploads` | Where resume files and screenshots are stored |

### LinkedIn Easy Apply Setup

LinkedIn Easy Apply requires an authenticated LinkedIn session.

```bash
# In your .env file:
LINKEDIN_EMAIL=your@email.com
LINKEDIN_PASSWORD=your-linkedin-password
```

**How it works:**
1. On the first Easy Apply run, the adapter logs in to LinkedIn using your credentials
2. Session cookies are saved to `uploads/linkedin_browser/` (inside the Docker volume)
3. Every subsequent run reuses the saved session — no re-login until the session expires

**Important notes:**
- Use a real LinkedIn account — Easy Apply requires profile data (headshot, connections, etc.)
- LinkedIn detects unusual activity. Keep your daily apply limit low (5–15/day) and the adapter already uses human-like delays
- If LinkedIn triggers a CAPTCHA or security challenge during login, the adapter returns `requires_human` — complete the challenge manually in a browser, then copy the session cookies
- LinkedIn's ToS prohibits automation. Use this tool responsibly and at your own risk

### Clerk Setup

1. Create a free account at [clerk.com](https://clerk.com)
2. Create an application — enable Email/Password sign-in
3. Copy `NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY` and `CLERK_SECRET_KEY` from API Keys
4. Add a webhook pointing to `http://your-domain/api/v1/webhooks/clerk` with the `user.created` event
5. Copy the webhook signing secret to `CLERK_WEBHOOK_SECRET`

---

## 🏛 Architecture

```
autoapply/
├── frontend/
│   ├── app/
│   │   ├── page.tsx                    # Public landing page
│   │   ├── (clerk)/                    # Auth-gated route group
│   │   │   ├── layout.tsx              # ClerkProvider lives here
│   │   │   ├── (auth)/sign-in/
│   │   │   ├── (auth)/sign-up/
│   │   │   └── dashboard/
│   │   │       ├── resume/             # Upload + scoring
│   │   │       ├── hunt-profile/       # 7-step preferences wizard
│   │   │       ├── jobs/               # Filterable job feed
│   │   │       ├── applications/       # Kanban tracker
│   │   │       └── settings/
│   ├── components/
│   │   ├── resume/ScoreRing.tsx        # Animated SVG ring charts
│   │   ├── jobs/JobCard.tsx            # Match score + tailor button
│   │   └── applications/KanbanBoard.tsx
│   └── lib/
│       ├── api.ts                      # All fetch calls centralized
│       └── types.ts                    # TypeScript types mirroring backend
│
├── backend/
│   ├── routers/                        # FastAPI route handlers
│   ├── services/
│   │   ├── resume_parser.py            # PyMuPDF + python-docx
│   │   ├── resume_scorer.py            # Claude ATS/Impact/Completeness
│   │   ├── resume_tailor.py            # Gap analysis + rewrite
│   │   ├── cover_letter.py             # Per-company cover letters
│   │   ├── job_scraper.py              # jobspy + Claude JD parser
│   │   ├── apply_engine.py             # Playwright ATS dispatcher
│   │   ├── pdf_generator.py            # WeasyPrint PDF export
│   │   └── adapters/
│   │       ├── greenhouse.py
│   │       ├── lever.py
│   │       ├── workday.py
│   │       └── icims.py
│   ├── workers/
│   │   ├── scrape_worker.py            # Runs every 6h via Celery Beat
│   │   └── apply_worker.py             # Processes queue, enforces daily limit
│   ├── models/
│   │   ├── orm.py                      # SQLAlchemy ORM
│   │   └── schemas.py                  # Pydantic v2 schemas
│   ├── middleware/auth.py              # Clerk JWT validation
│   ├── tests/                          # pytest integration suite
│   └── alembic/                        # Database migrations
│
└── docker-compose.yml
```

### Services at a Glance

| Service | Port | Purpose |
|---|---|---|
| `frontend` | 3000 | Next.js dashboard |
| `backend` | 8000 | FastAPI REST API |
| `postgres` | 5432 | Primary database |
| `redis` | 6379 | Celery broker + result store |
| `celery_worker` | — | Background task processor |
| `celery_beat` | — | Periodic scheduler (6h scrape) |
| `flower` | 5555 | Celery task monitor UI |

---

## 🧑‍💻 Development

```bash
# Watch backend logs
docker compose logs -f backend

# Watch worker logs
docker compose logs -f celery_worker

# Frontend hot reload (outside Docker)
cd frontend
npm install
cp .env.example .env.local   # fill Clerk keys
npm run dev                  # http://localhost:3000

# Run backend tests
docker compose exec backend pytest tests/ -v

# Run a specific test
docker compose exec backend pytest tests/test_resume_tailor.py -v

# Create a new migration
docker compose exec backend alembic revision --autogenerate -m "describe_change"
docker compose exec backend alembic upgrade head

# Monitor Celery tasks
open http://localhost:5555

# Manually trigger a job scrape
docker compose exec celery_worker celery -A celery_app call workers.scrape_worker.scrape_jobs_for_all_profiles
```

### Tech Stack

| Layer | Technology |
|---|---|
| Frontend | Next.js 14 (App Router), TypeScript, Tailwind CSS, shadcn/ui |
| Backend | Python 3.11, FastAPI, SQLAlchemy 2.0 (async), Pydantic v2 |
| AI Engine | Anthropic Claude (`claude-sonnet-4-20250514`) |
| Resume Parsing | PyMuPDF, python-docx |
| Job Scraping | python-jobspy |
| Browser Automation | Playwright, playwright-stealth |
| Database | PostgreSQL + Alembic |
| Queue | Redis + Celery + Celery Beat |
| Auth | Clerk v6 |
| PDF | WeasyPrint + Jinja2 |
| Deployment | Docker Compose |

---

## 🗺 Roadmap

- [ ] **Indeed Easy Apply adapter** — the highest-volume source after LinkedIn
- [ ] **Email notifications** — alert on new high-match jobs, interview requests
- [ ] **Resume versioning** — keep multiple resume variants, A/B test match scores
- [ ] **Analytics dashboard** — response rate by company size, role type, match score
- [ ] **Multi-user / team mode** — shared job board, individual applications
- [ ] **Chrome extension** — one-click apply on any job posting page
- [ ] **Supabase hosted option** — for users who can't self-host

---

## 🤝 Contributing

PRs are welcome. For large changes, please open an issue first to discuss the approach.

1. Fork the repo
2. Create a feature branch: `git checkout -b feature/your-feature`
3. Make your changes with tests
4. Run `pytest tests/ -v` and `npm run build` (both must pass)
5. Submit a PR with a clear description of what and why

### Areas that need help
- More ATS adapters (Workday edge cases, Taleo, Bamboo HR, SmartRecruiters)
- Better resume scoring prompts
- UI/UX improvements (especially the hunt profile wizard)
- End-to-end test coverage

---

## 🔒 Privacy & Security

- **No telemetry.** Zero analytics, tracking, or data collection.
- **Your resume data stays in your Postgres instance.** The only external calls are to the Anthropic API (for AI) and Clerk (for auth). Both can be replaced — Clerk with your own JWT, Anthropic with any OpenAI-compatible endpoint.
- **Resume files stored locally** with user-scoped paths — no predictable URLs.
- **Clerk JWT validated on every API call** — users can only access their own data, enforced at the query level.
- **Rate limiting on all scraper calls** with exponential backoff.
- **Input validation** on all file uploads (MIME type + 10MB size limit).

---

## 📄 License

Apache 2.0 — see [LICENSE](LICENSE).

Free to use, fork, modify, and self-host. If you build something useful on top of this, a mention or a star is appreciated.

---

<div align="center">

**Built with [Claude](https://anthropic.com) · Deployed with Docker · No VC funding, no tracking, no BS**

<br/>

If this saved you time, ⭐ the repo — it helps others find it.

</div>
