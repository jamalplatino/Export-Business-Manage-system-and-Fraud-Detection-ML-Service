from django.db import models
from invoices.models import Invoice

class Shipment(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('in_transit', 'In Transit'),
        ('delivered', 'Delivered'),
        ('returned', 'Returned'),
    ]

    invoice = models.ForeignKey(Invoice, on_delete=models.CASCADE, related_name='shipments')
    tracking_number = models.CharField(max_length=100, unique=True)
    carrier = models.CharField(max_length=100)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    shipped_date = models.DateField(null=True, blank=True)
    delivered_date = models.DateField(null=True, blank=True)

    def __str__(self):
        return f"{self.tracking_number} ({self.get_status_display()})"