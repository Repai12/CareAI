"""add auth verification and refresh token support

Revision ID: 6426cf84a54e
Revises: 5c905c544fa2
Create Date: 2026-08-20 03:12:57.833524

Brings `users` and the new `refresh_tokens` table under Alembic for the
first time. Every other shared table (vitals_logs, notifications, etc.)
is still created by app/main.py's Base.metadata.create_all() and does
NOT need a migration - that's fine for a brand-new table, but it cannot
add columns to a table that already exists, which is exactly what this
change needs to do to `users` (is_verified, verification_token, reset
tokens). Hence the first real migration for a table outside Member 2's
original medications/appointments scope - see the updated comment in
alembic/env.py's include_object().

Written with IF NOT EXISTS / IF EXISTS guards throughout so it's safe to
run regardless of whether a given database already has `users` from an
earlier create_all() (most teammates' existing dev DBs) or not (a
genuinely fresh database, where `alembic upgrade head` runs before
`users` has ever been created) - both end up at the same final shape.
"""
from typing import Sequence, Union

from alembic import op


# revision identifiers, used by Alembic.
revision: str = '6426cf84a54e'
down_revision: Union[str, Sequence[str], None] = '5c905c544fa2'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Full shape, for the case where `users` doesn't exist yet at all.
    op.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id UUID PRIMARY KEY,
            name VARCHAR NOT NULL,
            email VARCHAR NOT NULL UNIQUE,
            hashed_password VARCHAR NOT NULL,
            role VARCHAR NOT NULL,
            patient_code VARCHAR UNIQUE,
            is_verified BOOLEAN NOT NULL DEFAULT FALSE,
            verification_token VARCHAR,
            verification_token_expires_at TIMESTAMP,
            reset_token VARCHAR,
            reset_token_expires_at TIMESTAMP,
            created_at TIMESTAMP
        )
    """)
    op.execute("CREATE INDEX IF NOT EXISTS ix_users_email ON users (email)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_users_patient_code ON users (patient_code)")

    # For the case where `users` already existed (pre-dating this
    # migration) and just needs the new auth columns added.
    op.execute("ALTER TABLE users ADD COLUMN IF NOT EXISTS is_verified BOOLEAN NOT NULL DEFAULT FALSE")
    op.execute("ALTER TABLE users ADD COLUMN IF NOT EXISTS verification_token VARCHAR")
    op.execute("ALTER TABLE users ADD COLUMN IF NOT EXISTS verification_token_expires_at TIMESTAMP")
    op.execute("ALTER TABLE users ADD COLUMN IF NOT EXISTS reset_token VARCHAR")
    op.execute("ALTER TABLE users ADD COLUMN IF NOT EXISTS reset_token_expires_at TIMESTAMP")
    op.execute("CREATE INDEX IF NOT EXISTS ix_users_verification_token ON users (verification_token)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_users_reset_token ON users (reset_token)")

    op.execute("""
        CREATE TABLE IF NOT EXISTS refresh_tokens (
            id UUID PRIMARY KEY,
            user_id UUID NOT NULL REFERENCES users(id),
            token_hash VARCHAR NOT NULL UNIQUE,
            expires_at TIMESTAMP NOT NULL,
            revoked_at TIMESTAMP,
            created_at TIMESTAMP
        )
    """)
    op.execute("CREATE INDEX IF NOT EXISTS ix_refresh_tokens_user_id ON refresh_tokens (user_id)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_refresh_tokens_token_hash ON refresh_tokens (token_hash)")


def downgrade() -> None:
    op.execute("DROP TABLE IF EXISTS refresh_tokens")
    op.execute("ALTER TABLE users DROP COLUMN IF EXISTS reset_token_expires_at")
    op.execute("ALTER TABLE users DROP COLUMN IF EXISTS reset_token")
    op.execute("ALTER TABLE users DROP COLUMN IF EXISTS verification_token_expires_at")
    op.execute("ALTER TABLE users DROP COLUMN IF EXISTS verification_token")
    op.execute("ALTER TABLE users DROP COLUMN IF EXISTS is_verified")
