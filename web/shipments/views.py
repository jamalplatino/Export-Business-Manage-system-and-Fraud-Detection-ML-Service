from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from invoices.models import Invoice
from customers.views import require_edit_role
from .models import Shipment


def shipment_list(request):
    shipments = Shipment.objects.select_related('invoice__customer').order_by('-shipped_date')
    return render(request, 'shipments/list.html', {'shipments': shipments})


def shipment_detail(request, pk):
    shipment = get_object_or_404(Shipment, pk=pk)
    return render(request, 'shipments/detail.html', {'shipment': shipment})


def shipment_create(request):
    require_edit_role(request.user)
    invoices = Invoice.objects.select_related('customer').order_by('number')

    if request.method == 'POST':
        invoice_id = request.POST.get('invoice')
        tracking_number = request.POST.get('tracking_number', '').strip()
        carrier = request.POST.get('carrier', '').strip()
        status = request.POST.get('status', 'pending')
        shipped_date = request.POST.get('shipped_date', '').strip() or None
        delivered_date = request.POST.get('delivered_date', '').strip() or None

        errors = []
        if not invoice_id:
            errors.append('Invoice is required.')
        if not tracking_number:
            errors.append('Tracking number is required.')
        if not carrier:
            errors.append('Carrier is required.')
        if tracking_number and Shipment.objects.filter(tracking_number=tracking_number).exists():
            errors.append(f'Tracking number "{tracking_number}" already exists.')

        if errors:
            for e in errors:
                messages.error(request, e)
        else:
            invoice = get_object_or_404(Invoice, pk=invoice_id)
            Shipment.objects.create(
                invoice=invoice,
                tracking_number=tracking_number,
                carrier=carrier,
                status=status,
                shipped_date=shipped_date,
                delivered_date=delivered_date,
            )
            messages.success(request, f'Shipment {tracking_number} created.')
            return redirect('shipment_list')

    return render(request, 'shipments/form.html', {
        'action': 'Create',
        'invoices': invoices,
        'status_choices': Shipment.STATUS_CHOICES,
    })