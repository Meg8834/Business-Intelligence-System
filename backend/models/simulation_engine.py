def simulate_scenario(
    revenue: float,
    expenses: float,
    marketing_spend: float,
    customer_growth: float,
    marketing_change_pct: float = 0.0,
    price_change_pct: float = 0.0,
) -> dict:
    """
    Simulates the effect of business decisions on key metrics.

    Parameters
    ----------
    revenue            : Current revenue value.
    expenses           : Current expenses value.
    marketing_spend    : Current marketing spend.
    customer_growth    : Current customer growth rate (as a number, e.g. 5 means 5%).
    marketing_change_pct : % change to apply to marketing spend (+/-).
    price_change_pct     : % change to apply to price/revenue (+/-).

    Assumptions (simple linear model — suitable for BCA level):
    - A 10% increase in marketing spend → ~5% increase in revenue (0.5x multiplier).
    - A price change directly impacts revenue proportionally.
    - Marketing spend change also affects customer_growth (0.3x multiplier).
    """

    # --- Apply marketing change ---
    new_marketing = marketing_spend * (1 + marketing_change_pct / 100)
    marketing_revenue_boost = revenue * (marketing_change_pct / 100) * 0.5
    marketing_growth_boost = customer_growth * (marketing_change_pct / 100) * 0.3

    # --- Apply price change ---
    price_revenue_boost = revenue * (price_change_pct / 100)

    # --- Simulated values ---
    simulated_revenue = revenue + marketing_revenue_boost + price_revenue_boost
    simulated_marketing = new_marketing
    simulated_customer_growth = customer_growth + marketing_growth_boost
    simulated_profit = simulated_revenue - expenses  # expenses unchanged

    # --- Deltas ---
    revenue_delta = simulated_revenue - revenue
    profit_delta = simulated_profit - (revenue - expenses)

    return {
        "input": {
            "revenue": round(revenue, 2),
            "expenses": round(expenses, 2),
            "marketing_spend": round(marketing_spend, 2),
            "customer_growth": round(customer_growth, 2),
            "marketing_change_pct": marketing_change_pct,
            "price_change_pct": price_change_pct,
        },
        "simulated": {
            "revenue": round(simulated_revenue, 2),
            "expenses": round(expenses, 2),
            "marketing_spend": round(simulated_marketing, 2),
            "customer_growth": round(simulated_customer_growth, 2),
            "profit": round(simulated_profit, 2),
        },
        "delta": {
            "revenue_change": round(revenue_delta, 2),
            "profit_change": round(profit_delta, 2),
        },
    }