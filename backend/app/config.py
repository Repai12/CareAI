from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    DATABASE_URL: str = "sqlite:///./careai.db"

    JWT_SECRET: str = "dev-secret-change-me"
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRE_MINUTES: int = 60 * 24

    RESEND_API_KEY: str = ""
    RESEND_FROM_EMAIL: str = "onboarding@resend.dev"

    # Member 4 (Repai) - Gemini API for Doctor AI Patient Summary (Module 3/7)
    GEMINI_API_KEY: str = ""

    class Config:
        env_file = None


settings = Settings()