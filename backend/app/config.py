"""
config.py
---------
SHARED FILE - do not restructure without telling the team.
Central place to read environment variables. Every teammate's DATABASE_URL
should point to the SAME shared Neon Postgres instance (see README) so
everyone works against live, shared data instead of isolated local copies.
"""

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    DATABASE_URL: str

    JWT_SECRET: str = "dev-secret-change-me"
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRE_MINUTES: int = 60 * 24

    # Member 4 (Repai) - email provider for weekly reports
    RESEND_API_KEY: str = ""
    RESEND_FROM_EMAIL: str = "onboarding@resend.dev"

    class Config:
        env_file = ".env"


settings = Settings()
