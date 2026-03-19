from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from database.db_config import get_db
from database.models import User, BusinessData
from models.health_score import calculate_health_score
from models.anomaly_model import detect_anomalies
from models.forecasting_model import forecast_revenue
from utils.auth_utils import get_current_user

router = APIRouter()

PRIORITY_ORDER = {"critical": 0, "high": 1, "medium": 2, "low": 3}


def make_tip(tip, priority, category):
    return {"tip": tip, "priority": priority, "category": category}


@router.get("/tips")
def get_business_tips(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Returns prioritised tips for the logged-in user's data."""
    rows = db.query(BusinessData).filter(
        BusinessData.user_id == current_user.id
    ).order_by(BusinessData.id.asc()).all()

    if not rows:
        raise HTTPException(status_code=400, detail="No data found. Upload CSV first.")

    latest = rows[-1]
    revenue = latest.revenue
    expenses = latest.expenses
    marketing = latest.marketing_spend
    cgrowth = latest.customer_growth

    health = calculate_health_score(revenue, expenses, marketing, cgrowth)
    data = [r.to_dict() for r in rows]
    tagged = detect_anomalies(data)
    anomaly_count = sum(1 for r in tagged if r["is_anomaly"])
    revenues = [r.revenue for r in rows]
    forecast_next = forecast_revenue(revenues, periods=1)[0] if len(revenues) >= 2 else None

    tips = []
    profit = revenue - expenses
    margin = (profit / revenue * 100) if revenue > 0 else 0
    expense_ratio = (expenses / revenue * 100) if revenue > 0 else 100
    mkt_ratio = (marketing / revenue * 100) if revenue > 0 else 0

    if profit < 0:
        tips.append(make_tip("Business is running at a loss. Immediate cost restructuring required.", "critical", "Profit"))
    elif margin < 10:
        tips.append(make_tip("Profit margin below 10%. Review fixed costs and supplier contracts.", "high", "Profit"))
    else:
        tips.append(make_tip("Profit margin is healthy. Consider reinvesting into expansion.", "low", "Profit"))

    if mkt_ratio > 25:
        tips.append(make_tip("Marketing spend exceeds 25% of revenue. Audit ROI of campaigns.", "high", "Marketing"))
    elif mkt_ratio < 5:
        tips.append(make_tip("Marketing spend is very low. Increase budget to boost customer growth.", "medium", "Marketing"))
    else:
        tips.append(make_tip("Marketing spend is in optimal range. Maintain current strategy.", "low", "Marketing"))

    if cgrowth < 0:
        tips.append(make_tip("Customer growth is negative. Launch retention campaign immediately.", "critical", "Customer Growth"))
    elif cgrowth < 5:
        tips.append(make_tip("Customer growth below 5%. Consider referral programs.", "high", "Customer Growth"))
    else:
        tips.append(make_tip("Customer growth is strong. Ensure infrastructure can scale.", "low", "Customer Growth"))

    if expense_ratio > 80:
        tips.append(make_tip("Expenses exceed 80% of revenue. Eliminate top cost drivers.", "critical", "Expenses"))
    elif expense_ratio > 60:
        tips.append(make_tip("Expenses moderate. Look for automation to reduce costs.", "medium", "Expenses"))
    else:
        tips.append(make_tip("Expense control is excellent. Reinvest savings in high-ROI areas.", "low", "Expenses"))

    if forecast_next:
        if forecast_next < revenue:
            tips.append(make_tip("Revenue forecasted to decline. Boost marketing immediately.", "high", "Forecast"))
        else:
            tips.append(make_tip("Revenue forecasted to grow. Prepare to meet demand.", "low", "Forecast"))

    if anomaly_count > 0:
        tips.append(make_tip(
            f"{anomaly_count} anomalous month(s) detected. Review for fraud or errors.",
            "critical", "Anomaly"
        ))

    tips.sort(key=lambda x: PRIORITY_ORDER.get(x["priority"], 99))

    return {
        "user": current_user.name,
        "health_score": health["health_score"],
        "health_label": health["label"],
        "total_tips": len(tips),
        "critical_count": sum(1 for t in tips if t["priority"] == "critical"),
        "high_priority_count": sum(1 for t in tips if t["priority"] == "high"),
        "tips": tips,
    }