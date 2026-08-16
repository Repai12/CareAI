from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    DATABASE_URL: str = "sqlite:///./careai.db"

    JWT_SECRET: str = "dev-secret-change-me"
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRE_MINUTES: int = 60 * 24

    RESEND_API_KEY: str = ""
    RESEND_FROM_EMAIL: str = "onboarding@resend.dev"

    # Gemini API
    GEMINI_API_KEY: str = ""

    # Member 3 - Daily Safety Check-in
    SAFETY_CHECKIN_TIMEOUT_HOURS: int = 24

    class Config:
        env_file = None


settings = Settings()
