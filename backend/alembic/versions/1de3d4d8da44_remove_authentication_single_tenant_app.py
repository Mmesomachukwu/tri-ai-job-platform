"""remove authentication - single-tenant app

Revision ID: 1de3d4d8da44
Revises: c81ab067c486
Create Date: 2026-09-18 03:58:58.843988

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '1de3d4d8da44'
down_revision: Union[str, None] = 'c81ab067c486'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Drop the FK-bearing columns first, then the users table itself -
    # autogenerate ordered this backwards, which fails against a real
    # Postgres FK constraint (DependentObjectsStillExist).
    op.drop_index('ix_analyses_user_id', table_name='analyses')
    op.drop_constraint('analyses_user_id_fkey', 'analyses', type_='foreignkey')
    op.drop_column('analyses', 'user_id')
    op.drop_index('ix_resumes_user_id', table_name='resumes')
    op.drop_constraint('resumes_user_id_fkey', 'resumes', type_='foreignkey')
    op.drop_column('resumes', 'user_id')
    op.drop_index('ix_saved_jobs_user_id', table_name='saved_jobs')
    op.drop_constraint('saved_jobs_user_id_fkey', 'saved_jobs', type_='foreignkey')
    op.drop_column('saved_jobs', 'user_id')
    op.drop_index('ix_users_email', table_name='users')
    op.drop_table('users')


def downgrade() -> None:
    # Recreate users table first, then add back the FK-bearing columns -
    # again, reversed from autogenerate's order to avoid referencing a
    # table that doesn't exist yet.
    op.create_table('users',
    sa.Column('id', sa.VARCHAR(), autoincrement=False, nullable=False),
    sa.Column('name', sa.VARCHAR(), autoincrement=False, nullable=False),
    sa.Column('email', sa.VARCHAR(), autoincrement=False, nullable=False),
    sa.Column('password_hash', sa.VARCHAR(), autoincrement=False, nullable=False),
    sa.Column('created_at', postgresql.TIMESTAMP(), autoincrement=False, nullable=True),
    sa.Column('updated_at', postgresql.TIMESTAMP(), autoincrement=False, nullable=True),
    sa.PrimaryKeyConstraint('id', name='users_pkey')
    )
    op.create_index('ix_users_email', 'users', ['email'], unique=True)

    op.add_column('saved_jobs', sa.Column('user_id', sa.VARCHAR(), autoincrement=False, nullable=False))
    op.create_foreign_key('saved_jobs_user_id_fkey', 'saved_jobs', 'users', ['user_id'], ['id'])
    op.create_index('ix_saved_jobs_user_id', 'saved_jobs', ['user_id'], unique=False)
    op.add_column('resumes', sa.Column('user_id', sa.VARCHAR(), autoincrement=False, nullable=False))
    op.create_foreign_key('resumes_user_id_fkey', 'resumes', 'users', ['user_id'], ['id'])
    op.create_index('ix_resumes_user_id', 'resumes', ['user_id'], unique=False)
    op.add_column('analyses', sa.Column('user_id', sa.VARCHAR(), autoincrement=False, nullable=False))
    op.create_foreign_key('analyses_user_id_fkey', 'analyses', 'users', ['user_id'], ['id'])
    op.create_index('ix_analyses_user_id', 'analyses', ['user_id'], unique=False)
