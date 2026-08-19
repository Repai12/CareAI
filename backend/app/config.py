from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    DATABASE_URL: str
    JWT_SECRET: str = "dev-secret-change-me"
    JWT_ALGORITHM: str = "HS256"
    # Short-lived per README S3.2 ("~15 min"). Frontend is expected to
    # silently call /auth/refresh using the longer-lived refresh cookie.
    JWT_EXPIRE_MINUTES: int = 15
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    # Where verify-email/:token and reset-password/:token links point.
    FRONTEND_URL: str = "http://localhost:3000"
    RESEND_API_KEY: str = ""
    RESEND_FROM_EMAIL: str = "onboarding@resend.dev"
    # Gemini API
    GEMINI_API_KEY: str = ""
    # Member 3 - Daily Safety Check-in
    SAFETY_CHECKIN_TIMEOUT_HOURS: int = 24
    # Member 1 (Mubasshira) - Groq API for Report Analyzer / Symptom Checker / Diet
    GROQ_API_KEY: str = ""
    TWILIO_ACCOUNT_SID: str = ""
    TWILIO_AUTH_TOKEN: str = ""
    TWILIO_PHONE_NUMBER: str = ""

    model_config = SettingsConfigDict(
        env_file=".env",
        extra="ignore"
    )


settings = Settings()
