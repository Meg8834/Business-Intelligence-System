import pandas as pd
from io import BytesIO
from sqlalchemy import text
from database.db_config import engine

REQUIRED_COLUMNS = {"month", "revenue", "expenses", "marketing_spend", "customer_growth"}


def validate_and_clean(file_bytes: bytes) -> pd.DataFrame:
    """
    Reads CSV bytes, validates required columns,
    cleans nulls, and enforces correct types.
    Raises ValueError on bad input.
    """
    df = pd.read_csv(BytesIO(file_bytes))

    # Normalise column names (strip whitespace, lowercase)
    df.columns = [c.strip().lower() for c in df.columns]

    missing = REQUIRED_COLUMNS - set(df.columns)
    if missing:
        raise ValueError(f"Missing required columns: {missing}")

    # Keep only required columns
    df = df[list(REQUIRED_COLUMNS)]

    # Drop rows where ALL values are null
    df.dropna(how="all", inplace=True)

    # Fill remaining nulls with 0
    df.fillna(0, inplace=True)

    # Enforce numeric types for all except month
    numeric_cols = ["revenue", "expenses", "marketing_spend", "customer_growth"]
    for col in numeric_cols:
        df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)

    # month → string, strip whitespace
    df["month"] = df["month"].astype(str).str.strip()

    return df


def insert_dataframe(df: pd.DataFrame) -> int:
    """
    Inserts cleaned DataFrame rows into business_data table.
    Returns number of rows inserted.
    """
    rows_inserted = 0
    with engine.connect() as conn:
        for _, row in df.iterrows():
            conn.execute(
                text(
                    """
                    INSERT INTO business_data (month, revenue, expenses, marketing_spend, customer_growth)
                    VALUES (:month, :revenue, :expenses, :marketing_spend, :customer_growth)
                    """
                ),
                {
                    "month": row["month"],
                    "revenue": float(row["revenue"]),
                    "expenses": float(row["expenses"]),
                    "marketing_spend": float(row["marketing_spend"]),
                    "customer_growth": float(row["customer_growth"]),
                },
            )
            rows_inserted += 1
        conn.commit()
    return rows_inserted