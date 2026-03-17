import numpy as np
from sklearn.linear_model import LinearRegression


def forecast_revenue(revenue_list: list[float], periods: int = 3) -> list[float]:
    """
    Takes a list of historical revenue values and returns
    predictions for the next `periods` months.

    Uses simple Linear Regression on the month index as feature.
    """
    if len(revenue_list) < 2:
        raise ValueError("At least 2 data points are required for forecasting.")

    n = len(revenue_list)
    X = np.arange(n).reshape(-1, 1)          # month indices [0, 1, 2, ...]
    y = np.array(revenue_list, dtype=float)

    model = LinearRegression()
    model.fit(X, y)

    # Predict next `periods` months
    future_X = np.arange(n, n + periods).reshape(-1, 1)
    predictions = model.predict(future_X)

    return [round(float(p), 2) for p in predictions]