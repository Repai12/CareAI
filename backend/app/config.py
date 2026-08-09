"""
config.py
---------
Central place to read environment variables (DB URL, JWT secret, SendGrid key).
We NEVER hardcode secrets in code - they live in a .env file (which is git-ignored)
and are loaded here using pydantic-settings.
"""

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # PostgreSQL connection string, e.g.
    # postgresql://careai_user:careai_pass@localhost:5432/careai_db
    DATABASE_URL: str

    # Used to sign JWT auth tokens
    JWT_SECRET: str = "dev-secret-change-me"
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRE_MINUTES: int = 60 * 24  # 1 day

   # Resend (Module 2 - Feature 4)
    RESEND_API_KEY: str = ""
    RESEND_FROM_EMAIL: str = "onboarding@resend.dev"

    class Config:
        env_file = ".env"


settings = Settings()
