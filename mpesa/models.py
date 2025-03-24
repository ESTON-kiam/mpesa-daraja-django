from django.db import models


class MpesaPayment(models.Model):
    phone_number = models.CharField(max_length=15)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    reference = models.CharField(max_length=40)
    description = models.TextField()
    transaction_id = models.CharField(max_length=30, blank=True, null=True)
    checkout_request_id = models.CharField(max_length=50, blank=True, null=True)
    status = models.CharField(max_length=15, default='PENDING')
    receipt_number = models.CharField(max_length=30, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.phone_number} - {self.amount} - {self.status}"