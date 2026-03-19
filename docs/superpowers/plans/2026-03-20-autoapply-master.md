# AutoApply — Master Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build AutoApply — a self-hostable AI job application agent that parses resumes, scores them, scrapes matching jobs, tailors applications, and auto-applies via Playwright.

**Architecture:** Full-stack monorepo. FastAPI backend handles all AI + scraping logic. Next.js 14 frontend (App Router) provides the dashboard UI. Postgres (via Alembic) is the data store. Redis + Celery handle background work. Docker Compose ties everything together.

**Tech Stack:** Next.js 14, TypeScript, Tailwind, shadcn/ui, FastAPI, Python 3.11, Anthropic Claude API, PyMuPDF, python-docx, jobspy, Playwright, playwright-stealth, PostgreSQL, Alembic, Redis, Celery, WeasyPrint, Clerk Auth, Docker Compose

---

## Phase 1: Docker Compose Skeleton + Postgres Schema

**Files:**
- Create: `autoapply/docker-compose.yml`
- Create: `autoapply/.env.example`
- Create: `autoapply/backend/requirements.txt`
- Create: `autoapply/backend/alembic.ini`
- Create: `autoapply/backend/alembic/env.py`
- Create: `autoapply/backend/alembic/versions/001_initial_schema.py`
- Create: `autoapply/backend/db/database.py`
- Create: `autoapply/backend/models/schemas.py`

- [ ] Write docker-compose.yml with 6 services (frontend, backend, postgres, redis, celery_worker, flower)
- [ ] Write .env.example with all required vars
- [ ] Write backend requirements.txt
- [ ] Write Alembic migration for all 5 tables
- [ ] Write SQLAlchemy async database.py
- [ ] Write Pydantic v2 schemas.py
- [ ] Test: `docker compose up -d` all services healthy
- [ ] Commit: "feat: phase 1 - docker compose skeleton + postgres schema"

## Phase 2: FastAPI Base + Resume Upload/Parse/Score

**Files:**
- Create: `autoapply/backend/main.py`
- Create: `autoapply/backend/routers/resume.py`
- Create: `autoapply/backend/services/resume_parser.py`
- Create: `autoapply/backend/services/resume_scorer.py`
- Create: `autoapply/backend/middleware/auth.py`

- [ ] Write FastAPI main.py with CORS, middleware, router registration
- [ ] Write Clerk JWT validation middleware
- [ ] Write resume_parser.py (fitz + python-docx → Claude)
- [ ] Write resume_scorer.py (ATS + Impact + Completeness via Claude)
- [ ] Write resume router with upload/parse/score endpoints
- [ ] Test endpoints with curl
- [ ] Commit: "feat: phase 2 - fastapi base + resume parse/score"

## Phase 3: Next.js Shell + Auth + Resume Upload UI

**Files:**
- Create: `autoapply/frontend/` (full Next.js project)
- Create: `autoapply/frontend/app/layout.tsx`
- Create: `autoapply/frontend/app/page.tsx` (placeholder)
- Create: `autoapply/frontend/app/dashboard/layout.tsx`
- Create: `autoapply/frontend/app/dashboard/page.tsx`
- Create: `autoapply/frontend/app/dashboard/resume/page.tsx`
- Create: `autoapply/frontend/components/resume/ScoreRing.tsx`
- Create: `autoapply/frontend/components/resume/ResumeUpload.tsx`
- Create: `autoapply/frontend/lib/api.ts`
- Create: `autoapply/frontend/lib/types.ts`

- [ ] Init Next.js 14 app with TypeScript + Tailwind + shadcn/ui
- [ ] Set up Clerk auth (sign-in/sign-up routes)
- [ ] Build sidebar dashboard layout
- [ ] Build resume upload page with drag-drop
- [ ] Build animated score ring charts
- [ ] Wire to backend API
- [ ] Commit: "feat: phase 3 - nextjs shell + resume upload UI"

## Phase 4: Hunt Profile Form

**Files:**
- Create: `autoapply/backend/routers/hunt_profile.py`
- Create: `autoapply/frontend/app/dashboard/hunt-profile/page.tsx`
- Create: `autoapply/frontend/components/hunt-profile/HuntProfileForm.tsx`

- [ ] Write hunt_profile router (CRUD)
- [ ] Build 7-step wizard form in Next.js
- [ ] Commit: "feat: phase 4 - hunt profile"

## Phase 5: Job Scraper + Job Listing UI

**Files:**
- Create: `autoapply/backend/services/job_scraper.py`
- Create: `autoapply/backend/services/job_matcher.py`
- Create: `autoapply/backend/routers/jobs.py`
- Create: `autoapply/frontend/app/dashboard/jobs/page.tsx`
- Create: `autoapply/frontend/components/jobs/JobCard.tsx`

- [ ] Integrate jobspy
- [ ] Write Claude JD parser + match scorer
- [ ] Write jobs router
- [ ] Build filterable jobs list UI
- [ ] Commit: "feat: phase 5 - job scraper + jobs UI"

## Phase 6: AI Tailoring Engine

**Files:**
- Create: `autoapply/backend/services/resume_tailor.py`
- Create: `autoapply/backend/services/cover_letter.py`
- Create: `autoapply/backend/routers/applications.py`

- [ ] Write gap analysis prompt
- [ ] Write resume rewrite prompt (with integrity constraint)
- [ ] Write cover letter prompt
- [ ] Wire to applications router
- [ ] Commit: "feat: phase 6 - ai tailoring engine"

## Phase 7: Manual Apply Flow + Application Tracker

**Files:**
- Create: `autoapply/frontend/app/dashboard/applications/page.tsx`
- Create: `autoapply/frontend/components/applications/KanbanBoard.tsx`
- Create: `autoapply/frontend/components/applications/ApplicationCard.tsx`

- [ ] Build Kanban board (7 columns)
- [ ] Build application detail modal (diff view)
- [ ] Build analytics panel
- [ ] Commit: "feat: phase 7 - manual apply flow + tracker UI"

## Phase 8: Playwright ATS Adapters

**Files:**
- Create: `autoapply/backend/services/apply_engine.py`
- Create: `autoapply/backend/services/adapters/greenhouse.py`
- Create: `autoapply/backend/services/adapters/lever.py`

- [ ] Write base adapter interface
- [ ] Implement Greenhouse adapter
- [ ] Implement Lever adapter
- [ ] playwright-stealth + random delays
- [ ] Commit: "feat: phase 8 - playwright ats adapters"

## Phase 9: Celery Workers

**Files:**
- Create: `autoapply/backend/workers/scrape_worker.py`
- Create: `autoapply/backend/workers/apply_worker.py`
- Create: `autoapply/backend/celery_app.py`

- [ ] Set up Celery app with Redis broker
- [ ] Implement scrape_worker (every 6h via Celery Beat)
- [ ] Implement apply_worker (daily limit enforcement)
- [ ] Commit: "feat: phase 9 - celery workers"

## Phase 10: PDF Generation

**Files:**
- Create: `autoapply/backend/services/pdf_generator.py`
- Create: `autoapply/backend/templates/resume.html`

- [ ] WeasyPrint ATS-safe template
- [ ] Wire to applications endpoint
- [ ] Commit: "feat: phase 10 - pdf generation"

## Phase 11: Landing Page

**Files:**
- Modify: `autoapply/frontend/app/page.tsx`

- [ ] Dark hero with animated terminal feed
- [ ] Feature grid
- [ ] docker compose up CTA
- [ ] Commit: "feat: phase 11 - landing page"

## Phase 12: README + Docker Docs

**Files:**
- Create: `autoapply/README.md`

- [ ] Self-hosting guide
- [ ] Env var reference
- [ ] Commit: "docs: readme + docker docs"

## Phase 13: Git Push

- [ ] Init git repo
- [ ] Push to https://github.com/JoeArmageddon/JobAppTool.git
