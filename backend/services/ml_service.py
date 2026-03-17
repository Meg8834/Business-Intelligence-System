"""
ml_service.py
─────────────
Service layer that sits between routes and raw ML models.
Routes call these functions — they handle DB fetching,
preprocessing, and model invocation in one place.
"""

from sqlalchemy import text
from database.db_config import engine
from utils.preprocessing import preprocess_dataframe
from models.forecasting_model import forecast_revenue
from models.anomaly_model import detect_anomalies
from models.health_score import calculate_health_score
from models.explanation_engine import generate_explanation
import pandas as pd
from config import FORECAST_DEFAULT_PERIODS


def fetch_all_data() -> list[dict]:
    """Fetch all rows from business_data, ordered by id."""
    with engine.connect() as conn:
        result = conn.execute(text("SELECT * FROM business_data ORDER BY id ASC"))
        return [dict(r._mapping) for r in result]


def get_forecast_data(periods: int = FORECAST_DEFAULT_PERIODS) -> dict:
    """
    Fetches data, preprocesses it, runs Linear Regression forecast.
    Returns historical + forecast data ready for the frontend.
    """
    rows = fetch_all_data()
    if len(rows) < 2:
        raise ValueError("At least 2 months of data are required for forecasting.")

    df = preprocess_dataframe(pd.DataFrame(rows))

    months = df["month"].tolist()
    revenues = df["revenue"].tolist()

    predictions = forecast_revenue(revenues, periods=periods)
    forecast_labels = [f"Forecast Month {i + 1}" for i in range(periods)]

    return {
        "historical": {"months": months, "revenue": revenues},
        "forecast": {"months": forecast_labels, "revenue": predictions},
    }


def get_anomaly_data() -> dict:
    """
    Fetches data, preprocesses it, runs Isolation Forest.
    Returns all rows tagged with is_anomaly.
    """
    rows = fetch_all_data()
    if not rows:
        raise ValueError("No data found.")

    df = preprocess_dataframe(pd.DataFrame(rows))
    clean_rows = df.to_dict(orient="records")

    tagged = detect_anomalies(clean_rows)
    anomalies = [r for r in tagged if r["is_anomaly"]]

    return {
        "total_records": len(tagged),
        "anomaly_count": len(anomalies),
        "anomalies": anomalies,
        "all_data": tagged,
    }


def get_health_and_explanation() -> dict:
    """
    Uses the latest data row for health scoring and NL explanation.
    Uses full history for anomaly count and forecast.
    """
    rows = fetch_all_data()
    if not rows:
        raise ValueError("No data found.")

    df = preprocess_dataframe(pd.DataFrame(rows))
    latest = df.iloc[-1].to_dict()

    health = calculate_health_score(
        revenue=latest["revenue"],
        expenses=latest["expenses"],
        marketing_spend=latest["marketing_spend"],
        customer_growth=latest["customer_growth"],
    )

    # Anomaly count
    tagged = detect_anomalies(df.to_dict(orient="records"))
    anomaly_count = sum(1 for r in tagged if r["is_anomaly"])

    # Next month forecast
    revenues = df["revenue"].tolist()
    forecast_next = forecast_revenue(revenues, periods=1)[0] if len(revenues) >= 2 else None

    explanation = generate_explanation(
        revenue=latest["revenue"],
        expenses=latest["expenses"],
        marketing_spend=latest["marketing_spend"],
        customer_growth=latest["customer_growth"],
        health_score=health["health_score"],
        health_label=health["label"],
        anomaly_count=anomaly_count,
        forecast_next=forecast_next,
    )

    return {
        "latest_month": latest["month"],
        "health": health,
        "explanation": explanation,
    }