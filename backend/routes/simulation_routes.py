from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from database.models import User
from services.simulation_service import run_simulation_service
from utils.auth_utils import get_current_user

router = APIRouter()


class SimulationRequest(BaseModel):
    revenue: float
    expenses: float
    marketing_spend: float
    customer_growth: float
    marketing_change_pct: float = 0.0
    price_change_pct: float = 0.0


@router.post("/simulate")
def run_simulation(
    request: SimulationRequest,
    current_user: User = Depends(get_current_user)
):
    """Runs scenario simulation for the logged-in user."""
    try:
        result = run_simulation_service(
            revenue=request.revenue,
            expenses=request.expenses,
            marketing_spend=request.marketing_spend,
            customer_growth=request.customer_growth,
            marketing_change_pct=request.marketing_change_pct,
            price_change_pct=request.price_change_pct,
        )
        result["simulated_by"] = current_user.name
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))