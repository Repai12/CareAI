"""create application tables

Revision ID: 5c905c544fa2
Revises:
Create Date: 2026-08-16

Safely migrates the existing appointments and medications
tables to match the current SQLAlchemy models.

The existing medication_logs and visit_notes tables are
already present in NeonDB, so this migration intentionally
does NOT recreate them.
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# ============================================================
# REVISION IDENTIFIERS
# ============================================================

revision: str = "5c905c544fa2"
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


# ============================================================
# UPGRADE
# ============================================================

def upgrade() -> None:
    """Safely migrate existing application tables."""


    # ========================================================
    # APPOINTMENTS
    # ========================================================

    # --------------------------------------------------------
    # Add new columns.
    #
    # They are initially nullable because the table already
    # contains an existing appointment.
    # --------------------------------------------------------

    op.add_column(
        "appointments",
        sa.Column(
            "patient_name",
            sa.String(),
            nullable=True,
        ),
    )

    op.add_column(
        "appointments",
        sa.Column(
            "patient_email",
            sa.String(),
            nullable=True,
        ),
    )

    op.add_column(
        "appointments",
        sa.Column(
            "appointment_date",
            sa.Date(),
            nullable=True,
        ),
    )

    op.add_column(
        "appointments",
        sa.Column(
            "start_time",
            sa.Time(),
            nullable=True,
        ),
    )

    op.add_column(
        "appointments",
        sa.Column(
            "end_time",
            sa.Time(),
            nullable=True,
        ),
    )

    op.add_column(
        "appointments",
        sa.Column(
            "reason",
            sa.String(),
            nullable=True,
        ),
    )

    op.add_column(
        "appointments",
        sa.Column(
            "google_event_id",
            sa.String(),
            nullable=True,
        ),
    )


    # --------------------------------------------------------
    # status already exists in NeonDB.
    #
    # We DO NOT create it again.
    # --------------------------------------------------------


    # --------------------------------------------------------
    # Get patient name and email from users table.
    #
    # Existing:
    # appointments.patient_id -> users.id
    #
    # New:
    # appointments.patient_name
    # appointments.patient_email
    # --------------------------------------------------------

    op.execute(
        """
        UPDATE appointments AS a
        SET
            patient_name = u.name,
            patient_email = u.email
        FROM users AS u
        WHERE a.patient_id = u.id
        """
    )


    # --------------------------------------------------------
    # Convert scheduled_at into the new appointment fields.
    #
    # appointment_date = date portion
    # start_time       = time portion
    # end_time         = start + 1 hour
    #
    # Existing appointments are assumed to have a 1-hour
    # duration because the old schema did not store end_time.
    # --------------------------------------------------------

    op.execute(
        """
        UPDATE appointments
        SET
            appointment_date = scheduled_at::date,
            start_time = scheduled_at::time,
            end_time = (scheduled_at + INTERVAL '1 hour')::time
        """
    )


    # --------------------------------------------------------
    # Existing status values are preserved.
    #
    # Only NULL status values are changed to "booked".
    # --------------------------------------------------------

    op.execute(
        """
        UPDATE appointments
        SET status = 'booked'
        WHERE status IS NULL
        """
    )


    # --------------------------------------------------------
    # Make required columns NOT NULL.
    # --------------------------------------------------------

    op.alter_column(
        "appointments",
        "patient_name",
        existing_type=sa.String(),
        nullable=False,
    )

    op.alter_column(
        "appointments",
        "patient_email",
        existing_type=sa.String(),
        nullable=False,
    )

    op.alter_column(
        "appointments",
        "appointment_date",
        existing_type=sa.Date(),
        nullable=False,
    )

    op.alter_column(
        "appointments",
        "start_time",
        existing_type=sa.Time(),
        nullable=False,
    )

    op.alter_column(
        "appointments",
        "end_time",
        existing_type=sa.Time(),
        nullable=False,
    )

    op.alter_column(
        "appointments",
        "status",
        existing_type=sa.String(),
        nullable=False,
    )


    # --------------------------------------------------------
    # Remove old patient foreign key.
    # --------------------------------------------------------

    op.drop_constraint(
        "appointments_patient_id_fkey",
        "appointments",
        type_="foreignkey",
    )


    # --------------------------------------------------------
    # Remove old appointment columns.
    # --------------------------------------------------------

    op.drop_column(
        "appointments",
        "patient_id",
    )

    op.drop_column(
        "appointments",
        "scheduled_at",
    )


    # --------------------------------------------------------
    # Create ID index.
    # --------------------------------------------------------

    op.create_index(
        "ix_appointments_id",
        "appointments",
        ["id"],
        unique=False,
    )


    # ========================================================
    # MEDICATIONS
    # ========================================================

    # --------------------------------------------------------
    # Add medicine_name.
    # --------------------------------------------------------

    op.add_column(
        "medications",
        sa.Column(
            "medicine_name",
            sa.String(),
            nullable=True,
        ),
    )


    # --------------------------------------------------------
    # Add start_date and end_date.
    #
    # The old database does not contain equivalent values,
    # so these will initially be NULL for the existing
    # medication records.
    # --------------------------------------------------------

    op.add_column(
        "medications",
        sa.Column(
            "start_date",
            sa.Date(),
            nullable=True,
        ),
    )

    op.add_column(
        "medications",
        sa.Column(
            "end_date",
            sa.Date(),
            nullable=True,
        ),
    )


    # --------------------------------------------------------
    # Copy old medication name to medicine_name.
    # --------------------------------------------------------

    op.execute(
        """
        UPDATE medications
        SET medicine_name = name
        """
    )


    # medicine_name is required by the current model.

    op.alter_column(
        "medications",
        "medicine_name",
        existing_type=sa.String(),
        nullable=False,
    )


    # --------------------------------------------------------
    # Remove old medication foreign key.
    # --------------------------------------------------------

    op.drop_constraint(
        "medications_patient_id_fkey",
        "medications",
        type_="foreignkey",
    )


    # --------------------------------------------------------
    # Remove old medication columns.
    # --------------------------------------------------------

    op.drop_column(
        "medications",
        "patient_id",
    )

    op.drop_column(
        "medications",
        "name",
    )

    op.drop_column(
        "medications",
        "schedule_time",
    )

    op.drop_column(
        "medications",
        "active",
    )


    # --------------------------------------------------------
    # Create medication ID index.
    # --------------------------------------------------------

    op.create_index(
        "ix_medications_id",
        "medications",
        ["id"],
        unique=False,
    )


    # ========================================================
    # IMPORTANT
    # ========================================================
    #
    # medication_logs already exists in NeonDB.
    #
    # visit_notes already exists in NeonDB.
    #
    # Therefore we intentionally DO NOT call:
    #
    #     op.create_table("medication_logs", ...)
    #
    # or:
    #
    #     op.create_table("visit_notes", ...)
    #
    # ========================================================


# ============================================================
# DOWNGRADE
# ============================================================

def downgrade() -> None:
    """
    Reverse the appointments and medications migration.

    Existing medication_logs and visit_notes are intentionally
    not removed because they existed before this migration.
    """


    # ========================================================
    # MEDICATIONS
    # ========================================================

    # Restore old columns.

    op.add_column(
        "medications",
        sa.Column(
            "name",
            sa.String(),
            nullable=True,
        ),
    )

    op.add_column(
        "medications",
        sa.Column(
            "patient_id",
            sa.UUID(),
            nullable=True,
        ),
    )

    op.add_column(
        "medications",
        sa.Column(
            "schedule_time",
            sa.String(),
            nullable=True,
        ),
    )

    op.add_column(
        "medications",
        sa.Column(
            "active",
            sa.Boolean(),
            nullable=True,
        ),
    )


    # Restore medication name.

    op.execute(
        """
        UPDATE medications
        SET name = medicine_name
        """
    )


    # Remove new index.

    op.drop_index(
        "ix_medications_id",
        table_name="medications",
    )


    # Remove new columns.

    op.drop_column(
        "medications",
        "medicine_name",
    )

    op.drop_column(
        "medications",
        "start_date",
    )

    op.drop_column(
        "medications",
        "end_date",
    )


    # ========================================================
    # APPOINTMENTS
    # ========================================================

    # Restore old columns.

    op.add_column(
        "appointments",
        sa.Column(
            "patient_id",
            sa.UUID(),
            nullable=True,
        ),
    )

    op.add_column(
        "appointments",
        sa.Column(
            "scheduled_at",
            sa.DateTime(),
            nullable=True,
        ),
    )


    # Reconstruct scheduled_at.

    op.execute(
        """
        UPDATE appointments
        SET scheduled_at =
            appointment_date + start_time
        WHERE appointment_date IS NOT NULL
          AND start_time IS NOT NULL
        """
    )


    # Remove new appointment index.

    op.drop_index(
        "ix_appointments_id",
        table_name="appointments",
    )


    # Remove new columns.

    op.drop_column(
        "appointments",
        "patient_name",
    )

    op.drop_column(
        "appointments",
        "patient_email",
    )

    op.drop_column(
        "appointments",
        "appointment_date",
    )

    op.drop_column(
        "appointments",
        "start_time",
    )

    op.drop_column(
        "appointments",
        "end_time",
    )

    op.drop_column(
        "appointments",
        "reason",
    )

    op.drop_column(
        "appointments",
        "google_event_id",
    )


    # --------------------------------------------------------
    # NOTE:
    #
    # status was already present before this migration,
    # so it remains untouched.
    # --------------------------------------------------------