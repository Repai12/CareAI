import os
import sys
from logging.config import fileConfig

from dotenv import load_dotenv
from sqlalchemy import engine_from_config
from sqlalchemy import pool
from alembic import context


# ============================================================
# ADD BACKEND DIRECTORY TO PYTHON PATH
# ============================================================

sys.path.insert(
    0,
    os.path.abspath(
        os.path.join(
            os.path.dirname(__file__),
            ".."
        )
    )
)


# ============================================================
# IMPORT APPLICATION
# ============================================================

from app.database import Base
from app import models


# ============================================================
# LOAD ENVIRONMENT VARIABLES
# ============================================================

load_dotenv(
    os.path.join(
        os.path.dirname(__file__),
        "..",
        ".env"
    )
)

DATABASE_URL = os.getenv("DATABASE_URL")


# ============================================================
# ALEMBIC CONFIGURATION
# ============================================================

config = context.config

if DATABASE_URL:
    config.set_main_option(
        "sqlalchemy.url",
        DATABASE_URL.replace("%", "%%")
    )


# ============================================================
# LOGGING
# ============================================================

if config.config_file_name is not None:
    fileConfig(config.config_file_name)


# ============================================================
# SQLALCHEMY METADATA
# ============================================================

target_metadata = Base.metadata


# ============================================================
# TABLE FILTER
# ============================================================

def include_object(
    object,
    name,
    type_,
    reflected,
    compare_to
):
    """
    Tell Alembic which tables it should manage.

    This project shares the NeonDB database with other modules.
    Therefore, Alembic must NOT delete or modify tables belonging
    to other modules.

    Tables managed by this module:
        - medications
        - appointments
        - medication_logs
        - visit_notes
    """

    managed_tables = {
        "medications",
        "appointments",
        "medication_logs",
        "visit_notes",
    }

    # Only allow these tables to be considered by Alembic.
    if type_ == "table":
        if name not in managed_tables:
            return False

    return True


# ============================================================
# OFFLINE MIGRATIONS
# ============================================================

def run_migrations_offline() -> None:
    """Run migrations in offline mode."""

    url = config.get_main_option("sqlalchemy.url")

    context.configure(
        url=url,
        target_metadata=target_metadata,
        include_object=include_object,
        literal_binds=True,
        dialect_opts={
            "paramstyle": "named"
        },
    )

    with context.begin_transaction():
        context.run_migrations()


# ============================================================
# ONLINE MIGRATIONS
# ============================================================

def run_migrations_online() -> None:
    """Run migrations in online mode."""

    connectable = engine_from_config(
        config.get_section(
            config.config_ini_section,
            {}
        ),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:

        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            include_object=include_object,
        )

        with context.begin_transaction():
            context.run_migrations()


# ============================================================
# RUN MIGRATIONS
# ============================================================

if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()