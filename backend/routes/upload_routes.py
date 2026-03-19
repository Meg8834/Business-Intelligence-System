from fastapi import APIRouter, UploadFile, File, HTTPException, Query, Depends
from sqlalchemy.orm import Session
from sqlalchemy import text
from database.db_config import get_db, engine
from database.models import User, BusinessData
from utils.file_handler import validate_and_clean
from utils.auth_utils import get_current_user
import pandas as pd

router = APIRouter()


def insert_dataframe_for_user(df: pd.DataFrame, user_id: int, db: Session) -> int:
    """Inserts cleaned DataFrame rows for a specific user."""
    rows_inserted = 0
    for _, row in df.iterrows():
        record = BusinessData(
            user_id=user_id,
            month=row["month"],
            revenue=float(row["revenue"]),
            expenses=float(row["expenses"]),
            marketing_spend=float(row["marketing_spend"]),
            customer_growth=float(row["customer_growth"]),
        )
        db.add(record)
        rows_inserted += 1
    db.commit()
    return rows_inserted


@router.post("/upload")
async def upload_csv(
    file: UploadFile = File(...),
    mode: str = Query(default="append", enum=["append", "replace"]),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Upload CSV for the logged-in user only.
    mode=append  → adds to existing data
    mode=replace → clears user's data first, then inserts
    """
    if not file.filename.endswith(".csv"):
        raise HTTPException(status_code=400, detail="Only .csv files are accepted.")

    file_bytes = await file.read()

    try:
        df, warnings = validate_and_clean(file_bytes)
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))

    rows_deleted = 0
    if mode == "replace":
        deleted = db.query(BusinessData).filter(
            BusinessData.user_id == current_user.id
        ).delete()
        rows_deleted = deleted
        db.commit()

    rows_inserted = insert_dataframe_for_user(df, current_user.id, db)

    return {
        "message": f"File uploaded successfully in '{mode}' mode.",
        "filename": file.filename,
        "mode": mode,
        "rows_deleted": rows_deleted,
        "rows_inserted": rows_inserted,
        "warnings": warnings,
    }


@router.delete("/clear-data")
def clear_my_data(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Clears only the logged-in user's data."""
    deleted = db.query(BusinessData).filter(
        BusinessData.user_id == current_user.id
    ).delete()
    db.commit()
    return {"message": "Your data cleared successfully.", "rows_deleted": deleted}


@router.get("/data-count")
def get_data_count(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Returns row count for the logged-in user only."""
    count = db.query(BusinessData).filter(
        BusinessData.user_id == current_user.id
    ).count()
    return {"total_rows": count, "status": "empty" if count == 0 else "has_data"}


@router.get("/business-data")
def get_business_data(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Returns all business data for the logged-in user only."""
    data = db.query(BusinessData).filter(
        BusinessData.user_id == current_user.id
    ).order_by(BusinessData.id.asc()).all()
    return [d.to_dict() for d in data]