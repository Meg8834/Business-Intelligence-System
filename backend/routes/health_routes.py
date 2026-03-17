from fastapi import APIRouter, HTTPException
from services.ml_service import get_health_and_explanation

router = APIRouter()


@router.get("/health")
def get_business_health():
    """
    Returns Business Health Score + Natural Language Explanation
    for the latest month using the ml_service layer.
    """
    try:
        return get_health_and_explanation()
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))