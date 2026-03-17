"""
simulation_service.py
──────────────────────
Service layer for the scenario simulation engine.
Handles validation and delegates to the simulation model.
"""

from models.simulation_engine import simulate_scenario


def run_simulation_service(
    revenue: float,
    expenses: float,
    marketing_spend: float,
    customer_growth: float,
    marketing_change_pct: float = 0.0,
    price_change_pct: float = 0.0,
) -> dict:
    """
    Validates inputs and runs the scenario simulation.
    Raises ValueError on bad inputs.
    """
    if revenue <= 0:
        raise ValueError("Revenue must be greater than 0.")
    if expenses < 0:
        raise ValueError("Expenses cannot be negative.")
    if marketing_spend < 0:
        raise ValueError("Marketing spend cannot be negative.")
    if not (-100 <= marketing_change_pct <= 200):
        raise ValueError("Marketing change % must be between -100 and 200.")
    if not (-100 <= price_change_pct <= 200):
        raise ValueError("Price change % must be between -100 and 200.")

    result = simulate_scenario(
        revenue=revenue,
        expenses=expenses,
        marketing_spend=marketing_spend,
        customer_growth=customer_growth,
        marketing_change_pct=marketing_change_pct,
        price_change_pct=price_change_pct,
    )

    # Attach a plain-English verdict
    revenue_delta = result["delta"]["revenue_change"]
    if revenue_delta > 0:
        verdict = f"✅ This scenario is projected to increase revenue by ₹{revenue_delta:,.2f}."
    elif revenue_delta < 0:
        verdict = f"⚠️ This scenario may decrease revenue by ₹{abs(revenue_delta):,.2f}. Proceed with caution."
    else:
        verdict = "No significant change in revenue expected."

    result["verdict"] = verdict
    return result