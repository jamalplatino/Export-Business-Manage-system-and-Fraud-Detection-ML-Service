from django.db import models

# Create your models here.
class Customer(models.Model):
    name = models.CharField(max_length=200)
    email = models.EmailField(unique=True)
    phone = models.CharField(max_length=20, blank=True)
    country = models.CharField(max_length=100)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

class CustomerNote(models.Model):
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE, related_name='notes')
    body = models.TextField()
    metadata = models.JSONField(default=dict, blank=True)  # structured data from agents
    created_by = models.CharField(max_length=100, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Note for {self.customer.name} at {self.created_at:%Y-%m-%d}"
