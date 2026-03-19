# AutoApply — Claude Code Build Prompt

## Project Overview

Build **AutoApply** — an open-source, self-hostable AI job application agent. Users upload their resume, get an AI-powered score and improvement suggestions, define their job hunt criteria, and the tool automatically finds matching jobs, tailors the resume and cover letter for each one, and either auto-applies or queues for review. Everything runs locally via Docker Compose.

---

## Tech Stack

| Layer | Choice |
|---|---|
| Frontend | Next.js 14 (App Router) + TypeScript + Tailwind CSS + shadcn/ui |
| Backend | Python 3.11 + FastAPI |
| AI Engine | Anthropic Claude API (claude-sonnet-4-20250514) |
| Resume Parsing | PyMuPDF (`fitz`) + python-docx |
| Job Scraping | `jobspy` (PyPI) |
| Browser Automation | Playwright (Python) |
| Database | PostgreSQL via Supabase (or local Docker Postgres) |
| Queue | Redis + Celery |
| Auth | Clerk (Next.js) + API key validation on FastAPI |
| PDF Generation | WeasyPrint |
| Self-host | Docker Compose (one-command startup) |

---

## Design System

- **Theme:** Dark, terminal-meets-product aesthetic
- **Background:** `#0a0a0f`
- **Primary accent:** Indigo `#6366f1`
- **Secondary:** Emerald `#10b981` for success states
- **Danger:** Rose `#f43f5e` for rejected/failed states
- **Font:** `Geist` (display) + `Geist Mono` (data/code elements)
- **Style:** Dense information layout, sidebar navigation, subtle glows on interactive elements

---

## Project Structure

```
autoapply/
├── frontend/
│   ├── app/
│   │   ├── (auth)/sign-in/ sign-up/
│   │   ├── dashboard/
│   │   │   ├── page.tsx              # Overview + stats
│   │   │   ├── resume/               # Resume upload + scoring
│   │   │   ├── hunt-profile/         # Job preferences setup
│   │   │   ├── jobs/                 # Found jobs list
│   │   │   ├── applications/         # Application tracker
│   │   │   └── settings/
│   │   ├── layout.tsx
│   │   └── page.tsx                  # Landing page
│   ├── components/
│   │   ├── ui/                       # shadcn/ui
│   │   ├── resume/
│   │   ├── jobs/
│   │   └── applications/
│   └── lib/
│       ├── api.ts
│       └── types.ts
│
├── backend/
│   ├── main.py
│   ├── routers/
│   │   ├── resume.py
│   │   ├── jobs.py
│   │   ├── applications.py
│   │   └── hunt_profile.py
│   ├── services/
│   │   ├── resume_parser.py
│   │   ├── resume_scorer.py
│   │   ├── resume_tailor.py
│   │   ├── cover_letter.py
│   │   ├── job_scraper.py
│   │   ├── job_matcher.py
│   │   ├── apply_engine.py
│   │   └── pdf_generator.py
│   ├── workers/
│   │   ├── scrape_worker.py
│   │   └── apply_worker.py
│   ├── models/schemas.py
│   ├── db/database.py
│   └── requirements.txt
│
├── docker-compose.yml
├── .env.example
├── CLAUDE.md
└── README.md
```

---

## Module Build Instructions

### 1. Database Schema

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

---

### 2. Resume Parser (`backend/services/resume_parser.py`)

Accept PDF and DOCX. Use `fitz` for PDF, `python-docx` for DOCX. Send raw text to Claude:

```
You are a resume parser. Extract into strict JSON:
{
  "name", "email", "phone", "location", "linkedin", "github",
  "summary", "skills": [],
  "experience": [{ "company", "title", "start_date", "end_date", "current", "responsibilities": [], "achievements": [] }],
  "education": [], "certifications": [], "languages": [], "projects": []
}
Return ONLY valid JSON. No commentary.
```

---

### 3. Resume Scorer (`backend/services/resume_scorer.py`)

Score on three dimensions via Claude:
- **ATS Score (0-100):** keyword richness, standard section names, no tables/graphics
- **Impact Score (0-100):** % bullets with action verbs + quantified results
- **Completeness Score (0-100):** all key sections present

Return:
```json
{
  "ats_score": 72, "impact_score": 58, "completeness_score": 90, "overall_score": 73,
  "suggestions": [{ "category": "Impact", "issue": "...", "fix": "..." }]
}
```

Display as animated ring charts in the frontend.

---

### 4. Hunt Profile (`frontend/app/dashboard/hunt-profile/`)

7-step form:
1. Target job titles (tag input)
2. Industries (multi-select)
3. Locations + remote toggle
4. Seniority, salary floor, company size
5. Job sources (LinkedIn, Indeed, Glassdoor, Wellfound, Naukri, ZipRecruiter)
6. Company blacklist + daily apply limit slider (1–50)
7. Mode: `Auto-Apply` vs `Review Before Send`

---

### 5. Job Scraper (`backend/services/job_scraper.py`)

```python
from jobspy import scrape_jobs

jobs = scrape_jobs(
    site_name=["linkedin", "indeed", "glassdoor", "zip_recruiter"],
    search_term=hunt_profile.target_titles[0],
    location=hunt_profile.locations[0],
    results_wanted=50,
    hours_old=24
)
```

For each job: deduplicate, parse JD via Claude, score match against user resume (0-100), store in DB. Run as Celery periodic task every 6 hours.

---

### 6. AI Tailoring Engine (`backend/services/resume_tailor.py`)

**Step 1 — Gap Analysis:**
```
Given resume JSON and JD, identify: skill gaps, exact keyword matches, synonym matches,
suggested reordering for relevance. Return JSON.
```

**Step 2 — Resume Rewrite:**
```
You are a professional resume writer. Using ONLY the facts in the original resume
(never invent, never exaggerate, never hallucinate), rewrite the resume to:
- Lead with most relevant experience for this role
- Incorporate exact keywords from JD naturally
- Reframe bullets using JD language and priorities
- Strengthen impact language where numbers already exist
CRITICAL: Do not add any skills, experience, or credentials not in the original.
Return full rewritten resume as JSON matching original schema.
```

**Step 3 — Cover Letter:**
```
Write a 3-paragraph cover letter. Max 280 words. Professional, direct, not sycophantic.
P1: Why this specific company and role (use company name + 1 JD detail).
P2: Top 2-3 matching achievements from resume mapped to JD requirements.
P3: Forward-looking closer.
```

---

### 7. Application Tracker (`frontend/app/dashboard/applications/`)

Kanban columns: `Queued → Applying → Applied → Viewed → Interview → Rejected / Offer`

Each card: company logo (Clearbit), role title, match score badge, date, expand to see tailored resume diff + cover letter.

Analytics panel: response rate by industry/source, avg match score, applications/day chart.

---

### 8. Playwright Apply Engine (`backend/services/apply_engine.py`)

ATS adapters for: **Greenhouse**, **Lever**, **Workday**, **iCIMS**, **Indeed Easy Apply**

Each adapter returns: `success | failed | requires_human`

Anti-detection:
- Use `playwright-stealth`
- Random delays 500ms–2500ms between actions
- Screenshot confirmation on success
- Hard-enforce daily apply limit

---

### 9. PDF Generator (`backend/services/pdf_generator.py`)

WeasyPrint: tailored resume JSON → ATS-safe single-column PDF (no tables, no graphics, standard fonts).

---

### 10. Docker Compose

Services: `frontend (3000)`, `backend (8000)`, `postgres (5432)`, `redis (6379)`, `celery_worker`, `flower (5555)`

`.env.example`:
```
ANTHROPIC_API_KEY=
DATABASE_URL=
REDIS_URL=
CLERK_SECRET_KEY=
NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY=
CLERK_WEBHOOK_SECRET=
```

---

### 11. Landing Page (`frontend/app/page.tsx`)

Dark, high-converting. Include:
- Hero + animated terminal showing mock "applying to 12 jobs..." live feed
- Feature grid
- `docker compose up` one-liner CTA
- GitHub star badge

---

## Critical Constraints

1. **Resume integrity:** Claude must NEVER hallucinate credentials. Every rewrite prompt must include the explicit constraint.
2. **Daily apply cap:** Hard-enforce in Celery worker. Never exceed regardless of queue size.
3. **Privacy first:** In self-hosted mode, resumes and credentials never leave the user's own infrastructure. Document this clearly.
4. **Audit trail:** Store exact resume version + cover letter used per application.
5. **Rate limiting:** Exponential backoff on all scraper calls.

---

## Build Order

1. Docker Compose skeleton + Postgres schema
2. FastAPI base + Resume upload/parse/score endpoints
3. Next.js shell + auth + resume upload UI with score display
4. Hunt profile form (frontend + backend)
5. Job scraper + jobspy + job listing UI
6. AI tailoring engine (resume rewrite + cover letter)
7. Manual apply flow (user reviews, approves, applies)
8. Application tracker UI
9. Playwright ATS adapters (Greenhouse first)
10. Celery workers (auto-scrape + auto-apply queue)
11. PDF generation
12. Landing page
13. README + Docker docs
