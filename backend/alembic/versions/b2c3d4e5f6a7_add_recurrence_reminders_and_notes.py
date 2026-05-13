"""add recurrence, reminder_sent, and task_notes table

Revision ID: b2c3d4e5f6a7
Revises: f4e4ae5cab83
Create Date: 2026-05-13 00:00:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = 'b2c3d4e5f6a7'
down_revision: Union[str, None] = 'f4e4ae5cab83'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('tasks', sa.Column('recurrence', sa.String(), nullable=False, server_default='none'))
    op.add_column('tasks', sa.Column('reminder_sent', sa.Boolean(), nullable=False, server_default='false'))

    op.create_table(
        'task_notes',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('task_id', sa.Integer(), nullable=False),
        sa.Column('owner_id', sa.Integer(), nullable=False),
        sa.Column('content', sa.String(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.ForeignKeyConstraint(['owner_id'], ['users.id']),
        sa.ForeignKeyConstraint(['task_id'], ['tasks.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_task_notes_id', 'task_notes', ['id'])


def downgrade() -> None:
    op.drop_index('ix_task_notes_id', table_name='task_notes')
    op.drop_table('task_notes')
    op.drop_column('tasks', 'reminder_sent')
    op.drop_column('tasks', 'recurrence')
