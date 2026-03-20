from datetime import datetime

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


def format_currency(value: float | None) -> str:
    amount = float(value or 0)
    return f"Rs.{amount:,.2f}"


def calculate_row_profit(row: dict) -> float:
    return float(row.get("revenue", 0)) - float(row.get("expenses", 0))


def percentage_change(current: float, previous: float) -> float | None:
    if previous == 0:
        return None
    return round(((current - previous) / abs(previous)) * 100, 2)


def build_anomaly_reason(row: dict, baselines: dict) -> str:
    reasons = []

    revenue = float(row.get("revenue", 0))
    expenses = float(row.get("expenses", 0))
    marketing = float(row.get("marketing_spend", 0))
    growth = float(row.get("customer_growth", 0))
    profit = revenue - expenses

    baseline_revenue = baselines.get("revenue", 0)
    baseline_expenses = baselines.get("expenses", 0)
    baseline_marketing = baselines.get("marketing_spend", 0)
    baseline_growth = baselines.get("customer_growth", 0)

    if baseline_revenue and revenue < baseline_revenue * 0.75:
        reasons.append("revenue dropped well below the usual level")
    if baseline_expenses and expenses > baseline_expenses * 1.25:
        reasons.append("expenses spiked above the normal range")
    if baseline_marketing and marketing > baseline_marketing * 1.5:
        reasons.append("marketing spend jumped sharply")
    if growth < 0:
        reasons.append("customer growth turned negative")
    elif baseline_growth and growth < baseline_growth - 5:
        reasons.append("customer growth slowed noticeably")
    if profit < 0:
        reasons.append("the month ended in a loss")

    if not reasons:
        reasons.append("the combination of metrics looked unusual compared with the rest of the data")

    return "; ".join(reasons[:3])


def build_recommendations(ctx: dict) -> list[str]:
    recommendations = []
    breakdown = ctx.get("breakdown", {})

    if breakdown.get("profit_margin_pct", 0) < 20:
        recommendations.append("Improve profit margin by increasing revenue or reducing expense-heavy operations.")
    if breakdown.get("expense_ratio_pct", 0) > 70:
        recommendations.append("Reduce expenses below 70% of revenue to improve business health.")
    if breakdown.get("marketing_ratio_pct", 0) > 20:
        recommendations.append("Audit marketing spend and reallocate budget toward channels with better returns.")
    if ctx.get("customer_growth", 0) < 5:
        recommendations.append("Invest in customer acquisition and retention to lift growth above 5%.")
    if ctx.get("anomaly_count", 0) > 0:
        recommendations.append(f"Investigate {ctx['anomaly_count']} anomalous month(s) to find the operational cause.")

    forecast_next = ctx.get("forecast_next")
    if forecast_next is not None and forecast_next < ctx.get("revenue", 0):
        recommendations.append("Revenue is forecast to soften next month, so review pricing, demand, and campaign performance.")

    if not recommendations:
        recommendations.append("Business looks healthy. Focus on scaling what is already working.")

    return recommendations[:5]


def get_admin_insights(db: Session) -> dict:
    users = db.query(User).order_by(User.id.asc()).all()
    summaries = []

    for user in users:
        rows = db.query(BusinessData).filter(
            BusinessData.user_id == user.id
        ).order_by(BusinessData.id.asc()).all()
        if not rows:
            summaries.append({
                "user_id": user.id,
                "name": user.name,
                "email": user.email,
                "record_count": 0,
                "anomaly_count": 0,
            })
            continue

        tagged = detect_anomalies([row.to_dict() for row in rows])
        anomaly_count = sum(1 for row in tagged if row["is_anomaly"])
        summaries.append({
            "user_id": user.id,
            "name": user.name,
            "email": user.email,
            "record_count": len(rows),
            "anomaly_count": anomaly_count,
        })

    top_user = max(summaries, key=lambda item: item["anomaly_count"], default=None)
    return {
        "users": summaries,
        "top_user": top_user,
        "total_users": len(users),
    }


def get_user_context(user_id: int, db: Session, is_admin: bool = False) -> dict:
    rows = db.query(BusinessData).filter(
        BusinessData.user_id == user_id
    ).order_by(BusinessData.id.asc()).all()

    if not rows:
        context = {
            "today": datetime.now().strftime("%A, %B %d, %Y"),
        }
        if is_admin:
            context["admin_insights"] = get_admin_insights(db)
        return context

    data = [row.to_dict() for row in rows]
    tagged = detect_anomalies(data)
    anomalies = [row for row in tagged if row["is_anomaly"]]

    latest = data[-1]
    previous = data[-2] if len(data) >= 2 else None

    latest_health = calculate_health_score(
        latest["revenue"],
        latest["expenses"],
        latest["marketing_spend"],
        latest["customer_growth"],
    )

    revenues = [row["revenue"] for row in data]
    forecast_next = forecast_revenue(revenues, periods=1)[0] if len(revenues) >= 2 else None
    for row in data:
        row["profit"] = calculate_row_profit(row)

    best_month = max(data, key=lambda row: row["profit"])
    worst_month = min(data, key=lambda row: row["profit"])
    low_growth_months = [row for row in data if float(row.get("customer_growth", 0)) < 5]

    baselines = {
        "revenue": sum(row["revenue"] for row in data) / len(data),
        "expenses": sum(row["expenses"] for row in data) / len(data),
        "marketing_spend": sum(row["marketing_spend"] for row in data) / len(data),
        "customer_growth": sum(row["customer_growth"] for row in data) / len(data),
    }

    anomaly_details = []
    for row in anomalies:
        anomaly_details.append({
            **row,
            "reason": build_anomaly_reason(row, baselines),
        })

    recommendations = build_recommendations({
        "breakdown": latest_health["breakdown"],
        "customer_growth": latest["customer_growth"],
        "anomaly_count": len(anomalies),
        "forecast_next": forecast_next,
        "revenue": latest["revenue"],
    })

    context = {
        "latest_month": latest["month"],
        "latest": latest,
        "previous": previous,
        "revenue": latest["revenue"],
        "expenses": latest["expenses"],
        "marketing_spend": latest["marketing_spend"],
        "customer_growth": latest["customer_growth"],
        "profit": latest["profit"],
        "profit_margin": round((latest["profit"] / latest["revenue"] * 100), 2) if latest["revenue"] > 0 else 0,
        "health_score": latest_health["health_score"],
        "health_label": latest_health["label"],
        "breakdown": latest_health["breakdown"],
        "anomaly_count": len(anomalies),
        "anomalies": anomaly_details,
        "forecast_next": forecast_next,
        "total_months": len(data),
        "months": data,
        "best_month": best_month,
        "worst_month": worst_month,
        "low_growth_months": low_growth_months,
        "recommendations": recommendations,
        "today": datetime.now().strftime("%A, %B %d, %Y"),
    }

    if previous:
        context["comparison"] = {
            "revenue_change": latest["revenue"] - previous["revenue"],
            "revenue_change_pct": percentage_change(latest["revenue"], previous["revenue"]),
            "expense_change": latest["expenses"] - previous["expenses"],
            "expense_change_pct": percentage_change(latest["expenses"], previous["expenses"]),
            "profit_change": latest["profit"] - previous["profit"],
            "profit_change_pct": percentage_change(latest["profit"], previous["profit"]),
            "customer_growth_change": round(latest["customer_growth"] - previous["customer_growth"], 2),
        }

    if is_admin:
        context["admin_insights"] = get_admin_insights(db)

    return context


def build_system_prompt(ctx: dict, user_name: str, is_admin: bool) -> str:
    recent_months = ", ".join(
        f"{row['month']} (Revenue {format_currency(row['revenue'])}, Profit {format_currency(row['profit'])})"
        for row in ctx.get("months", [])[-3:]
    )
    anomaly_summary = ", ".join(
        f"{row['month']}: {row['reason']}"
        for row in ctx.get("anomalies", [])[:3]
    ) or "No anomalies detected."
    recommendations = "\n".join(f"- {tip}" for tip in ctx.get("recommendations", []))

    admin_block = ""
    if is_admin and ctx.get("admin_insights", {}).get("top_user"):
        top_user = ctx["admin_insights"]["top_user"]
        admin_block = f"""
=== ADMIN INSIGHTS ===
Total Users     : {ctx['admin_insights']['total_users']}
Highest Anomaly User : {top_user['name']} ({top_user['email']}) with {top_user['anomaly_count']} anomalies
"""

    return f"""
You are an expert Business Intelligence Assistant for {user_name}'s business.
Use the following real-time data to answer questions accurately.

=== BUSINESS DATA ===
Latest Month    : {ctx.get('latest_month')}
Revenue         : {format_currency(ctx.get('revenue'))}
Expenses        : {format_currency(ctx.get('expenses'))}
Profit          : {format_currency(ctx.get('profit'))} ({ctx.get('profit_margin', 0)}% margin)
Marketing Spend : {format_currency(ctx.get('marketing_spend'))}
Customer Growth : {ctx.get('customer_growth', 0)}%
Recent Months   : {recent_months}

=== ML RESULTS ===
Health Score    : {ctx.get('health_score', 0)}/100 ({ctx.get('health_label')})
Anomalies       : {ctx.get('anomaly_count', 0)} month(s)
Anomaly Details : {anomaly_summary}
Next Month Forecast: {format_currency(ctx.get('forecast_next'))}
Best Month      : {ctx.get('best_month', {}).get('month')} ({format_currency(ctx.get('best_month', {}).get('profit'))} profit)
Worst Month     : {ctx.get('worst_month', {}).get('month')} ({format_currency(ctx.get('worst_month', {}).get('profit'))} profit)
Recommendations :
{recommendations}
{admin_block}
Give specific, actionable advice using these numbers.
Use Indian Rupee (Rs.) for currency. Be concise and professional.
"""


def answer_anomalies(ctx: dict) -> str:
    anomalies = ctx.get("anomalies", [])
    if not anomalies:
        return "No anomalies detected in your uploaded data."

    lines = [f"{len(anomalies)} anomalies detected."]
    for row in anomalies[:3]:
        lines.append(
            f"- {row['month']}: {row['reason']}. Revenue {format_currency(row['revenue'])}, "
            f"expenses {format_currency(row['expenses'])}, growth {row['customer_growth']}%."
        )
    return "\n".join(lines)


def answer_comparison(ctx: dict, msg: str) -> str:
    if "best" in msg or "worst" in msg:
        best = ctx["best_month"]
        worst = ctx["worst_month"]
        return (
            f"Best month by profit was {best['month']} with profit {format_currency(best['profit'])}. "
            f"Worst month was {worst['month']} with profit {format_currency(worst['profit'])}."
        )

    previous = ctx.get("previous")
    comparison = ctx.get("comparison")
    if not previous or not comparison:
        return "I need at least two months of data to compare periods."

    latest = ctx["latest"]
    revenue_delta = format_currency(comparison["revenue_change"])
    profit_delta = format_currency(comparison["profit_change"])
    growth_delta = comparison["customer_growth_change"]
    return (
        f"Compared with {previous['month']}, {latest['month']} revenue changed by {revenue_delta} "
        f"({comparison['revenue_change_pct']}%), profit changed by {profit_delta} "
        f"({comparison['profit_change_pct']}%), and customer growth changed by {growth_delta} points."
    )


def answer_recommendations(ctx: dict) -> str:
    tips = ctx.get("recommendations", [])
    return "Recommendations:\n" + "\n".join(f"* {tip}" for tip in tips)


def answer_low_growth(ctx: dict) -> str:
    low_growth = ctx.get("low_growth_months", [])
    if not low_growth:
        return "No months have low growth. All recorded months are at or above 5% customer growth."

    lines = ["Months with low growth (<5% customer growth):"]
    for row in low_growth[:8]:
        lines.append(
            f"* {row['month']}: growth {row['customer_growth']}%, revenue {format_currency(row['revenue'])}, "
            f"profit {format_currency(row['profit'])}"
        )
    return "\n".join(lines)


def answer_admin_insights(ctx: dict, current_user: User) -> str:
    if not current_user.is_admin:
        return "Admin insights are available only to admin users."

    insights = ctx.get("admin_insights", {})
    top_user = insights.get("top_user")
    if not top_user:
        return "No admin insight data is available yet."

    return (
        f"Across {insights['total_users']} users, {top_user['name']} ({top_user['email']}) "
        f"currently has the highest anomaly count with {top_user['anomaly_count']} anomalies "
        f"across {top_user['record_count']} record(s)."
    )


def answer_name(ctx: dict, current_user: User) -> str:
    return f"Your name is {current_user.name}."


def answer_date(ctx: dict) -> str:
    return f"Today is {ctx['today']}."


def fallback_response(message: str, ctx: dict, current_user: User) -> str:
    msg = message.lower().strip()

    if any(word in msg for word in ["what is my name", "who am i", "my name"]):
        return answer_name(ctx, current_user)

    if "date" in msg or "today" in msg:
        return answer_date(ctx)

    if any(word in msg for word in ["admin insight", "highest anomaly", "which user", "all users", "platform-level"]):
        return answer_admin_insights(ctx, current_user)

    if "latest" not in ctx:
        return "No data found. Please upload your CSV first."

    if any(word in msg for word in ["compare", "last month", "previous month", "best month", "worst month"]):
        return answer_comparison(ctx, msg)

    if any(word in msg for word in ["anomaly", "anomalies", "anomalous", "risk", "risks"]):
        return answer_anomalies(ctx)

    if any(word in msg for word in ["low growth", "growth below", "show only months with low growth", "filter growth"]):
        return answer_low_growth(ctx)

    if any(word in msg for word in ["improve", "tips", "suggest", "recommend"]):
        return answer_recommendations(ctx)

    if any(word in msg for word in ["health", "score"]):
        return f"Health Score: {ctx['health_score']}/100 - {ctx['health_label']}."

    if any(word in msg for word in ["revenue", "sales"]):
        return f"Latest revenue: {format_currency(ctx['revenue'])} for {ctx['latest_month']}."

    if any(word in msg for word in ["profit", "loss"]):
        return f"Profit: {format_currency(ctx['profit'])} ({ctx['profit_margin']}% margin)."

    if any(word in msg for word in ["forecast", "predict"]):
        if ctx["forecast_next"] is None:
            return "I need at least two months of revenue data before I can forecast the next month."
        return f"Next month forecast: {format_currency(ctx['forecast_next'])}."

    if any(word in msg for word in ["hi", "hello", "help"]):
        return (
            f"Hello! Health score: {ctx['health_score']}/100. "
            "Ask me about anomalies, comparisons, recommendations, low-growth months, or forecasts."
        )

    return (
        "Ask me about: anomalies and why they happened, comparing months, recommendations to improve profit, "
        "months with low growth, forecasts, health score, or admin insights."
    )


@router.post("/chat")
def chat(
    request: ChatRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if not request.message.strip():
        raise HTTPException(status_code=400, detail="Message cannot be empty.")

    ctx = get_user_context(current_user.id, db, current_user.is_admin)
    local_answer = fallback_response(request.message, ctx, current_user)
    msg = request.message.lower()
    rule_based_triggers = [
        "anomaly", "anomalies", "anomalous", "risk", "risks",
        "compare", "last month", "previous month", "best month", "worst month",
        "improve", "tips", "suggest", "recommend",
        "low growth", "growth below", "filter growth",
        "highest anomaly", "which user", "admin insight", "all users", "platform-level",
        "what is my name", "who am i", "my name",
        "date", "today",
    ]

    if "latest" not in ctx or any(trigger in msg for trigger in rule_based_triggers):
        return {
            "question": request.message,
            "answer": local_answer,
            "powered_by": "Rule-based",
        }

    if client and OPENAI_API_KEY and ctx:
        try:
            system_prompt = build_system_prompt(ctx, current_user.name, current_user.is_admin)
            response = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": request.message},
                ],
                max_tokens=400,
                temperature=0.7,
            )
            model_answer = response.choices[0].message.content.strip()

            if any(trigger in request.message.lower() for trigger in [
                "anomaly", "anomalies", "anomalous", "compare", "last month", "previous month",
                "best month", "worst month", "improve", "tips", "suggest", "recommend",
                "low growth", "highest anomaly", "which user", "admin insight"
            ]):
                return {
                    "question": request.message,
                    "answer": local_answer,
                    "powered_by": "Rule-based",
                }

            return {
                "question": request.message,
                "answer": model_answer,
                "powered_by": "OpenAI GPT-3.5",
            }
        except Exception:
            return {
                "question": request.message,
                "answer": local_answer,
                "powered_by": "Rule-based fallback",
            }

    return {
        "question": request.message,
        "answer": local_answer,
        "powered_by": "Rule-based",
    }
