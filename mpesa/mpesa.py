from rest_framework.response import Response
from rest_framework import status
import requests
import json
from django.http import JsonResponse
from requests.auth import HTTPBasicAuth
from .models import MpesaPayment
from .credentials import MpesaAccessToken, LipanaMpesaPpassword
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
import logging
from django.conf import settings
from django.shortcuts import render, redirect

logger = logging.getLogger(__name__)

@csrf_exempt
def StkPushView(request):
    if request.method == "POST":
            # Extract validated data
            phone_number = request.POST['phone_number']
            amount = request.POST['amount']

            # Get access token
            access_token = MpesaAccessToken.validated_mpesa_access_token()
            print(access_token)
            api_url = "https://sandbox.safaricom.co.ke/mpesa/stkpush/v1/processrequest"
            headers = {"Authorization": f"Bearer {access_token}"}
            # Prepare request data
            request_data = {
                "BusinessShortCode": LipanaMpesaPpassword.Business_short_code,
                "Password": LipanaMpesaPpassword().decode_password,
                "Timestamp": LipanaMpesaPpassword.get_lipa_time(),
                "TransactionType": "CustomerPayBillOnline",
                "Amount": int(amount),
                "PartyA": int(phone_number),
                "PartyB": LipanaMpesaPpassword.Business_short_code,
                "PhoneNumber": int(phone_number),
                "CallBackURL": settings.MPESA_CALLBACK_URL,
                "AccountReference": "Reference",
                "TransactionDesc": "Reference"
            }

            # Make STK Push request
            response = requests.post(api_url, json=request_data, headers=headers)
            response_data = response.json()

            # Handle response
            if response_data.get('ResponseCode') == '0':
                return JsonResponse({'message': 'STK Push initiated successfully', 'data': response_data}, status=status.HTTP_200_OK)
            else:
                return JsonResponse({'message': 'STK Push failed', 'data': response_data}, status=status.HTTP_400_BAD_REQUEST)

        # If data is invalid
    return render(request, 'index.html')


# @method_decorator(csrf_exempt, name='dispatch')
@csrf_exempt
def mpesa_callback(request):
    if request.method == 'POST':
        try:
            # Parse the incoming JSON
            callback_data = json.loads(request.body)
            logger.info("Callback received: %s", callback_data)

            stk_callback = callback_data['Body']['stkCallback']
            merchant_request_id = stk_callback.get('MerchantRequestID')
            checkout_request_id = stk_callback.get('CheckoutRequestID')
            response_code = stk_callback.get('ResultCode', -1)  # Default to -1 if missing
            response_description = stk_callback.get('ResultDesc', 'No description')

            # Only process and store data if the payment was successful (response_code == 0)
            if response_code == 0:
                callback_metadata = stk_callback.get('CallbackMetadata', {}).get('Item', [])

                # Initialize default values
                amount = 0
                phone_number = ''
                reference = ''
                receipt_number = ''
                transaction_date = ''

                # Extract payment details from metadata
                for item in callback_metadata:
                    if item.get('Name') == 'Amount':
                        amount = item.get('Value', 0)
                    elif item.get('Name') == 'MpesaReceiptNumber':
                        receipt_number = item.get('Value', '')
                    elif item.get('Name') == 'PhoneNumber':
                        phone_number = item.get('Value', '')
                    elif item.get('Name') == 'TransactionDate':
                        transaction_date = item.get('Value', '')

                MpesaPayment.objects.create(
                        amount=amount,
                        reference=reference,
                )
                logger.info("New transaction created for CheckoutRequestID: %s", checkout_request_id)

                return JsonResponse({'message': 'Payment successful and processed'}, status=200)

            else:
                # Log and respond for failed or canceled payments
                logger.warning(
                    "Payment not successful (ResultCode: %d, ResultDesc: %s) for CheckoutRequestID: %s",
                    response_code, response_description, checkout_request_id
                )
                return JsonResponse({
                    'message': 'Payment not successful',
                    'data': {
                        'result_code': response_code,
                        'result_description': response_description
                    }
                }, status=200)

        except KeyError as e:
            logger.error("Missing key in callback data: %s", str(e))
            return JsonResponse({'error': f'Missing key: {str(e)}'}, status=400)
        except json.JSONDecodeError:
            logger.error("Invalid JSON received in callback")
            return JsonResponse({'error': 'Invalid JSON'}, status=400)
        except Exception as e:
            logger.error("Unexpected error: %s", str(e))
            return JsonResponse({'error': str(e)}, status=500)
    else:
        return JsonResponse({'error': 'Invalid request method'}, status=405)