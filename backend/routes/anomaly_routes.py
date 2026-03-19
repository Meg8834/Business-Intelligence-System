from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from database.db_config import get_db
from database.models import User, BusinessData
from models.anomaly_model import detect_anomalies
from utils.auth_utils import get_current_user

router = APIRouter()


@router.get("/anomaly")
def get_anomalies(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Detects anomalies in the logged-in user's data only."""
    rows = db.query(BusinessData).filter(
        BusinessData.user_id == current_user.id
    ).order_by(BusinessData.id.asc()).all()

    if not rows:
        raise HTTPException(status_code=400, detail="No data found. Upload CSV first.")

    data = [r.to_dict() for r in rows]
    tagged = detect_anomalies(data)
    anomalies = [r for r in tagged if r["is_anomaly"]]

    return {
        "total_records": len(tagged),
        "anomaly_count": len(anomalies),
        "anomalies": anomalies,
        "all_data": tagged,
    }