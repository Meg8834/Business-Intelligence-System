from fastapi import APIRouter, HTTPException
from sqlalchemy import text
from database.db_config import engine
from models.anomaly_model import detect_anomalies

router = APIRouter()


@router.get("/anomaly")
def get_anomalies():
    """
    Fetches all business data from DB, runs Isolation Forest,
    and returns each row tagged with is_anomaly: true/false.
    """
    with engine.connect() as conn:
        result = conn.execute(
            text("SELECT * FROM business_data ORDER BY id ASC")
        )
        rows = [dict(r._mapping) for r in result]

    if not rows:
        raise HTTPException(status_code=400, detail="No data found. Please upload data first.")

    tagged = detect_anomalies(rows)

    anomalies = [r for r in tagged if r["is_anomaly"]]
    normal = [r for r in tagged if not r["is_anomaly"]]

    return {
        "total_records": len(tagged),
        "anomaly_count": len(anomalies),
        "anomalies": anomalies,
        "normal": normal,
        "all_data": tagged,     # useful for frontend chart colouring
    }