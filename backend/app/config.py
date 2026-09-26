import os

from dotenv import load_dotenv

load_dotenv()

GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
GROQ_MODEL = os.getenv("GROQ_MODEL", "openai/gpt-oss-20b")
MYSQL_URL = os.getenv("MYSQL_URL", "")
DATABASE_URL = MYSQL_URL or os.getenv("DATABASE_URL", "")

DEFAULT_CORS_ORIGINS = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "https://gracious-enjoyment-production-524c.up.railway.app",
]

_cors_origins = os.getenv("CORS_ORIGINS", "")
_extra_cors_origins = [origin.strip() for origin in _cors_origins.split(",") if origin.strip()]
CORS_ORIGINS = list(dict.fromkeys([*DEFAULT_CORS_ORIGINS, *_extra_cors_origins]))
