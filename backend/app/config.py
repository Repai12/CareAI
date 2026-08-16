from pydantic_settings import BaseSettings

from pydantic_settings import BaseSettings, SettingsConfigDict
class Settings(BaseSettings):
    DATABASE_URL: str 

    JWT_SECRET: str = "dev-secret-change-me"
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRE_MINUTES: int = 60 * 24

    RESEND_API_KEY: str = ""
    RESEND_FROM_EMAIL: str = "onboarding@resend.dev"

    # Gemini API
    GEMINI_API_KEY: str = ""

    # Member 3 - Daily Safety Check-in
    SAFETY_CHECKIN_TIMEOUT_HOURS: int = 24

    # Member 1 (Mubasshira) - Groq API for Report Analyzer / Symptom Checker / Diet
    GROQ_API_KEY: str = ""

    model_config = SettingsConfigDict(
        env_file=".env",
        extra="ignore"
    )