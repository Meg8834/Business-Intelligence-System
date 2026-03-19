from fastapi import APIRouter, HTTPException, Query, Depends
from sqlalchemy.orm import Session
from database.db_config import get_db
from database.models import User, BusinessData
from models.forecasting_model import forecast_revenue
from utils.auth_utils import get_current_user

router = APIRouter()


@router.get("/forecast")
def get_forecast(
    periods: int = Query(default=3, ge=1, le=12),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Forecasts revenue for the logged-in user's data only."""
    rows = db.query(BusinessData).filter(
        BusinessData.user_id == current_user.id
    ).order_by(BusinessData.id.asc()).all()

    if len(rows) < 2:
        raise HTTPException(status_code=400, detail="Need at least 2 months of data.")

    months = [r.month for r in rows]
    revenues = [r.revenue for r in rows]
    predictions = forecast_revenue(revenues, periods=periods)
    forecast_labels = [f"Forecast Month {i+1}" for i in range(periods)]

    # Confidence band (±10% of std deviation)
    import numpy as np
    std = float(np.std(revenues))
    lower = [round(p - std * 0.5, 2) for p in predictions]
    upper = [round(p + std * 0.5, 2) for p in predictions]

    return {
        "historical": {"months": months, "revenue": revenues},
        "forecast": {
            "months": forecast_labels,
            "revenue": predictions,
            "lower_band": lower,
            "upper_band": upper,
        },
    }