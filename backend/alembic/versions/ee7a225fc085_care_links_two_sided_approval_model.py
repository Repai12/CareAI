"""care_links two-sided approval model

Revision ID: ee7a225fc085
Revises: 6426cf84a54e
Create Date: 2026-08-20 03:31:43.230406

Replaces `patient_links` (bare patient_id/viewer_id/relationship_label,
no status at all - any row meant instant, permanent access) with
`care_links`, adding the fields README S4.1 specs: link_role,
permission_level, status (pending/active/declined/revoked), invited_by,
and response/revocation timestamps. This is what makes the two-sided
approval flow possible - previously registering with someone's
patient_code granted access immediately, which is exactly the
auto-active-on-redemption anti-pattern flagged as a known gap (S13):
anyone with a leaked/guessed code could silently attach themselves to a
patient's medical data.

Copies rows rather than a plain ALTER TABLE ... RENAME, and deliberately
does NOT gate that copy on "care_links doesn't exist yet": app/main.py's
Base.metadata.create_all() runs on every app import/startup and will
happily create an empty `care_links` table (it now matches the current
model) before this migration ever runs, if a teammate's workflow starts
the app first. A rename-only-if-absent guard would then silently skip
over real patient_links data forever, orphaning existing family/doctor
connections. Copying by matching primary key instead means this is safe
and idempotent regardless of which ran first, or how many times this
migration itself is re-run.
"""
from typing import Sequence, Union

from alembic import op


# revision identifiers, used by Alembic.
revision: str = 'ee7a225fc085'
down_revision: Union[str, Sequence[str], None] = '6426cf84a54e'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Full target shape, for the case where care_links doesn't exist at all yet.
    op.execute("""
        CREATE TABLE IF NOT EXISTS care_links (
            id UUID PRIMARY KEY,
            patient_id UUID NOT NULL REFERENCES users(id),
            viewer_id UUID NOT NULL REFERENCES users(id),
            link_role VARCHAR NOT NULL,
            relationship_label VARCHAR,
            permission_level VARCHAR NOT NULL,
            status VARCHAR NOT NULL,
            invited_by UUID REFERENCES users(id),
            created_at TIMESTAMP,
            responded_at TIMESTAMP,
            revoked_at TIMESTAMP
        )
    """)

    # New columns, for the case where care_links already existed (e.g.
    # created empty by create_all()) but is missing some of these.
    op.execute("ALTER TABLE care_links ADD COLUMN IF NOT EXISTS link_role VARCHAR")
    op.execute("ALTER TABLE care_links ADD COLUMN IF NOT EXISTS permission_level VARCHAR")
    op.execute("ALTER TABLE care_links ADD COLUMN IF NOT EXISTS status VARCHAR")
    op.execute("ALTER TABLE care_links ADD COLUMN IF NOT EXISTS invited_by UUID REFERENCES users(id)")
    op.execute("ALTER TABLE care_links ADD COLUMN IF NOT EXISTS created_at TIMESTAMP")
    op.execute("ALTER TABLE care_links ADD COLUMN IF NOT EXISTS responded_at TIMESTAMP")
    op.execute("ALTER TABLE care_links ADD COLUMN IF NOT EXISTS revoked_at TIMESTAMP")

    # Copy every patient_links row not already represented in care_links
    # (matched by id, so this is a no-op on a second run), backfilling
    # the new columns as `active` - these rows represent access that was
    # already granted and in use under the old always-on behavior, and
    # silently demoting it to `pending` would revoke working connections
    # as a side effect of a migration, which is its own kind of surprise.
    op.execute("""
        DO $$
        BEGIN
            IF EXISTS (SELECT FROM information_schema.tables WHERE table_name = 'patient_links') THEN
                INSERT INTO care_links (
                    id, patient_id, viewer_id, link_role, relationship_label,
                    permission_level, status, created_at
                )
                SELECT
                    pl.id, pl.patient_id, pl.viewer_id,
                    COALESCE(pl.relationship_label, 'family'),
                    pl.relationship_label,
                    CASE WHEN COALESCE(pl.relationship_label, 'family') = 'doctor'
                         THEN 'view_and_manage' ELSE 'view_only' END,
                    'active',
                    now()
                FROM patient_links pl
                WHERE NOT EXISTS (SELECT 1 FROM care_links cl WHERE cl.id = pl.id);

                DROP TABLE patient_links;
            END IF;
        END $$;
    """)

    # Defensive backfill for any other NULLs, then lock in NOT NULL.
    op.execute("""
        UPDATE care_links SET
            link_role = COALESCE(link_role, relationship_label, 'family'),
            permission_level = COALESCE(
                permission_level,
                CASE WHEN COALESCE(relationship_label, 'family') = 'doctor'
                     THEN 'view_and_manage' ELSE 'view_only' END
            ),
            status = COALESCE(status, 'active'),
            created_at = COALESCE(created_at, now())
        WHERE link_role IS NULL OR permission_level IS NULL OR status IS NULL OR created_at IS NULL
    """)
    op.execute("ALTER TABLE care_links ALTER COLUMN link_role SET NOT NULL")
    op.execute("ALTER TABLE care_links ALTER COLUMN permission_level SET NOT NULL")
    op.execute("ALTER TABLE care_links ALTER COLUMN status SET NOT NULL")

    op.execute("CREATE INDEX IF NOT EXISTS ix_care_links_patient_id ON care_links (patient_id)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_care_links_viewer_id ON care_links (viewer_id)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_care_links_status ON care_links (status)")


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS ix_care_links_status")
    op.execute("DROP INDEX IF EXISTS ix_care_links_viewer_id")
    op.execute("DROP INDEX IF EXISTS ix_care_links_patient_id")
    op.execute("""
        CREATE TABLE IF NOT EXISTS patient_links (
            id UUID PRIMARY KEY,
            patient_id UUID NOT NULL,
            viewer_id UUID NOT NULL,
            relationship_label VARCHAR
        )
    """)
    op.execute("""
        INSERT INTO patient_links (id, patient_id, viewer_id, relationship_label)
        SELECT id, patient_id, viewer_id, relationship_label FROM care_links
        WHERE NOT EXISTS (SELECT 1 FROM patient_links pl WHERE pl.id = care_links.id)
    """)
    op.execute("DROP TABLE care_links")
