"""add search_events table

Revision ID: 9039df349c31
Revises: d97ea1c1b2fd
Create Date: 2026-01-08 19:36:47.645848

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '9039df349c31'
down_revision: Union[str, Sequence[str], None] = 'd97ea1c1b2fd'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Создаём таблицу search_events
    op.create_table(
        'search_events',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('genre_id', sa.Integer(), nullable=True),
        sa.Column('author_id', sa.Integer(), nullable=True),
        sa.Column('query_text', sa.String(length=511), nullable=True),
        sa.Column('created_at', sa.Date(), server_default=sa.text("TIMEZONE('utc', now())"), nullable=False),
        sa.ForeignKeyConstraint(['author_id'], ['authors.id'], name=op.f('fk_search_events_author_id_authors'), ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['genre_id'], ['genres.id'], name=op.f('fk_search_events_genre_id_genres'), ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], name=op.f('fk_search_events_user_id_users'), ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id', name=op.f('pk_search_events'))
    )
    
    # Изменяем server_default для reservations.reserve_date
    op.alter_column('reservations', 'reserve_date',
               existing_type=sa.DATE(),
               server_default=sa.text("TIMEZONE('utc', now())"),
               existing_nullable=False)
    
    # Удаляем старый уникальный индекс
    op.drop_index(op.f('uq_reservations_active_user_book'), table_name='reservations', postgresql_where="((status)::text = 'active'::text)")


def downgrade() -> None:
    """Downgrade schema."""
    # Создаём обратно уникальный индекс
    op.create_index(op.f('uq_reservations_active_user_book'), 'reservations', ['user_id', 'book_id'], unique=True, postgresql_where="((status)::text = 'active'::text)")
    
    # Возвращаем старый server_default для reservations.reserve_date
    op.alter_column('reservations', 'reserve_date',
               existing_type=sa.DATE(),
               server_default=sa.text('CURRENT_DATE'),
               existing_nullable=False)
    
    # Удаляем таблицу search_events
    op.drop_table('search_events')
