"""add reservations constraints

Revision ID: a9ea6d4aa1f3
Revises: 00b5402309b5
Create Date: 2025-11-17 13:47:51.690188

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a9ea6d4aa1f3'
down_revision: Union[str, Sequence[str], None] = '00b5402309b5'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("""
        ALTER TABLE reservations
        ADD CONSTRAINT ck_reservations_dates
        CHECK (return_date IS NULL OR return_date >= reserve_date)
    """)
    
    op.execute("""
        CREATE UNIQUE INDEX uq_reservations_active_user_book
        ON reservations (user_id, book_id)
        WHERE status = 'active'
    """)


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS uq_reservations_active_user_book")
    op.execute("ALTER TABLE reservations DROP CONSTRAINT IF EXISTS ck_reservations_dates")
