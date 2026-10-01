from django.db import models
from invoices.models import Invoice

class Payment(models.Model):
    METHOD_CHOICES = [
        ('bank_transfer', 'Bank Transfer'),
        ('card', 'Card'),
        ('paypal', 'PayPal'),
    ]

    invoice = models.ForeignKey(Invoice, on_delete=models.PROTECT, related_name='payments')
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    method = models.CharField(max_length=20, choices=METHOD_CHOICES)
    reference = models.CharField(max_length=100, blank=True)
    paid_at = models.DateTimeField()
    created_at = models.DateTimeField(auto_now_add=True)

    # ML-scored fields
    fraud_score = models.FloatField(null=True, blank=True)
    is_flagged = models.BooleanField(default=False)


    def __str__(self):
        return f"Payment {self.amount} for {self.invoice.number}"