from django.contrib import admin
from .models import Shipment

@admin.register(Shipment)
class ShipmentAdmin(admin.ModelAdmin):
    list_display = ('tracking_number', 'invoice', 'carrier', 'status')
    list_filter = ('status', 'carrier')
    search_fields = ('tracking_number',)