import os
from dotenv import load_dotenv

load_dotenv()

class Settings:
    PROJECT_NAME: str = "LogiFlow Logistics API"
    PROJECT_DESCRIPTION: str = "Backend REST API for LogiFlow Customer Chatbot powered by Workora AI Employee"
    VERSION: str = "1.0.0"
    
    DATABASE_URL: str = os.getenv(
        "DATABASE_URL",
        "sqlite:///./logiflow.db"  # Fallback to local SQLite if PostgreSQL is not specified
    )
    SECRET_KEY: str = os.getenv(
        "JWT_SECRET_KEY",
        os.getenv("SECRET_KEY", "workora_secure_demo_jwt_secret_key_2026")
    )
    ALGORITHM: str = os.getenv("ALGORITHM", "HS256")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "1440"))
    FRONTEND_URL: str = os.getenv("FRONTEND_URL", "http://localhost:3000")

settings = Settings()
