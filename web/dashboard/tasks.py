from celery import shared_task
from django.db.models import Sum, Count
from django.db.models.functions import TruncDate
from django.utils import timezone
from datetime import timedelta
import logging

from invoices.models import Invoice
from payments.models import Payment
from .models import DailyRevenue

logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def aggregate_daily_revenue(self, days_back: int = 30):
    """
    Aggregate invoices and payments by day and upsert into DailyRevenue.
    Retries up to 3 times on failure with a 60s delay between attempts.
    """
    try:
        today = timezone.now().date()
        start = today - timedelta(days=days_back)

        # --- Invoices grouped by issued_date ---
        invoice_rows = (
            Invoice.objects
            .filter(issued_date__gte=start)
            .annotate(day=TruncDate("issued_date"))
            .values("day")
            .annotate(
                total_invoiced=Sum("amount"),
                invoice_count=Count("id"),
            )
        )
        invoice_by_day = {row["day"]: row for row in invoice_rows}

        # --- Payments grouped by paid_at date ---
        payment_rows = (
            Payment.objects
            .filter(paid_at__date__gte=start)
            .annotate(day=TruncDate("paid_at"))
            .values("day")
            .annotate(
                total_paid=Sum("amount"),
                payment_count=Count("id"),
            )
        )
        payment_by_day = {row["day"]: row for row in payment_rows}

        # --- Merge into DailyRevenue ---
        all_days = set(invoice_by_day.keys()) | set(payment_by_day.keys())
        created = updated = 0

        for day in all_days:
            inv = invoice_by_day.get(day, {})
            pay = payment_by_day.get(day, {})

            total_invoiced = inv.get("total_invoiced") or 0
            total_paid = pay.get("total_paid") or 0

            obj, was_created = DailyRevenue.objects.update_or_create(
                date=day,
                defaults={
                    "total_invoiced": total_invoiced,
                    "total_paid": total_paid,
                    "outstanding": total_invoiced - total_paid,
                    "invoice_count": inv.get("invoice_count", 0),
                    "payment_count": pay.get("payment_count", 0),
                },
            )
            if was_created:
                created += 1
            else:
                updated += 1

        result = {
            "days_processed": len(all_days),
            "created": created,
            "updated": updated,
            "range": f"{start} → {today}",
        }
        logger.info(f"aggregate_daily_revenue complete: {result}")
        return result

    except Exception as exc:
        logger.exception("aggregate_daily_revenue failed")
        raise self.retry(exc=exc)