"""Initial migration

Revision ID: 001
Revises:
Create Date: 2025-12-22 12:00:00.000000

"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create Enums
    # sa.Enum("CLIENT", "AGENT", "ADMIN", name="userrole").create(op.get_bind())
    # sa.Enum("OPEN", "AI_ANSWERED", "ESCALATED", "CLOSED", name="ticketstatus").create(
    #     op.get_bind()
    # )
    # sa.Enum("AI", "HUMAN", name="responsesource").create(op.get_bind())
    # sa.Enum("new_doc", "enrich", "correction", name="kbupdatetype").create(
    #     op.get_bind()
    # )

    # Create Users
    op.create_table(
        "users",
        sa.Column("id", sa.BigInteger(), nullable=False),
        sa.Column("email", sa.String(length=255), nullable=False),
        sa.Column("password_hash", sa.Text(), nullable=False),
        sa.Column(
            "role", sa.Enum("CLIENT", "AGENT", "ADMIN", name="userrole"), nullable=False
        ),
        sa.Column("language", sa.String(length=5), nullable=True),
        sa.Column("profile_picture_url", sa.Text(), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=True,
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_users_email"), "users", ["email"], unique=True)
    op.create_index(op.f("ix_users_id"), "users", ["id"], unique=False)

    # Create KB Documents
    op.create_table(
        "kb_documents",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("category", sa.String(length=100), nullable=True),
        # Using vector type if available, else handled as custom
        sa.Column("embeddings", sa.Text(), nullable=True),  # Placeholder for vector
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=True,
        ),
        sa.PrimaryKeyConstraint("id"),
    )

    # Create Tickets
    op.create_table(
        "tickets",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("reference", sa.String(length=20), nullable=False),
        sa.Column("client_id", sa.BigInteger(), nullable=False),
        sa.Column("assigned_agent_id", sa.BigInteger(), nullable=True),
        sa.Column("subject", sa.String(length=255), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("category", sa.String(length=100), nullable=True),
        sa.Column(
            "status",
            sa.Enum("OPEN", "AI_ANSWERED", "ESCALATED", "CLOSED", name="ticketstatus"),
            nullable=True,
        ),
        sa.Column("ai_confidence", sa.Float(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=True,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=True,
        ),
        sa.ForeignKeyConstraint(
            ["assigned_agent_id"],
            ["users.id"],
        ),
        sa.ForeignKeyConstraint(
            ["client_id"],
            ["users.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("reference"),
    )

    # Create KB Snippets
    op.create_table(
        "kb_snippets",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("doc_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("relevance_score", sa.Float(), nullable=True),
        sa.ForeignKeyConstraint(["doc_id"], ["kb_documents.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )

    # Create KB Updates
    op.create_table(
        "kb_updates",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("ticket_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column(
            "change_type",
            sa.Enum("new_doc", "enrich", "correction", name="kbupdatetype"),
            nullable=False,
        ),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column(
            "timestamp",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=True,
        ),
        sa.ForeignKeyConstraint(
            ["ticket_id"],
            ["tickets.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
    )

    # Create Ticket Attachments
    op.create_table(
        "ticket_attachments",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("ticket_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("file_url", sa.Text(), nullable=False),
        sa.Column("file_type", sa.String(length=50), nullable=True),
        sa.Column(
            "uploaded_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=True,
        ),
        sa.ForeignKeyConstraint(
            ["ticket_id"],
            ["tickets.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
    )

    # Create Ticket Feedback
    op.create_table(
        "ticket_feedback",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("ticket_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("satisfied", sa.Boolean(), nullable=False),
        sa.Column("comment", sa.Text(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=True,
        ),
        sa.ForeignKeyConstraint(
            ["ticket_id"],
            ["tickets.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("ticket_id"),
    )

    # Create Ticket Responses
    op.create_table(
        "ticket_responses",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("ticket_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column(
            "source", sa.Enum("AI", "HUMAN", name="responsesource"), nullable=False
        ),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("confidence", sa.Float(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=True,
        ),
        sa.ForeignKeyConstraint(
            ["ticket_id"],
            ["tickets.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
    )


def downgrade() -> None:
    op.drop_table("ticket_responses")
    op.drop_table("ticket_feedback")
    op.drop_table("ticket_attachments")
    op.drop_table("kb_updates")
    op.drop_table("kb_snippets")
    op.drop_table("tickets")
    op.drop_table("kb_documents")
    op.drop_index(op.f("ix_users_id"), table_name="users")
    op.drop_index(op.f("ix_users_email"), table_name="users")
    op.drop_table("users")

    sa.Enum(name="kbupdatetype").drop(op.get_bind())
    sa.Enum(name="responsesource").drop(op.get_bind())
    sa.Enum(name="ticketstatus").drop(op.get_bind())
    sa.Enum(name="userrole").drop(op.get_bind())
