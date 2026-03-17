import os
from dotenv import load_dotenv

load_dotenv()  # loads from .env file if present

# ── Database ─────────────────────────────────────────────────────
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://postgres:yourpassword@localhost:5432/business_ai_db"  # change as needed
)

# ── App Settings ─────────────────────────────────────────────────
APP_TITLE = "Business Decision Intelligence System"
APP_VERSION = "1.0.0"
DEBUG = os.getenv("DEBUG", "True") == "True"

# ── ML Settings ──────────────────────────────────────────────────
FORECAST_DEFAULT_PERIODS = 3
ANOMALY_CONTAMINATION = 0.1      # 10% of data assumed anomalous
ISOLATION_FOREST_ESTIMATORS = 100

# ── Upload Settings ───────────────────────────────────────────────
ALLOWED_EXTENSIONS = [".csv"]
REQUIRED_CSV_COLUMNS = {"month", "revenue", "expenses", "marketing_spend", "customer_growth"}