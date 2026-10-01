"""
Client for the fraud detection ML service.
Computes features for a single payment and calls the service.
"""
import math
import httpx
from django.conf import settings


ML_SERVICE_URL = getattr(settings, "ML_SERVICE_URL", "http://127.0.0.1:8002")


def score_payment(payment) -> tuple[float, bool]:


    """
    Compute features for a single payment and get its fraud score.
    Returns (probability, is_flagged).
    """
    # to get CUSTOMER INFO
    customer = payment.invoice.customer
    # Historical baseline — excludes the current row
    past_amounts = list(
        payment.__class__.objects
        .filter(invoice__customer=customer)
        .exclude(pk=payment.pk)
        .values_list("amount", flat=True)
    )

    if past_amounts:
        cust_avg = float(sum(past_amounts) / len(past_amounts))
        cust_count = len(past_amounts)
    else:
        cust_avg = float(payment.amount)
        cust_count = 1

    ratio = float(payment.amount) / cust_avg if cust_avg > 0 else 1.0

    features = {
        "log_amount": math.log1p(float(payment.amount)),
        "hour": payment.paid_at.hour,
        "dow": payment.paid_at.weekday(),
        "cust_avg": cust_avg,
        "cust_count": cust_count,
        "ratio_to_avg": ratio,
    }

    try:
        resp = httpx.post(f"{ML_SERVICE_URL}/score", json=features, timeout=5.0)
        resp.raise_for_status()
        data = resp.json()
        return data["probability"], data["is_fraud"]
    except Exception as e:
        print(f"ML scoring failed: {e}")
        return 0.0, False