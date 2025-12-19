import os
from dotenv import load_dotenv
load_dotenv()
from pathlib import Path
import os

BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")  # 👈 EXPLICIT PATH

class Settings:
    # App info
    APP_NAME = "Accesco Chatbot"
    ENV = os.getenv("ENV", "development")
    DB_USER=os.getenv("DB_USER")
    DB_PASSWORD=os.getenv("DB_PASSWORD")
    DB_HOST=os.getenv("DB_HOST")
    DB_PORT=os.getenv("DB_PORT","5432")
    DB_NAME=os.getenv("DB_NAME","postgres")
    # Database (Supabase / Render / Local)
    DATABASE_URL =(f"postgresql+psycopg2://{DB_USER}:{DB_PASSWORD}"
    f"@{DB_HOST}:{DB_PORT}/{DB_NAME}")

    # Security (optional, future use)
    SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret")

settings = Settings()
print("DB_HOST =", os.getenv("DB_HOST"))