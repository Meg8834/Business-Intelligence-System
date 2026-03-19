import os
from dotenv import load_dotenv

load_dotenv()

# ── Database ──────────────────────────────────────────────────────
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://postgres:yourpassword@localhost:5432/business_ai_db"
)

# ── App ───────────────────────────────────────────────────────────
APP_TITLE   = "Business Decision Intelligence System"
APP_VERSION = "2.0.0"
DEBUG       = os.getenv("DEBUG", "True") == "True"

# ── ML ────────────────────────────────────────────────────────────
FORECAST_DEFAULT_PERIODS    = 3
ANOMALY_CONTAMINATION       = 0.1
ISOLATION_FOREST_ESTIMATORS = 100

# ── Upload ────────────────────────────────────────────────────────
ALLOWED_EXTENSIONS   = [".csv"]
REQUIRED_CSV_COLUMNS = {"month", "revenue", "expenses", "marketing_spend", "customer_growth"}

# ── Email ─────────────────────────────────────────────────────────
EMAIL_HOST     = os.getenv("EMAIL_HOST", "smtp.gmail.com")
EMAIL_PORT     = int(os.getenv("EMAIL_PORT", "587"))
EMAIL_USER     = os.getenv("EMAIL_USER", "your_email@gmail.com")
EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD", "your_app_password")

# ── OpenAI ────────────────────────────────────────────────────────
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")

# ── JWT Auth ──────────────────────────────────────────────────────
JWT_SECRET          = os.getenv("JWT_SECRET", "your_super_secret_jwt_key_change_this")
JWT_ALGORITHM       = "HS256"
JWT_EXPIRE_MINUTES  = int(os.getenv("JWT_EXPIRE_MINUTES", "1440"))  # 24 hours