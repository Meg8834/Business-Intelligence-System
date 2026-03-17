from fastapi import APIRouter, HTTPException, Query
from sqlalchemy import text
from database.db_config import engine
from models.forecasting_model import forecast_revenue

router = APIRouter()


@router.get("/forecast")
def get_forecast(periods: int = Query(default=3, ge=1, le=12)):
    """
    Reads all revenue values from the database,
    applies Linear Regression, and returns future predictions.
    Query param `periods` controls how many months to predict (1–12).
    """
    with engine.connect() as conn:
        result = conn.execute(
            text("SELECT month, revenue FROM business_data ORDER BY id ASC")
        )
        rows = [dict(r._mapping) for r in result]

    if len(rows) < 2:
        raise HTTPException(
            status_code=400,
            detail="Not enough data to forecast. Upload at least 2 months of data.",
        )

    months = [r["month"] for r in rows]
    revenues = [float(r["revenue"]) for r in rows]

    predictions = forecast_revenue(revenues, periods=periods)

    # Generate future month labels  e.g. "Forecast 1", "Forecast 2" ...
    forecast_labels = [f"Forecast Month {i + 1}" for i in range(periods)]

    return {
        "historical": {"months": months, "revenue": revenues},
        "forecast": {"months": forecast_labels, "revenue": predictions},
    }