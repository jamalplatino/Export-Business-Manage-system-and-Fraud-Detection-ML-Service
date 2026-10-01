from django.db import models

class DailyRevenue(models.Model):
    date = models.DateField(unique=True)
    total_invoiced = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    total_paid = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    outstanding = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    invoice_count = models.IntegerField(default=0)
    payment_count = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-date']

    def __str__(self):
        return f"{self.date}: invoiced {self.total_invoiced}, paid {self.total_paid}"