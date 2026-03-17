import pandas as pd
import numpy as np


def normalize_columns(df: pd.DataFrame) -> pd.DataFrame:
    """
    Strips whitespace from column names and lowercases them.
    """
    df.columns = [c.strip().lower() for c in df.columns]
    return df


def fill_missing_values(df: pd.DataFrame) -> pd.DataFrame:
    """
    Drops fully empty rows, fills remaining numeric nulls with 0.
    """
    df.dropna(how="all", inplace=True)
    numeric_cols = df.select_dtypes(include=[np.number]).columns
    df[numeric_cols] = df[numeric_cols].fillna(0)
    return df


def enforce_types(df: pd.DataFrame) -> pd.DataFrame:
    """
    Casts numeric business columns to float.
    Casts month to string.
    """
    numeric_cols = ["revenue", "expenses", "marketing_spend", "customer_growth"]
    for col in numeric_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0).astype(float)

    if "month" in df.columns:
        df["month"] = df["month"].astype(str).str.strip()

    return df


def remove_duplicates(df: pd.DataFrame) -> pd.DataFrame:
    """
    Drops duplicate rows based on the 'month' column (keeps last).
    """
    if "month" in df.columns:
        df = df.drop_duplicates(subset=["month"], keep="last")
    return df


def preprocess_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    """
    Full preprocessing pipeline — runs all steps in order.
    Call this before passing data to any ML model.
    """
    df = normalize_columns(df)
    df = fill_missing_values(df)
    df = enforce_types(df)
    df = remove_duplicates(df)
    df.reset_index(drop=True, inplace=True)
    return df