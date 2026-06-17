"""initial migration

Revision ID: 0001
Revises:
Create Date: 2026-06-17 12:00:00.000000
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB, UUID

revision: str = "0001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id", sa.BigInteger(), autoincrement=False, nullable=False),
        sa.Column("username", sa.String(128), nullable=True),
        sa.Column("first_name", sa.String(256), nullable=True),
        sa.Column("last_name", sa.String(256), nullable=True),
        sa.Column("language_code", sa.String(16), nullable=True),
        sa.Column("is_active", sa.Boolean(), default=True),
        sa.Column("is_owner", sa.Boolean(), default=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "references",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("uuid", sa.String(36), nullable=False),
        sa.Column("source", sa.String(128), nullable=False),
        sa.Column("source_url", sa.String(1024), nullable=True),
        sa.Column("title", sa.String(512), nullable=True),
        sa.Column("original_text", sa.Text(), nullable=True),
        sa.Column("translated_text", sa.Text(), nullable=True),
        sa.Column("image_url", sa.String(1024), nullable=True),
        sa.Column("local_image_path", sa.String(512), nullable=True),
        sa.Column("category", sa.String(128), nullable=True),
        sa.Column("tags", JSONB(), nullable=True, default=dict),
        sa.Column("ai_summary", sa.Text(), nullable=True),
        sa.Column("engagement", JSONB(), nullable=True),
        sa.Column("region", sa.String(64), nullable=True),
        sa.Column("language", sa.String(16), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_references_uuid", "references", ["uuid"])
    op.create_index("ix_references_category", "references", ["category"])

    op.create_table(
        "settings",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("user_id", sa.BigInteger(), nullable=False),
        sa.Column("auto_posting_enabled", sa.Boolean(), default=False),
        sa.Column("posting_interval_hours", sa.Integer(), default=6),
        sa.Column("boards", JSONB(), nullable=True, default=list),
        sa.Column("categories", JSONB(), nullable=True, default=list),
        sa.Column("image_style", sa.String(128), default="modern minimalistic"),
        sa.Column("language", sa.String(16), default="ru"),
        sa.Column("content_tone", sa.String(64), default="professional"),
        sa.Column("openai_model", sa.String(64), default="gpt-4o"),
        sa.Column("image_generation_model", sa.String(64), default="openai"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("user_id"),
    )

    op.create_table(
        "scheduler_jobs",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("job_id", sa.String(256), nullable=False),
        sa.Column("name", sa.String(256), nullable=False),
        sa.Column("job_type", sa.String(64), nullable=False),
        sa.Column("interval_minutes", sa.Integer(), nullable=True),
        sa.Column("is_active", sa.Boolean(), default=True),
        sa.Column("last_run", sa.DateTime(timezone=True), nullable=True),
        sa.Column("next_run", sa.DateTime(timezone=True), nullable=True),
        sa.Column("metadata", JSONB(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("job_id"),
    )
    op.create_index("ix_scheduler_jobs_job_type", "scheduler_jobs", ["job_type"])

    op.create_table(
        "pins",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("uuid", sa.String(36), nullable=False),
        sa.Column("user_id", sa.BigInteger(), nullable=False),
        sa.Column("pinterest_pin_id", sa.String(128), nullable=True),
        sa.Column("board_id", sa.String(128), nullable=True),
        sa.Column("title", sa.String(512), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("link", sa.String(1024), nullable=True),
        sa.Column("image_url", sa.String(1024), nullable=True),
        sa.Column("local_image_path", sa.String(512), nullable=True),
        sa.Column("category", sa.String(128), nullable=True),
        sa.Column("tags", JSONB(), nullable=True),
        sa.Column("seo_keywords", JSONB(), nullable=True),
        sa.Column("cta_text", sa.String(256), nullable=True),
        sa.Column("source_url", sa.String(1024), nullable=True),
        sa.Column("is_published", sa.Boolean(), default=False),
        sa.Column("is_ai_generated", sa.Boolean(), default=False),
        sa.Column("published_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("pinterest_pin_id"),
    )
    op.create_index("ix_pins_uuid", "pins", ["uuid"])
    op.create_index("ix_pins_category", "pins", ["category"])

    op.create_table(
        "generated_content",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("uuid", sa.String(36), nullable=False),
        sa.Column("reference_id", sa.BigInteger(), nullable=True),
        sa.Column("pin_title", sa.String(512), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("seo_keywords", JSONB(), nullable=True),
        sa.Column("hashtags", JSONB(), nullable=True),
        sa.Column("cta_text", sa.String(256), nullable=True),
        sa.Column("category", sa.String(128), nullable=True),
        sa.Column("tone", sa.String(64), nullable=True),
        sa.Column("is_used", sa.Boolean(), default=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["reference_id"], ["references.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_generated_content_uuid", "generated_content", ["uuid"])
    op.create_index("ix_generated_content_category", "generated_content", ["category"])

    op.create_table(
        "analytics",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("pin_id", sa.BigInteger(), nullable=False),
        sa.Column("impressions", sa.Integer(), default=0),
        sa.Column("saves", sa.Integer(), default=0),
        sa.Column("clicks", sa.Integer(), default=0),
        sa.Column("outbound_clicks", sa.Integer(), default=0),
        sa.Column("ctr", sa.Float(), nullable=True),
        sa.Column("collected_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["pin_id"], ["pins.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("pin_id", "collected_at", name="uq_pin_analytics_date"),
    )

    op.create_table(
        "generated_images",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("content_id", sa.BigInteger(), nullable=False),
        sa.Column("file_path", sa.String(512), nullable=False),
        sa.Column("prompt", sa.Text(), nullable=True),
        sa.Column("model", sa.String(64), nullable=True),
        sa.Column("style", sa.String(128), nullable=True),
        sa.Column("colors", JSONB(), nullable=True),
        sa.Column("is_selected", sa.Boolean(), default=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["content_id"], ["generated_content.id"]),
        sa.PrimaryKeyConstraint("id"),
    )


def downgrade() -> None:
    op.drop_table("generated_images")
    op.drop_table("analytics")
    op.drop_table("generated_content")
    op.drop_table("pins")
    op.drop_table("scheduler_jobs")
    op.drop_table("settings")
    op.drop_table("references")
    op.drop_table("users")
