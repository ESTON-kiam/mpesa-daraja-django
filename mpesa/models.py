from django.db import models
from django.utils import timezone


class MpesaPayment(models.Model):
    """Model for M-Pesa payment transactions"""
    STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
    )

    transaction_id = models.CharField(max_length=50, unique=True)
    phone_number = models.CharField(max_length=15)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    transaction_date = models.DateTimeField(default=timezone.now)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')

    def __str__(self):
        return f"{self.transaction_id} - {self.amount} - {self.status}"

    class Meta:
        ordering = ['-transaction_date']