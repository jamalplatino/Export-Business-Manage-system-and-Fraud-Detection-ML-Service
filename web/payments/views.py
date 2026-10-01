from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages

from customers.views import require_edit_role
from .models import Invoice, Payment

from datetime import datetime
from django.utils import timezone


def payment_list(request):
    payments = Payment.objects.select_related('invoice__customer').order_by('-paid_at')
    return render(request, 'payments/list.html', {'payments': payments})


def payment_detail(request, pk):
    payment = get_object_or_404(Payment, pk=pk)
    return render(request, 'payments/detail.html', {'payment': payment})


def payment_create(request):
    require_edit_role(request.user)
    invoices = Invoice.objects.all().order_by('number')

    if request.method == 'POST':
        invoice_id = request.POST.get('invoice')
        method = request.POST.get('method', '').strip()
        reference = request.POST.get('reference', '').strip()
        amount = request.POST.get('amount', '').strip()
        paid_at = request.POST.get('paid_at', '').strip()

        errors = []
        if not invoice_id:
            errors.append('Invoice is required.')
        if not method:
            errors.append('Payment method is required.')
        if not reference:
            errors.append('Reference is required.')
        if not amount:
            errors.append('Amount is required.')
        if not paid_at:
            errors.append('Paid date is required.')
        if reference and Payment.objects.filter(reference=reference).exists():
            errors.append(f'Reference "{reference}" already exists.')

        

        if errors:
            for e in errors:
                messages.error(request, e)
        else:
            invoice = get_object_or_404(Invoice, pk=invoice_id)

            # Parse paid_at into an aware datetime
            try:
                naive_dt = datetime.fromisoformat(paid_at)
                aware_dt = timezone.make_aware(naive_dt) if timezone.is_naive(naive_dt) else naive_dt
            except ValueError:
                messages.error(request, 'Invalid paid_at format.')
                return render(request, 'payments/form.html', {
                    'action': 'Create',
                    'invoices': invoices,
                    'method_choices': Payment.METHOD_CHOICES,
                })

            payment = Payment.objects.create(
                invoice=invoice,
                method=method,
                reference=reference,
                amount=amount,
                paid_at=aware_dt,
            )
            payment.refresh_from_db()

            # Score with ML service
            from .ml_client import score_payment
            probability, flagged = score_payment(payment)
            payment.fraud_score = probability
            payment.is_flagged = flagged
            payment.save()

            if flagged:
                messages.warning(request, f'⚠ Payment flagged for review (score {probability:.2f}).')
            else:
                messages.success(request, f'Payment created for invoice {invoice.number}.')

            return redirect('payment_list')

    return render(request, 'payments/form.html', {
        'action': 'Create',
        'invoices': invoices,
        'method_choices': Payment.METHOD_CHOICES,
    })