"""Initial schema — users, resumes, hunt_profiles, jobs, applications

Revision ID: 001
Revises:
Create Date: 2026-03-20
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID, ARRAY, JSON

revision = "001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id", UUID(as_uuid=False), primary_key=True),
        sa.Column("clerk_id", sa.String(), nullable=False, unique=True),
        sa.Column("email", sa.String(), nullable=False, unique=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
    )
    op.create_index("ix_users_clerk_id", "users", ["clerk_id"])

    op.create_table(
        "resumes",
        sa.Column("id", UUID(as_uuid=False), primary_key=True),
        sa.Column("user_id", UUID(as_uuid=False), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("raw_text", sa.Text()),
        sa.Column("structured_json", JSON()),
        sa.Column("ats_score", sa.Float()),
        sa.Column("impact_score", sa.Float()),
        sa.Column("completeness_score", sa.Float()),
        sa.Column("overall_score", sa.Float()),
        sa.Column("suggestions_json", JSON()),
        sa.Column("file_url", sa.String()),
        sa.Column("original_filename", sa.String()),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
    )
    op.create_index("ix_resumes_user_id", "resumes", ["user_id"])

    op.create_table(
        "hunt_profiles",
        sa.Column("id", UUID(as_uuid=False), primary_key=True),
        sa.Column("user_id", UUID(as_uuid=False), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("target_titles", ARRAY(sa.String()), server_default="{}"),
        sa.Column("industries", ARRAY(sa.String()), server_default="{}"),
        sa.Column("locations", ARRAY(sa.String()), server_default="{}"),
        sa.Column("remote_preference", sa.String(), server_default="hybrid"),
        sa.Column("seniority_level", sa.String()),
        sa.Column("salary_floor", sa.Integer()),
        sa.Column("company_size_pref", sa.String()),
        sa.Column("blacklisted_companies", ARRAY(sa.String()), server_default="{}"),
        sa.Column("job_sources", ARRAY(sa.String()), server_default="{}"),
        sa.Column("is_active", sa.Boolean(), server_default="true"),
        sa.Column("daily_apply_limit", sa.Integer(), server_default="10"),
        sa.Column("auto_apply", sa.Boolean(), server_default="false"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
    )
    op.create_index("ix_hunt_profiles_user_id", "hunt_profiles", ["user_id"])

    op.create_table(
        "jobs",
        sa.Column("id", UUID(as_uuid=False), primary_key=True),
        sa.Column("title", sa.String(), nullable=False),
        sa.Column("company", sa.String(), nullable=False),
        sa.Column("location", sa.String()),
        sa.Column("description_raw", sa.Text()),
        sa.Column("description_parsed_json", JSON()),
        sa.Column("source", sa.String()),
        sa.Column("source_url", sa.String()),
        sa.Column("source_job_id", sa.String(), unique=True),
        sa.Column("salary_min", sa.Integer()),
        sa.Column("salary_max", sa.Integer()),
        sa.Column("posted_at", sa.DateTime(timezone=True)),
        sa.Column("scraped_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.Column("match_score", sa.Float()),
        sa.Column("match_reasons_json", JSON()),
        sa.Column("status", sa.String(), server_default="new"),
    )
    op.create_index("ix_jobs_source_job_id", "jobs", ["source_job_id"])
    op.create_index("ix_jobs_status", "jobs", ["status"])

    op.create_table(
        "applications",
        sa.Column("id", UUID(as_uuid=False), primary_key=True),
        sa.Column("user_id", UUID(as_uuid=False), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("job_id", UUID(as_uuid=False), sa.ForeignKey("jobs.id", ondelete="CASCADE"), nullable=False),
        sa.Column("resume_id", UUID(as_uuid=False), sa.ForeignKey("resumes.id"), nullable=True),
        sa.Column("tailored_resume_text", sa.Text()),
        sa.Column("tailored_resume_pdf_url", sa.String()),
        sa.Column("cover_letter_text", sa.Text()),
        sa.Column("status", sa.String(), server_default="queued"),
        sa.Column("applied_at", sa.DateTime(timezone=True)),
        sa.Column("response_at", sa.DateTime(timezone=True)),
        sa.Column("notes", sa.Text()),
        sa.Column("screenshot_url", sa.String()),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
    )
    op.create_index("ix_applications_user_id", "applications", ["user_id"])
    op.create_index("ix_applications_status", "applications", ["status"])


def downgrade() -> None:
    op.drop_table("applications")
    op.drop_table("jobs")
    op.drop_table("hunt_profiles")
    op.drop_table("resumes")
    op.drop_table("users")
