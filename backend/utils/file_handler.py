import pandas as pd
import numpy as np
from io import BytesIO
from sqlalchemy import text
from database.db_config import engine
from config import REQUIRED_CSV_COLUMNS

# ── Column name aliases ───────────────────────────────────────────
# Maps common alternate column names to our standard names.
# This allows different business profiles to upload their CSVs.
COLUMN_ALIASES = {
    # month
    "date": "month",
    "period": "month",
    "month_name": "month",
    "time": "month",

    # revenue
    "sales": "revenue",
    "income": "revenue",
    "total_sales": "revenue",
    "gross_revenue": "revenue",
    "turnover": "revenue",

    # expenses
    "costs": "expenses",
    "cost": "expenses",
    "expenditure": "expenses",
    "total_expenses": "expenses",
    "overhead": "expenses",
    "operational_cost": "expenses",

    # marketing_spend
    "marketing": "marketing_spend",
    "ads": "marketing_spend",
    "advertising": "marketing_spend",
    "promotion": "marketing_spend",
    "ad_spend": "marketing_spend",
    "marketing_budget": "marketing_spend",

    # customer_growth
    "customers": "customer_growth",
    "new_customers": "customer_growth",
    "clients_gained": "customer_growth",
    "growth": "customer_growth",
    "customer_increase": "customer_growth",
    "user_growth": "customer_growth",
}

MAX_FILE_SIZE_MB = 10
MAX_FILE_SIZE_BYTES = MAX_FILE_SIZE_MB * 1024 * 1024


def clean_currency(value):
    """
    Handles values like rupees 1,20,000 or $1,200.50 or 1.2L.
    Strips currency symbols, commas, spaces and converts to float.
    """
    if pd.isna(value):
        return np.nan
    s = str(value).strip()
    s = s.replace('\u20b9', '').replace('$', '').replace('\u00a3', '').replace('\u20ac', '').replace(' ', '')
    s = s.replace(',', '')
    if s.endswith('L') or s.endswith('l'):
        try: return float(s[:-1]) * 100000
        except: return np.nan
    if s.endswith('K') or s.endswith('k'):
        try: return float(s[:-1]) * 1000
        except: return np.nan
    if s.endswith('M') or s.endswith('m'):
        try: return float(s[:-1]) * 1000000
        except: return np.nan
    try:
        return float(s)
    except:
        return np.nan


def validate_and_clean(file_bytes: bytes) -> tuple:
    """
    Full validation and cleaning pipeline.

    Returns:
        df       : Cleaned DataFrame ready for DB insert
        warnings : List of non-fatal warning messages to show the user

    Raises:
        ValueError: On fatal errors (wrong file, missing columns, empty data)
    """
    warnings = []

    # ── 1. File size check ───────────────────────────────────────
    if len(file_bytes) > MAX_FILE_SIZE_BYTES:
        raise ValueError(f"File too large. Maximum allowed size is {MAX_FILE_SIZE_MB}MB.")

    # ── 2. Parse CSV ─────────────────────────────────────────────
    try:
        df = pd.read_csv(BytesIO(file_bytes))
    except Exception as e:
        raise ValueError(f"Could not read CSV file. Make sure it is a valid CSV. Error: {str(e)}")

    if df.empty:
        raise ValueError("The uploaded CSV file is empty.")

    # ── 3. Normalize column names ─────────────────────────────────
    df.columns = [c.strip().lower().replace(' ', '_') for c in df.columns]

    # ── 4. Apply column aliases (support different business profiles)
    df.rename(columns=COLUMN_ALIASES, inplace=True)

    # ── 5. Check required columns ─────────────────────────────────
    missing = REQUIRED_CSV_COLUMNS - set(df.columns)
    if missing:
        raise ValueError(
            f"Missing required columns: {missing}. "
            f"Your CSV has: {set(df.columns)}. "
            f"Required: {REQUIRED_CSV_COLUMNS}."
        )

    # ── 6. Keep only required columns ─────────────────────────────
    df = df[list(REQUIRED_CSV_COLUMNS)].copy()

    # ── 7. Drop fully empty rows ──────────────────────────────────
    before = len(df)
    df.dropna(how='all', inplace=True)
    dropped = before - len(df)
    if dropped > 0:
        warnings.append(f"{dropped} completely empty row(s) were removed.")

    if df.empty:
        raise ValueError("No valid data rows found after removing empty rows.")

    # ── 8. Validate month column ──────────────────────────────────
    missing_months = df['month'].isna().sum()
    if missing_months > 0:
        warnings.append(f"{missing_months} row(s) had missing month values and were removed.")
        df = df[df['month'].notna()]

    df['month'] = df['month'].astype(str).str.strip()
    blank_months = (df['month'] == '') | (df['month'] == 'nan') | (df['month'] == '0')
    if blank_months.sum() > 0:
        warnings.append(f"{blank_months.sum()} row(s) had blank month values and were removed.")
        df = df[~blank_months]

    if df.empty:
        raise ValueError("No valid rows remain after month validation.")

    # ── 9. Clean numeric columns (handles currency symbols, commas, L/K/M)
    numeric_cols = ['revenue', 'expenses', 'marketing_spend', 'customer_growth']
    for col in numeric_cols:
        original = df[col].copy()
        df[col] = df[col].apply(clean_currency)
        failed = df[col].isna() & original.notna()
        if failed.sum() > 0:
            warnings.append(
                f"{failed.sum()} value(s) in '{col}' could not be converted and were set to 0."
            )
        df[col] = df[col].fillna(0).astype(float)

    # ── 10. Negative value check ──────────────────────────────────
    for col in ['revenue', 'expenses', 'marketing_spend']:
        neg_count = (df[col] < 0).sum()
        if neg_count > 0:
            warnings.append(
                f"{neg_count} negative value(s) found in '{col}'. "
                "These have been kept but may affect ML results."
            )

    # ── 11. Duplicate month check ─────────────────────────────────
    dupes = df.duplicated(subset=['month'], keep='last')
    dupe_count = dupes.sum()
    if dupe_count > 0:
        warnings.append(
            f"{dupe_count} duplicate month(s) found. Keeping the last occurrence of each."
        )
        df = df.drop_duplicates(subset=['month'], keep='last')

    # ── 12. Final reset ───────────────────────────────────────────
    df.reset_index(drop=True, inplace=True)

    return df, warnings


def insert_dataframe(df: pd.DataFrame) -> int:
    """
    Bulk inserts cleaned DataFrame into business_data table.
    Uses pandas to_sql for speed — much faster than row-by-row.
    Returns number of rows inserted.
    """
    rows_to_insert = df[['month', 'revenue', 'expenses', 'marketing_spend', 'customer_growth']]

    rows_to_insert.to_sql(
        name='business_data',
        con=engine,
        if_exists='append',
        index=False,
        method='multi',
        chunksize=500,
    )

    return len(rows_to_insert)