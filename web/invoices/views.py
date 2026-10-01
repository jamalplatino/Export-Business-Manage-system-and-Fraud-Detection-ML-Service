from django.shortcuts import render

from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from customers.models import Customer
from customers.views import require_edit_role
from .models import Invoice


def invoice_list(request):
    invoices = Invoice.objects.select_related('customer').order_by('-issued_date')
    return render(request, 'invoices/list.html', {'invoices': invoices})


def invoice_detail(request, pk):
    invoice = get_object_or_404(Invoice, pk=pk)
    return render(request, 'invoices/detail.html', {'invoice': invoice})


def invoice_create(request):
    require_edit_role(request.user)
    customers = Customer.objects.all().order_by('name')

    if request.method == 'POST':
        customer_id = request.POST.get('customer')
        number = request.POST.get('number', '').strip()
        amount = request.POST.get('amount', '').strip()
        currency = request.POST.get('currency', 'USD').strip()
        status = request.POST.get('status', 'draft')
        issued_date = request.POST.get('issued_date')
        due_date = request.POST.get('due_date')

        # validation
        errors = []
        if not customer_id:
            errors.append('Customer is required.')
        if not number:
            errors.append('Invoice number is required.')
        if not amount:
            errors.append('Amount is required.')
        if not issued_date or not due_date:
            errors.append('Both issued and due dates are required.')
        if Invoice.objects.filter(number=number).exists():
            errors.append(f'Invoice number "{number}" already exists.')

        if errors:
            for e in errors:
                messages.error(request, e)
        else:
            customer = get_object_or_404(Customer, pk=customer_id)
            Invoice.objects.create(
                customer=customer,
                number=number,
                amount=amount,
                currency=currency,
                status=status,
                issued_date=issued_date,
                due_date=due_date,
            )
            messages.success(request, f'Invoice {number} created.')
            return redirect('invoice_list')

    return render(request, 'invoices/form.html', {
        'action': 'Create',
        'customers': customers,
        'status_choices': Invoice.STATUS_CHOICES,
    })