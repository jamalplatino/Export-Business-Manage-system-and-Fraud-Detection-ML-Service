from django.contrib import admin

# Register your models here.
from django.contrib import admin
from .models import Invoice

@admin.register(Invoice)
class InvoiceAdmin(admin.ModelAdmin):
    list_display = ('number', 'customer', 'amount', 'currency', 'status', 'due_date')
    list_filter = ('status', 'currency')
    search_fields = ('number', 'customer__name')