"""Update ticket attachments table

Revision ID: 002
Revises: 001
Create Date: 2025-12-23 12:00:00.000000

"""

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "002"
down_revision = "001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add new columns to ticket_attachments
    op.add_column(
        "ticket_attachments",
        sa.Column("filename", sa.String(length=255), nullable=True),
    )
    op.add_column(
        "ticket_attachments",
        sa.Column("original_filename", sa.String(length=255), nullable=True),
    )
    op.add_column(
        "ticket_attachments",
        sa.Column("file_path", sa.Text(), nullable=True),
    )
    op.add_column(
        "ticket_attachments",
        sa.Column("file_size", sa.BigInteger(), nullable=True),
    )
    
    # Copy data from file_url to file_path for existing records
    op.execute(
        "UPDATE ticket_attachments SET file_path = file_url, filename = file_url, original_filename = file_url WHERE file_path IS NULL"
    )
    
    # Make columns not nullable after data migration
    op.alter_column("ticket_attachments", "filename", nullable=False)
    op.alter_column("ticket_attachments", "original_filename", nullable=False)
    op.alter_column("ticket_attachments", "file_path", nullable=False)
    
    # Drop old column
    op.drop_column("ticket_attachments", "file_url")


def downgrade() -> None:
    # Add back file_url
    op.add_column(
        "ticket_attachments",
        sa.Column("file_url", sa.Text(), nullable=True),
    )
    
    # Copy data back
    op.execute(
        "UPDATE ticket_attachments SET file_url = file_path"
    )
    
    op.alter_column("ticket_attachments", "file_url", nullable=False)
    
    # Drop new columns
    op.drop_column("ticket_attachments", "filename")
    op.drop_column("ticket_attachments", "original_filename")
    op.drop_column("ticket_attachments", "file_path")
    op.drop_column("ticket_attachments", "file_size")
