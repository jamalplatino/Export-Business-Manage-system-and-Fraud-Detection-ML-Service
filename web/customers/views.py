from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from .models import Customer
from django.contrib.auth.decorators import login_required

from django.core.exceptions import PermissionDenied

def require_edit_role(user):
    if not user.profile.can_edit():
        raise PermissionDenied("You don't have permission to edit.")


@login_required
def customer_list(request):
    customers = Customer.objects.all().order_by('name')
    return render(request, 'customers/list.html', {'customers': customers})


@login_required
def customer_detail(request, pk):
    customer = get_object_or_404(Customer, pk=pk)
    return render(request, 'customers/detail.html', {'customer': customer})


@login_required
def customer_create(request):
    require_edit_role(request.user)

    if request.method == 'POST':
        name = request.POST.get('name', '').strip()
        email = request.POST.get('email', '').strip()
        phone = request.POST.get('phone', '').strip()
        country = request.POST.get('country', '').strip()

        if not name or not email or not country:
            messages.error(request, 'Name, email, and country are required.')
        else:
            Customer.objects.create(name=name, email=email, phone=phone, country=country)
            messages.success(request, f'Customer "{name}" created.')
            return redirect('customer_list')

    return render(request, 'customers/form.html', {'action': 'Create'})