import os

from dotenv import load_dotenv

load_dotenv()

GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
GROQ_MODEL = os.getenv("GROQ_MODEL", "openai/gpt-oss-20b")
DATABASE_URL = os.getenv("DATABASE_URL", "")

_cors_origins = os.getenv("CORS_ORIGINS") or "http://localhost:5173,http://127.0.0.1:5173"
CORS_ORIGINS = [origin.strip() for origin in _cors_origins.split(",") if origin.strip()]
