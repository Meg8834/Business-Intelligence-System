from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session
from database.db_config import get_db
from database.models import User, BusinessData
from models.health_score import calculate_health_score
from models.anomaly_model import detect_anomalies
from models.forecasting_model import forecast_revenue
from utils.auth_utils import get_current_user
from config import OPENAI_API_KEY
from openai import OpenAI

router = APIRouter()
client = OpenAI(api_key=OPENAI_API_KEY) if OPENAI_API_KEY else None


class ChatRequest(BaseModel):
    message: str


def get_user_context(user_id: int, db: Session) -> dict:
    rows = db.query(BusinessData).filter(
        BusinessData.user_id == user_id
    ).order_by(BusinessData.id.asc()).all()

    if not rows:
        return {}

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
    profit = latest.revenue - latest.expenses

    return {
        "latest_month": latest.month,
        "revenue": latest.revenue,
        "expenses": latest.expenses,
        "marketing_spend": latest.marketing_spend,
        "customer_growth": latest.customer_growth,
        "profit": profit,
        "profit_margin": round((profit / latest.revenue * 100), 2) if latest.revenue > 0 else 0,
        "health_score": health["health_score"],
        "health_label": health["label"],
        "breakdown": health["breakdown"],
        "anomaly_count": anomaly_count,
        "forecast_next": forecast_next,
        "total_months": len(rows),
    }


def build_system_prompt(ctx: dict, user_name: str) -> str:
    return f"""
You are an expert Business Intelligence Assistant for {user_name}'s business.
Use the following real-time data to answer questions accurately.

=== BUSINESS DATA ===
Latest Month    : {ctx.get('latest_month')}
Revenue         : Rs. {ctx.get('revenue', 0):,.2f}
Expenses        : Rs. {ctx.get('expenses', 0):,.2f}
Profit          : Rs. {ctx.get('profit', 0):,.2f} ({ctx.get('profit_margin', 0)}% margin)
Marketing Spend : Rs. {ctx.get('marketing_spend', 0):,.2f}
Customer Growth : {ctx.get('customer_growth', 0)}%

=== ML RESULTS ===
Health Score    : {ctx.get('health_score', 0)}/100 ({ctx.get('health_label')})
Anomalies       : {ctx.get('anomaly_count', 0)} month(s)
Next Month Forecast: Rs. {ctx.get('forecast_next', 0):,.2f}
Total Months    : {ctx.get('total_months', 0)}

Give specific, actionable advice using these numbers.
Use Indian Rupee (Rs.) for currency. Be concise and professional.
"""


def fallback_response(message: str, ctx: dict) -> str:
    msg = message.lower()
    if not ctx:
        return "No data found. Please upload your CSV first."
    if any(w in msg for w in ["health", "score"]):
        return f"Health Score: {ctx['health_score']}/100 — {ctx['health_label']}."
    if any(w in msg for w in ["revenue", "sales"]):
        return f"Latest revenue: Rs.{ctx['revenue']:,.2f} for {ctx['latest_month']}."
    if any(w in msg for w in ["profit", "loss"]):
        return f"Profit: Rs.{ctx['profit']:,.2f} ({ctx['profit_margin']}% margin)."
    if any(w in msg for w in ["anomaly", "risk"]):
        return f"{ctx['anomaly_count']} anomalies detected."
    if any(w in msg for w in ["forecast", "predict"]):
        return f"Next month forecast: Rs.{ctx['forecast_next']:,.2f}."
    if any(w in msg for w in ["hi", "hello", "help"]):
        return f"Hello! Health score: {ctx['health_score']}/100. Ask me about revenue, profit, anomalies, or forecast."
    if any(w in msg for w in ["improve", "tips", "suggest"]):
        tips = []
        if ctx["health_score"] < 60:
            tips.append("Reduce expenses below 70% of revenue.")
        if ctx["customer_growth"] < 5:
            tips.append("Invest in customer acquisition.")
        if ctx["anomaly_count"] > 0:
            tips.append(f"Investigate {ctx['anomaly_count']} anomalous months.")
        if not tips:
            tips.append("Business looks healthy! Focus on scaling.")
        return "Recommendations:\n" + "\n".join(f"* {t}" for t in tips)
    return "Ask me about: revenue, profit, expenses, anomalies, forecast, health score, or tips."


@router.post("/chat")
def chat(
    request: ChatRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if not request.message.strip():
        raise HTTPException(status_code=400, detail="Message cannot be empty.")

    ctx = get_user_context(current_user.id, db)

    if client and OPENAI_API_KEY:
        try:
            system_prompt = build_system_prompt(ctx, current_user.name) if ctx else (
                f"You are a Business Intelligence Assistant for {current_user.name}. "
                "No data uploaded yet — ask them to upload their CSV."
            )
            response = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": request.message},
                ],
                max_tokens=400,
                temperature=0.7,
            )
            return {
                "question": request.message,
                "answer": response.choices[0].message.content.strip(),
                "powered_by": "OpenAI GPT-3.5",
            }
        except Exception as e:
            answer = fallback_response(request.message, ctx)
            return {"question": request.message, "answer": answer, "powered_by": "Rule-based fallback"}

    answer = fallback_response(request.message, ctx)
    return {"question": request.message, "answer": answer, "powered_by": "Rule-based"}