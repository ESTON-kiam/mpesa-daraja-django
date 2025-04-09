from django.shortcuts import render, redirect
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from .models import MpesaPayment
from django.contrib import messages
import uuid

def index(request):
    """
    Display the payment form and recent payments
    """
    recent_payments = MpesaPayment.objects.all()[:10]

    context = {
        'recent_payments': recent_payments
    }
    return render(request, 'mpesa_app/index.html', context)

@csrf_exempt
def process_payment(request):
    """
    Process M-Pesa payment request
    """
    if request.method == 'POST':
        phone_number = request.POST.get('phone_number')
        amount = request.POST.get('amount')

        transaction_id = f"MPY{uuid.uuid4().hex[:8].upper()}"
        payment = MpesaPayment(
            transaction_id=transaction_id,
            phone_number=phone_number,
            amount=amount,
            status='pending'
        )
        payment.save()

        messages.success(request,
                         f"Payment request of KSH {amount} initiated. Please check your phone to complete the "
                         f"transaction.")
        return redirect('index')

    return redirect('index')

@csrf_exempt
def mpesa_callback(request):
    """
    Callback endpoint for M-Pesa API
    """
    if request.method == 'POST':

        transaction_id = request.POST.get('transaction_id')
        status = request.POST.get('status', 'completed')

        try:
            payment = MpesaPayment.objects.get(transaction_id=transaction_id)
            payment.status = status
            payment.save()
            return JsonResponse({'status': 'success'})
        except MpesaPayment.DoesNotExist:
            return JsonResponse({'status': 'error', 'message': 'Transaction not found'})

    return JsonResponse({'status': 'error', 'message': 'Invalid request method'})