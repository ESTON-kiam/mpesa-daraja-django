from django.shortcuts import render
from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
import requests
import json
import base64
import datetime
from .models import MpesaPayment
from django.conf import settings


def get_access_token():
    """Get OAuth access token from Safaricom"""
    consumer_key = settings.MPESA_CONSUMER_KEY
    consumer_secret = settings.MPESA_CONSUMER_SECRET
    api_url = "https://sandbox.safaricom.co.ke/oauth/v1/generate?grant_type=client_credentials"

    auth = base64.b64encode(f"{consumer_key}:{consumer_secret}".encode()).decode('utf-8')
    headers = {'Authorization': f'Basic {auth}'}

    try:
        response = requests.get(api_url, headers=headers)
        response.raise_for_status()
        data = response.json()
        return data['access_token']
    except Exception as e:
        print(f"Error getting access token: {e}")
        return None


def generate_password():
    """Generate the M-Pesa API password"""
    shortcode = settings.MPESA_SHORTCODE
    passkey = settings.MPESA_PASSKEY
    timestamp = datetime.datetime.now().strftime('%Y%m%d%H%M%S')
    password_str = f"{shortcode}{passkey}{timestamp}"
    password_bytes = password_str.encode('utf-8')
    return base64.b64encode(password_bytes).decode('utf-8'), timestamp


def payment_view(request):
    """View for handling M-Pesa payment"""
    if request.method == 'POST':
        phone = request.POST.get('phone_number')
        amount = request.POST.get('amount')
        reference = request.POST.get('reference', 'Payment')
        description = request.POST.get('description', 'Payment')

        # Format phone number (remove leading 0 or +254)
        if phone.startswith('0'):
            phone = '254' + phone[1:]
        elif phone.startswith('+254'):
            phone = phone[1:]

        # Create payment record
        payment = MpesaPayment.objects.create(
            phone_number=phone,
            amount=amount,
            reference=reference,
            description=description
        )

        # Get access token
        access_token = get_access_token()
        if not access_token:
            return render(request, 'mpesa_api/paymentmpesa.html', {
                'error': 'Failed to get access token',
                'payment': None
            })

        # Generate password
        password, timestamp = generate_password()

        # Prepare STK Push request
        headers = {
            'Authorization': f'Bearer {access_token}',
            'Content-Type': 'application/json',
        }

        callback_url = settings.MPESA_CALLBACK_URL

        payload = {
            "BusinessShortCode": settings.MPESA_SHORTCODE,
            "Password": password,
            "Timestamp": timestamp,
            "TransactionType": "CustomerPayBillOnline",
            "Amount": int(float(amount)),
            "PartyA": phone,
            "PartyB": settings.MPESA_SHORTCODE,
            "PhoneNumber": phone,
            "CallBackURL": callback_url,
            "AccountReference": reference,
            "TransactionDesc": description
        }

        # Make STK Push request
        try:
            api_url = "https://sandbox.safaricom.co.ke/mpesa/stkpush/v1/processrequest"
            response = requests.post(api_url, json=payload, headers=headers)
            response.raise_for_status()
            res_data = response.json()

            # Save checkout request ID
            if 'CheckoutRequestID' in res_data:
                payment.checkout_request_id = res_data['CheckoutRequestID']
                payment.save()

                return render(request, 'mpesa_api/paymentmpesa.html', {
                    'payment': payment,
                    'success': True,
                    'message': 'Payment request sent. Check your phone.'
                })
            else:
                return render(request, 'mpesa_api/paymentmpesa.html', {
                    'payment': None,
                    'error': 'Failed to initiate payment'
                })

        except Exception as e:
            return render(request, 'mpesa_api/paymentmpesa.html', {
                'payment': None,
                'error': f'Error: {str(e)}'
            })

    # GET request - show form
    return render(request, 'mpesa_api/paymentmpesa.html')


@csrf_exempt
def callback(request):
    """Handle M-Pesa callback"""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)

            # Extract the callback data
            callback_data = data.get('Body', {}).get('stkCallback', {})
            checkout_request_id = callback_data.get('CheckoutRequestID')
            result_code = callback_data.get('ResultCode')

            # Find the payment
            try:
                payment = MpesaPayment.objects.get(checkout_request_id=checkout_request_id)

                if result_code == 0:  # Success
                    payment_data = callback_data.get('CallbackMetadata', {}).get('Item', [])

                    # Extract transaction details
                    for item in payment_data:
                        if item.get('Name') == 'MpesaReceiptNumber':
                            payment.receipt_number = item.get('Value')
                        elif item.get('Name') == 'TransactionId':
                            payment.transaction_id = item.get('Value')

                    payment.status = 'COMPLETED'
                else:
                    payment.status = 'FAILED'

                payment.save()

            except MpesaPayment.DoesNotExist:
                # Payment not found
                pass

            return HttpResponse(status=200)
        except Exception as e:
            return HttpResponse(str(e), status=500)

    return HttpResponse('Method not allowed', status=405)


def check_payment_status(request, checkout_request_id):
    """Check payment status"""
    try:
        payment = MpesaPayment.objects.get(checkout_request_id=checkout_request_id)
        return JsonResponse({
            'status': payment.status,
            'receipt_number': payment.receipt_number,
            'transaction_id': payment.transaction_id
        })
    except MpesaPayment.DoesNotExist:
        return JsonResponse({'error': 'Payment not found'}, status=404)