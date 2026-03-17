import numpy as np
import pandas as pd
from sklearn.ensemble import IsolationForest


def detect_anomalies(data: list[dict]) -> list[dict]:
    """
    Accepts a list of business data dicts (each with revenue,
    expenses, marketing_spend, customer_growth).

    Returns the same list with an added `is_anomaly` boolean field.
    Isolation Forest labels -1 as anomaly, 1 as normal.
    """
    if len(data) < 4:
        # Not enough samples for Isolation Forest — mark all as normal
        for row in data:
            row["is_anomaly"] = False
        return data

    feature_cols = ["revenue", "expenses", "marketing_spend", "customer_growth"]
    df = pd.DataFrame(data)

    # Ensure numeric
    for col in feature_cols:
        df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)

    X = df[feature_cols].values

    model = IsolationForest(
        n_estimators=100,
        contamination=0.1,   # assume ~10% of data could be anomalous
        random_state=42,
    )
    labels = model.fit_predict(X)   # 1 = normal, -1 = anomaly

    result = []
    for i, row in enumerate(data):
        row_copy = dict(row)
        row_copy["is_anomaly"] = bool(labels[i] == -1)
        result.append(row_copy)

    return result