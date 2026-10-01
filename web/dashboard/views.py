from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.db.models import Sum, Count, Q, F
from django.utils import timezone
from datetime import timedelta
from invoices.models import Invoice
from payments.models import Payment
from shipments.models import Shipment
from customers.models import Customer


@login_required
def dashboard(request):
    today = timezone.now().date()
    thirty_days_ago = today - timedelta(days=30)

    # --- Top-line metrics ---
    total_invoiced = Invoice.objects.aggregate(t=Sum('amount'))['t'] or 0
    total_paid = Payment.objects.aggregate(t=Sum('amount'))['t'] or 0
    outstanding = total_invoiced - total_paid

    unpaid_count = Invoice.objects.exclude(status='paid').count()
    overdue_count = Invoice.objects.filter(
        status__in=['sent', 'overdue'],
        due_date__lt=today,
    ).count()

    customer_count = Customer.objects.count()
    shipment_count = Shipment.objects.count()

    # --- Revenue last 30 days, grouped by day ---
    daily_revenue = (
        Payment.objects
        .filter(paid_at__date__gte=thirty_days_ago)
        .extra(select={'day': 'date(paid_at)'})
        .values('day')
        .annotate(total=Sum('amount'))
        .order_by('day')
    )

    # Prepare chart data
    revenue_labels = [row['day'].strftime('%Y-%m-%d') if hasattr(row['day'], 'strftime')
                      else str(row['day']) for row in daily_revenue]
    revenue_values = [float(row['total']) for row in daily_revenue]

    # --- Invoices by status ---
    invoice_status = (
        Invoice.objects
        .values('status')
        .annotate(count=Count('id'))
        .order_by('status')
    )
    status_labels = [row['status'].title() for row in invoice_status]
    status_values = [row['count'] for row in invoice_status]

    # --- Top 5 customers by invoiced amount ---
    top_customers = (
        Customer.objects
        .annotate(total=Sum('invoices__amount'))
        .filter(total__isnull=False)
        .order_by('-total')[:5]
    )

    context = {
        'total_invoiced': total_invoiced,
        'total_paid': total_paid,
        'outstanding': outstanding,
        'unpaid_count': unpaid_count,
        'overdue_count': overdue_count,
        'customer_count': customer_count,
        'shipment_count': shipment_count,
        'revenue_labels': revenue_labels,
        'revenue_values': revenue_values,
        'status_labels': status_labels,
        'status_values': status_values,
        'top_customers': top_customers,
    }
    return render(request, 'dashboard/index.html', context)