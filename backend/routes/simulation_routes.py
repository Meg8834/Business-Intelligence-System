from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from services.simulation_service import run_simulation_service

router = APIRouter()


class SimulationRequest(BaseModel):
    revenue: float
    expenses: float
    marketing_spend: float
    customer_growth: float
    marketing_change_pct: float = 0.0   # e.g. 20 means +20%
    price_change_pct: float = 0.0       # e.g. -10 means -10%


@router.post("/simulate")
def run_simulation(request: SimulationRequest):
    """
    Accepts current business metrics and desired change percentages.
    Returns simulated outcome with before/after comparison + verdict.
    """
    try:
        result = run_simulation_service(
            revenue=request.revenue,
            expenses=request.expenses,
            marketing_spend=request.marketing_spend,
            customer_growth=request.customer_growth,
            marketing_change_pct=request.marketing_change_pct,
            price_change_pct=request.price_change_pct,
        )
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))