from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from database.db_config import get_db
from database.models import User, BusinessData
from models.health_score import calculate_health_score
from models.explanation_engine import generate_explanation
from models.anomaly_model import detect_anomalies
from models.forecasting_model import forecast_revenue
from utils.auth_utils import get_current_user

router = APIRouter()


@router.get("/health")
def get_business_health(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Returns health score and explanation for the logged-in user's data."""
    rows = db.query(BusinessData).filter(
        BusinessData.user_id == current_user.id
    ).order_by(BusinessData.id.asc()).all()

    if not rows:
        raise HTTPException(status_code=400, detail="No data found. Upload CSV first.")

    latest = rows[-1]
    health = calculate_health_score(
        latest.revenue, latest.expenses,
        latest.marketing_spend, latest.customer_growth
    )

    data = [r.to_dict() for r in rows]
    tagged = detect_anomalies(data)
    anomaly_count = sum(1 for r in tagged if r["is_anomaly"])

    revenues = [r.revenue for r in rows]
    forecast_next = forecast_revenue(revenues, periods=1)[0] if len(revenues) >= 2 else None

    explanation = generate_explanation(
        latest.revenue, latest.expenses,
        latest.marketing_spend, latest.customer_growth,
        health["health_score"], health["label"],
        anomaly_count, forecast_next
    )

    return {
        "user": current_user.name,
        "latest_month": latest.month,
        "health": health,
        "explanation": explanation,
    }