# CLAUDE.md — AutoApply

> Read this fully before every session. This is the single source of truth.
> Never ask Kshitij to re-explain anything covered here.

---

## What This Is

**AutoApply** — open-source, self-hostable AI job application agent.

Users upload a resume → get AI scoring + improvement suggestions → define job
criteria → the tool finds matching jobs, tailors the resume and cover letter
for each one, and either auto-applies or queues for human review.

Everything runs locally via Docker Compose. No user data leaves their own
infrastructure in self-hosted mode. That privacy guarantee is a core product
promise — never compromise it.

**GitHub:** open-source project. Write code as if strangers will read it.
Clean commits, meaningful names, no TODOs left in production paths.

---

## ⚠️ RESUME INTEGRITY — NON-NEGOTIABLE

This is the single most important constraint in the entire project.

**Claude must NEVER:**
- Add skills not present in the original resume
- Invent job titles, companies, dates, or responsibilities
- Exaggerate or embellish any achievement
- Add certifications, degrees, or credentials not explicitly stated
- Infer experience from context and present it as fact

**Every resume rewrite prompt must include this constraint verbatim.**
If you are writing or modifying `resume_tailor.py` or any prompt that touches
resume content, stop and re-read this section first.

Violation of this constraint is not a bug — it is a product failure that
could cause real harm to real users.

---

## Tech Stack

| Layer | Choice |
|---|---|
| Frontend | Next.js 14 (App Router) + TypeScript + Tailwind CSS + shadcn/ui |
| Backend | Python 3.11 + FastAPI |
| AI Engine | Anthropic Claude API (`claude-sonnet-4-20250514`) |
| Resume Parsing | PyMuPDF (`fitz`) + python-docx |
| Job Scraping | `jobspy` (PyPI) |
| Browser Automation | Playwright (Python) + playwright-stealth |
| Database | PostgreSQL (Supabase or local Docker Postgres) |
| Queue | Redis + Celery |
| Auth | Clerk (Next.js) + API key validation on FastAPI |
| PDF Generation | WeasyPrint |
| Self-host | Docker Compose |

Do not suggest alternative libraries unless there is a hard technical blocker.
This stack is decided.

---

## Design System

```
Background:   #0a0a0f
Primary:      #6366f1  (indigo)
Success:      #10b981  (emerald) — applied, matched, offer states
Danger:       #f43f5e  (rose) — rejected, failed, error states
Warning:      #f59e0b  (amber) — review needed, queued states
Surface:      #12121a
Border:       rgba(99, 102, 241, 0.15)
Text primary: #f8fafc
Text muted:   #94a3b8
```

**Fonts:** Geist (display + body) + Geist Mono (data labels, scores, code,
terminal elements). Load via `next/font/google`.

**Style:** Dense information layout. Sidebar navigation. Subtle indigo glows
on interactive elements. Terminal aesthetic — this is a tool, not a marketing
site. Data should be readable at a glance.

**Components:** Use shadcn/ui for all primitives. Never build from scratch
what shadcn already covers. Extend with custom variants as needed.

---

## Project Structure

```
autoapply/
├── frontend/
│   ├── app/
│   │   ├── (auth)/sign-in/ sign-up/
│   │   ├── dashboard/
│   │   │   ├── page.tsx              # Overview + stats
│   │   │   ├── resume/               # Upload + scoring
│   │   │   ├── hunt-profile/         # Job preferences
│   │   │   ├── jobs/                 # Found jobs list
│   │   │   ├── applications/         # Kanban tracker
│   │   │   └── settings/
│   │   ├── layout.tsx
│   │   └── page.tsx                  # Landing page
│   ├── components/
│   │   ├── ui/                       # shadcn/ui only
│   │   ├── resume/
│   │   ├── jobs/
│   │   └── applications/
│   └── lib/
│       ├── api.ts                    # All fetch calls here
│       └── types.ts                  # Shared TypeScript types
│
├── backend/
│   ├── main.py                       # FastAPI app init
│   ├── routers/
│   │   ├── resume.py
│   │   ├── jobs.py
│   │   ├── applications.py
│   │   └── hunt_profile.py
│   ├── services/
│   │   ├── resume_parser.py
│   │   ├── resume_scorer.py
│   │   ├── resume_tailor.py          # ⚠️ Resume integrity rules apply
│   │   ├── cover_letter.py
│   │   ├── job_scraper.py
│   │   ├── job_matcher.py
│   │   ├── apply_engine.py
│   │   └── pdf_generator.py
│   ├── workers/
│   │   ├── scrape_worker.py          # Celery: runs every 6h
│   │   └── apply_worker.py           # Celery: respects daily limit
│   ├── models/schemas.py             # Pydantic v2 models
│   ├── db/database.py                # SQLAlchemy async
│   └── requirements.txt
│
├── docker-compose.yml
├── .env.example
├── CLAUDE.md                         # This file
└── README.md
```

---

## Code Conventions

### Python (Backend)

- **Pydantic v2** — use `model_validator`, `field_validator`. No v1 patterns.
- **FastAPI** — async everywhere (`async def`). No sync route handlers.
- **SQLAlchemy** — async sessions via `AsyncSession`. Never raw psycopg2.
- **Error handling** — every router endpoint wrapped in try/except.
  Return structured error responses: `{"error": "message", "code": "ERROR_CODE"}`
- **Claude API calls** — always use `try/except anthropic.APIError`.
  Log the full error, return a clean user-facing message.
- **Celery tasks** — always set `max_retries=3`, `default_retry_delay=60`.
  Log start, completion, and failure of every task.
- **Type hints** — mandatory on all function signatures.
- **No bare `except:`** — always catch specific exceptions.

### TypeScript (Frontend)

- **Strict mode** on. No `any` types. Ever.
- **API calls** — all in `lib/api.ts`. Components never call `fetch` directly.
- **Types** — all shared types in `lib/types.ts`. Mirror backend Pydantic schemas.
- **Server vs Client components** — default to Server Components.
  Add `'use client'` only when you need interactivity or browser APIs.
- **Error boundaries** — wrap all dashboard routes.
- **Loading states** — every async operation has a loading skeleton.
  Never show a blank panel while data loads.

### General

- **Never commit `.env`** — only `.env.example` with placeholder values
- **No console.log in production paths** — use proper logging
- **No hardcoded strings** — magic numbers and strings go in constants files
- **Every Claude API call** must specify `max_tokens` explicitly

---

## Database Schema

```sql
users (id, clerk_id, email, created_at)

resumes (
  id, user_id, raw_text, structured_json,
  ats_score, impact_score, completeness_score, overall_score,
  suggestions_json, file_url, created_at, updated_at
)

hunt_profiles (
  id, user_id, target_titles[], industries[], locations[],
  remote_preference, seniority_level, salary_floor,
  company_size_pref, blacklisted_companies[],
  job_sources[], is_active, daily_apply_limit, created_at
)

jobs (
  id, title, company, location, description_raw,
  description_parsed_json, source, source_url, source_job_id,
  salary_min, salary_max, posted_at, scraped_at,
  match_score, match_reasons_json, status
)

applications (
  id, user_id, job_id, resume_id,
  tailored_resume_text, tailored_resume_pdf_url,
  cover_letter_text, status,
  applied_at, response_at, notes
)
```

**Migration tool:** Alembic. Every schema change = a migration file.
Never alter tables manually in production.

---

## AI Prompt Patterns

### Resume Parser prompt
```
You are a resume parser. Extract into strict JSON:
{
  "name", "email", "phone", "location", "linkedin", "github",
  "summary", "skills": [],
  "experience": [{ "company", "title", "start_date", "end_date",
    "current", "responsibilities": [], "achievements": [] }],
  "education": [], "certifications": [], "languages": [], "projects": []
}
Return ONLY valid JSON. No commentary. No markdown fences.
```

### Resume Scorer prompt
Returns: `ats_score`, `impact_score`, `completeness_score`, `overall_score` (0–100 each)
+ `suggestions`: `[{ category, issue, fix }]`

### Resume Tailor — Step 1 (Gap Analysis)
Identify: skill gaps, exact keyword matches, synonym matches, suggested
reordering for relevance. Return JSON.

### Resume Tailor — Step 2 (Rewrite) ⚠️
```
CRITICAL CONSTRAINT: Use ONLY facts present in the original resume.
Never invent, never exaggerate, never hallucinate.
Do not add skills, experience, or credentials not in the original.

Rewrite to:
- Lead with most relevant experience for this role
- Incorporate exact JD keywords naturally
- Reframe bullets using JD language and priorities
- Strengthen impact language where numbers already exist

Return full rewritten resume as JSON matching original schema.
```

### Cover Letter prompt
3 paragraphs, max 280 words, professional, not sycophantic.
P1: Why this company + role (use company name + 1 JD detail).
P2: Top 2–3 matching achievements mapped to JD requirements.
P3: Forward-looking closer.

---

## Apply Engine Rules

**ATS adapters to build (in order):**
1. Greenhouse
2. Lever
3. Workday
4. iCIMS
5. Indeed Easy Apply

**Each adapter must return:** `success | failed | requires_human`

**Anti-detection (non-negotiable):**
- `playwright-stealth` on every browser instance
- Random delays 500ms–2500ms between all actions
- Screenshot confirmation stored on success
- Never exceed daily apply limit — hard-enforce in Celery worker

**If daily limit is hit:** stop the queue, log it, surface a notification
in the dashboard. Never silently skip or overflow.

---

## Celery Workers

- `scrape_worker` — runs every 6 hours via Celery Beat
- `apply_worker` — processes application queue, checks daily limit first

Both workers must:
1. Log task start with timestamp and user_id
2. Use exponential backoff on external API failures
3. Never crash silently — unhandled exceptions must be caught and logged
4. Store task result (success/failure/reason) in DB

---

## Docker Services

| Service | Port |
|---|---|
| frontend | 3000 |
| backend | 8000 |
| postgres | 5432 |
| redis | 6379 |
| celery_worker | — |
| flower (Celery monitor) | 5555 |

Health checks on all services. Backend waits for postgres and redis to be
healthy before starting. Document every env var in `.env.example`.

---

## Security Rules

- Clerk JWT validation on every protected Next.js route
- API key validation middleware on every FastAPI endpoint
- User can only access their own data — enforce at query level, not just route level
- Resume files stored with user-scoped paths — never predictable URLs
- Rate limiting on all scraper calls — exponential backoff
- Input validation on all file uploads (MIME type + size limit)
- No PII in logs

Run `snyk-fix` skill after completing any module that touches auth,
file uploads, or external API calls.

---

## Build Order

Work through this in sequence. Do not skip ahead. Check off as completed.

- [ ] **1. Docker Compose skeleton** — all services defined, health checks, `.env.example`
- [ ] **2. Postgres schema** — Alembic migrations for all 5 tables
- [ ] **3. FastAPI base** — app init, middleware, Clerk auth, error handling
- [ ] **4. Resume upload/parse/score** — endpoints + PyMuPDF + Claude parser + scorer
- [ ] **5. Next.js shell** — auth flow, dashboard layout, sidebar nav
- [ ] **6. Resume upload UI** — drag-drop upload, animated ring score charts
- [ ] **7. Hunt profile** — 7-step form frontend + backend endpoint
- [ ] **8. Job scraper** — jobspy integration + Claude JD parser + match scorer
- [ ] **9. Jobs listing UI** — filterable list, match score badges
- [ ] **10. AI tailoring engine** — gap analysis + resume rewrite + cover letter
- [ ] **11. Manual apply flow** — user reviews tailored resume + cover letter, approves
- [ ] **12. Application tracker** — Kanban UI (Queued → ... → Offer/Rejected)
- [ ] **13. Playwright ATS adapters** — Greenhouse first, then Lever
- [ ] **14. Celery workers** — auto-scrape + auto-apply queue
- [ ] **15. PDF generation** — WeasyPrint ATS-safe resume PDF
- [ ] **16. Landing page** — dark hero + animated terminal feed + `docker compose up` CTA
- [ ] **17. README + Docker docs** — self-hosting guide, env var reference

---

## Session Startup Checklist

At the start of every session, before writing any code:

1. Read this file fully
2. Run `git status` — know what changed last session
3. Check which build order step you're on
4. `docker compose up -d` and confirm all services healthy
5. Use `sdd` skill for any module touching more than 2 files
6. Use `context7` for FastAPI, Playwright, Celery, jobspy, WeasyPrint — these
   change frequently and Claude's training data may be stale

---

## Current Status

> Update this manually at the end of every session.

**Current step:** Not started

**Last session:** —

**Blockers:** —

**Notes:** —
