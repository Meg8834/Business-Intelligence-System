def calculate_health_score(
    revenue: float,
    expenses: float,
    marketing_spend: float,
    customer_growth: float,
) -> dict:
    """
    Calculates a Business Health Score out of 100 based on 4 sub-scores.

    Sub-scores (25 pts each):
    1. Profit Margin Score  — higher margin = better
    2. Expense Ratio Score  — lower expense/revenue ratio = better
    3. Marketing Efficiency — reasonable marketing spend
    4. Customer Growth Score — positive growth = better
    """
    score = 0
    breakdown = {}

    # --- 1. Profit Margin (target: >20%) ---
    if revenue > 0:
        margin = (revenue - expenses) / revenue * 100
    else:
        margin = 0

    if margin >= 30:
        margin_score = 25
    elif margin >= 20:
        margin_score = 20
    elif margin >= 10:
        margin_score = 13
    elif margin >= 0:
        margin_score = 7
    else:
        margin_score = 0   # negative margin

    score += margin_score
    breakdown["profit_margin_score"] = margin_score
    breakdown["profit_margin_pct"] = round(margin, 2)

    # --- 2. Expense Ratio (target: expenses < 70% of revenue) ---
    if revenue > 0:
        expense_ratio = expenses / revenue * 100
    else:
        expense_ratio = 100

    if expense_ratio <= 50:
        expense_score = 25
    elif expense_ratio <= 70:
        expense_score = 18
    elif expense_ratio <= 90:
        expense_score = 10
    else:
        expense_score = 0

    score += expense_score
    breakdown["expense_ratio_score"] = expense_score
    breakdown["expense_ratio_pct"] = round(expense_ratio, 2)

    # --- 3. Marketing Efficiency (target: marketing_spend < 20% of revenue) ---
    if revenue > 0:
        mkt_ratio = marketing_spend / revenue * 100
    else:
        mkt_ratio = 100

    if mkt_ratio <= 10:
        mkt_score = 25
    elif mkt_ratio <= 20:
        mkt_score = 18
    elif mkt_ratio <= 35:
        mkt_score = 10
    else:
        mkt_score = 5

    score += mkt_score
    breakdown["marketing_efficiency_score"] = mkt_score
    breakdown["marketing_ratio_pct"] = round(mkt_ratio, 2)

    # --- 4. Customer Growth (target: >5%) ---
    if customer_growth >= 15:
        growth_score = 25
    elif customer_growth >= 5:
        growth_score = 18
    elif customer_growth >= 0:
        growth_score = 10
    else:
        growth_score = 0   # negative growth

    score += growth_score
    breakdown["customer_growth_score"] = growth_score
    breakdown["customer_growth_value"] = customer_growth

    # --- Overall label ---
    if score >= 80:
        label = "Excellent"
    elif score >= 60:
        label = "Good"
    elif score >= 40:
        label = "Average"
    else:
        label = "Poor"

    return {
        "health_score": score,
        "label": label,
        "breakdown": breakdown,
    }