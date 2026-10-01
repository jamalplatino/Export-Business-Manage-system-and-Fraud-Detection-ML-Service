from django.contrib import admin
from .models import DailyRevenue

@admin.register(DailyRevenue)
class DailyRevenueAdmin(admin.ModelAdmin):
    list_display = ('date', 'total_invoiced', 'total_paid', 'outstanding', 'invoice_count')
    list_filter = ('date',)