def generate_explanation(
    revenue: float,
    expenses: float,
    marketing_spend: float,
    customer_growth: float,
    health_score: int,
    health_label: str,
    anomaly_count: int = 0,
    forecast_next: float = None,
) -> dict:
    """
    Generates a plain-English summary of the current business state.
    Returns a dict with an overall summary and individual insight messages.
    """
    insights = []

    # --- Profit insight ---
    profit = revenue - expenses
    if profit > 0:
        margin_pct = round(profit / revenue * 100, 1)
        insights.append(
            f"Your business is currently profitable with a margin of {margin_pct}%. "
            f"Profit stands at ₹{profit:,.2f}."
        )
    else:
        insights.append(
            f"⚠️ Your business is currently running at a loss of ₹{abs(profit):,.2f}. "
            "Immediate cost reduction is recommended."
        )

    # --- Expense insight ---
    if revenue > 0:
        expense_ratio = expenses / revenue * 100
        if expense_ratio > 80:
            insights.append(
                f"Expenses are very high at {expense_ratio:.1f}% of revenue. "
                "Consider reducing operational costs."
            )
        elif expense_ratio > 60:
            insights.append(
                f"Expenses are moderate at {expense_ratio:.1f}% of revenue. "
                "There is room for optimisation."
            )
        else:
            insights.append(
                f"Expenses are well-controlled at {expense_ratio:.1f}% of revenue. Keep it up!"
            )

    # --- Marketing insight ---
    if revenue > 0:
        mkt_ratio = marketing_spend / revenue * 100
        if mkt_ratio > 30:
            insights.append(
                f"Marketing spend is high ({mkt_ratio:.1f}% of revenue). "
                "Evaluate ROI before increasing further."
            )
        elif mkt_ratio < 5:
            insights.append(
                "Marketing spend is very low. Increasing investment could accelerate customer growth."
            )
        else:
            insights.append(
                f"Marketing spend ({mkt_ratio:.1f}% of revenue) is within a healthy range."
            )

    # --- Customer growth insight ---
    if customer_growth > 10:
        insights.append(
            f"Strong customer growth of {customer_growth}% — your acquisition strategies are working."
        )
    elif customer_growth > 0:
        insights.append(
            f"Customer growth is positive at {customer_growth}%, but there is room to scale."
        )
    else:
        insights.append(
            f"⚠️ Customer growth is stagnant or declining ({customer_growth}%). "
            "Review your retention and marketing strategies."
        )

    # --- Anomaly insight ---
    if anomaly_count > 0:
        insights.append(
            f"🚨 {anomaly_count} anomalous data point(s) were detected. "
            "These could indicate unusual revenue drops or expense spikes — investigate immediately."
        )
    else:
        insights.append("No anomalies detected. Business data looks consistent.")

    # --- Forecast insight ---
    if forecast_next is not None:
        direction = "increase" if forecast_next > revenue else "decrease"
        insights.append(
            f"📈 Revenue is forecasted to {direction} to ₹{forecast_next:,.2f} next month "
            "based on historical trends."
        )

    # --- Overall summary ---
    summary = (
        f"Your business health score is {health_score}/100 — rated '{health_label}'. "
        + insights[0]
    )

    return {
        "summary": summary,
        "insights": insights,
    }