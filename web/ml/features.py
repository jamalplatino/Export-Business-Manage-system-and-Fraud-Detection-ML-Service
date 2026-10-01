"""
Turn payments into numeric feature vectors for the fraud model.
"""
import math
import pandas as pd
from payments.models import Payment


def build_features():
    """Read all payments, return a DataFrame with features and a synthetic label."""
    payments = Payment.objects.select_related("invoice__customer").all()

    rows = []
    for p in payments:
        rows.append({
            "id": p.id,
            "amount": float(p.amount),
            "paid_at": p.paid_at,
            "customer_id": p.invoice.customer_id,
        })

    df = pd.DataFrame(rows)
    if df.empty:
        print("No payments in the database yet. Add some before continuing.")
        return df

    # Time-based features
    df["paid_at"] = pd.to_datetime(df["paid_at"], utc=True)
    df["hour"] = df["paid_at"].dt.hour
    df["dow"] = df["paid_at"].dt.dayofweek

    # Per-customer aggregates
    cust_stats = (
        df.groupby("customer_id")["amount"]
        .agg(["mean", "count"])
        .rename(columns={"mean": "cust_avg", "count": "cust_count"})
    )
    df = df.join(cust_stats, on="customer_id")
    df["ratio_to_avg"] = df["amount"] / df["cust_avg"]

    # Synthetic label: fraud if amount is > 3x the customer's average
    df["is_fraud"] = (df["ratio_to_avg"] > 3.0).astype(int)

    # Log-scale amount to reduce the effect of large outliers
    df["log_amount"] = df["amount"].apply(math.log1p)

    return df[
        [
            "id",
            "log_amount",
            "hour",
            "dow",
            "cust_avg",
            "cust_count",
            "ratio_to_avg",
            "is_fraud",
        ]
    ]