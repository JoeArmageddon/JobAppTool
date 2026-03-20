# Docker Setup Guide — AutoApply

## 1. Install Docker Desktop (Windows 11)

1. Go to https://www.docker.com/products/docker-desktop/
2. Click **Download for Windows — AMD64**
   - AMD64 = all normal Intel/AMD laptops and desktops
   - ARM only for Surface Pro X or similar ARM devices
   - Not sure? Run in PowerShell: `(Get-WmiObject Win32_Processor).Architecture`
     - Returns `9` → AMD64 (you're here)
     - Returns `12` → ARM64
3. Run `Docker Desktop Installer.exe`
4. Keep **"Use WSL 2 instead of Hyper-V"** checked (default)
5. Restart your PC

## 2. Install WSL 2

Open **PowerShell as Administrator**:

```powershell
wsl --install
wsl --set-default-version 2
```

Restart if prompted.

## 3. Verify Installation

Open any terminal:

```bash
docker --version
docker compose version
```

Both should print version numbers. The Docker whale icon should appear in your system tray.

---

## 4. Configure Your .env File

Copy the example and fill in your values:

```bash
cd "D:\Projects\Job Application Tool\autoapply"
copy .env.example .env
notepad .env
```

### Required values to fill in:

```env
# AI Provider — pick one:
LLM_PROVIDER=groq
GROQ_API_KEY=your-groq-key     # free at console.groq.com
# OR
# LLM_PROVIDER=anthropic
# ANTHROPIC_API_KEY=sk-ant-...

# Database — choose any strong password:
POSTGRES_PASSWORD=your-strong-password-here
DATABASE_URL=postgresql+asyncpg://autoapply:your-strong-password-here@postgres:5432/autoapply
SYNC_DATABASE_URL=postgresql://autoapply:your-strong-password-here@postgres:5432/autoapply

# Clerk Auth — free at clerk.com:
NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY=pk_test_...
CLERK_SECRET_KEY=sk_test_...
CLERK_WEBHOOK_SECRET=whsec_...

# LinkedIn Easy Apply (optional):
LINKEDIN_EMAIL=your@email.com
LINKEDIN_PASSWORD=your-linkedin-password
```

### Getting Clerk Keys (free):
1. Go to https://clerk.com and create a free account
2. Create a new application — enable Email/Password sign-in
3. Go to **Configure → API Keys**
4. Copy `NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY` and `CLERK_SECRET_KEY`
5. Go to **Configure → Webhooks** → Add endpoint:
   - URL: `http://localhost:8000/api/v1/webhooks/clerk`
   - Event: `user.created`
6. Copy the signing secret → `CLERK_WEBHOOK_SECRET`

---

## 5. Start AutoApply

```bash
cd "D:\Projects\Job Application Tool\autoapply"

# Start all 7 services
docker compose up -d

# First time only — create database tables
docker compose exec backend alembic upgrade head

# Check all services are healthy
docker compose ps
```

Open **http://localhost:3000** in your browser.

---

## 6. Services Overview

| Service     | URL                        | What it does                        |
|-------------|----------------------------|-------------------------------------|
| frontend    | http://localhost:3000      | Next.js dashboard                   |
| backend     | http://localhost:8000      | FastAPI REST API                    |
| postgres    | localhost:5432             | PostgreSQL database                 |
| redis       | localhost:6379             | Celery task queue                   |
| celery_worker | —                        | Runs background tasks               |
| celery_beat | —                          | Triggers job scrape every 6 hours   |
| flower      | http://localhost:5555      | Celery task monitor                 |

---

## 7. Common Commands

```bash
# View all logs
docker compose logs -f

# View logs for one service
docker compose logs -f backend
docker compose logs -f celery_worker

# Restart a service after a code change
docker compose restart backend

# Stop everything (keeps data)
docker compose down

# Stop and delete all data (fresh start)
docker compose down -v

# Run database migrations after schema change
docker compose exec backend alembic upgrade head

# Manually trigger a job scrape (don't wait 6 hours)
docker compose exec celery_worker celery -A celery_app call workers.scrape_worker.scrape_jobs_for_all_profiles

# Open Celery task monitor
# http://localhost:5555
```

---

## 8. Troubleshooting

**"WSL 2 installation is incomplete"**
```powershell
# Run in PowerShell as Administrator
wsl --update
wsl --set-default-version 2
# Then restart Docker Desktop
```

**Backend keeps restarting**
```bash
docker compose logs backend
# Most common cause: missing env var or wrong POSTGRES_PASSWORD
```

**"POSTGRES_PASSWORD is not set"**
- Make sure your `.env` file has `POSTGRES_PASSWORD=something` (not `CHANGE_ME`)
- The three DATABASE_URL values must use the same password

**Port already in use**
```bash
# Find what's using port 3000 or 8000
netstat -ano | findstr :3000
# Kill it or change the port in docker-compose.yml
```

**Frontend build fails in Docker**
- Make sure `NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY` is set in `.env`
- It must start with `pk_test_` or `pk_live_`

---

## 9. Switching AI Provider

To switch between Anthropic and Groq without rebuilding:

```bash
# Edit .env
notepad .env
# Change LLM_PROVIDER=groq or LLM_PROVIDER=anthropic

# Restart the backend and workers to pick up the change
docker compose restart backend celery_worker celery_beat
```
