"""AutoApply FastAPI application entry point."""

import os
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from loguru import logger

from routers import resume, hunt_profile, jobs, applications


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("AutoApply backend starting up")
    # Ensure uploads directory exists
    uploads_dir = os.environ.get("UPLOADS_DIR", "/app/uploads")
    os.makedirs(uploads_dir, exist_ok=True)
    yield
    logger.info("AutoApply backend shutting down")


app = FastAPI(
    title="AutoApply API",
    version="1.0.0",
    description="Self-hostable AI job application agent",
    lifespan=lifespan,
)

# CORS — frontend origin only
ALLOWED_ORIGINS = os.environ.get(
    "ALLOWED_ORIGINS", "http://localhost:3000"
).split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ─── Global exception handler ────────────────────────────────────────────────

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    logger.error(f"Unhandled exception on {request.method} {request.url}: {exc}")
    return JSONResponse(
        status_code=500,
        content={"error": "Internal server error", "code": "INTERNAL_ERROR"},
    )


# ─── Health check ────────────────────────────────────────────────────────────

@app.get("/health", tags=["system"])
async def health() -> dict:
    return {"status": "ok", "service": "autoapply-backend"}


# ─── Routers ─────────────────────────────────────────────────────────────────

app.include_router(resume.router, prefix="/api/v1")
app.include_router(hunt_profile.router, prefix="/api/v1")
app.include_router(jobs.router, prefix="/api/v1")
app.include_router(applications.router, prefix="/api/v1")
