# credentials.py
import base64
import requests
from requests.auth import HTTPBasicAuth
import datetime
from dotenv import load_dotenv
import os
from django.conf import settings
load_dotenv()

class MpesaAccessToken:
    @staticmethod
    def get_access_token():
        # Daraja Sandbox credentials
        consumer_key = settings.MPESA_CONSUMER_KEY
        consumer_secret = settings.MPESA_CONSUMER_SECRET
        api_url = 'https://sandbox.safaricom.co.ke/oauth/v1/generate?grant_type=client_credentials'
        response = requests.get(api_url, auth=HTTPBasicAuth(consumer_key, consumer_secret))
        json_response = response.json()
        return json_response['access_token']

    @classmethod
    def validated_mpesa_access_token(cls):
        return cls.get_access_token()

class LipanaMpesaPpassword:
    # Daraja Sandbox credentials
    Business_short_code = '174379'
    Shortcode_password = settings.MPESA_PASSKEY

    @staticmethod
    def get_lipa_time():
        return datetime.datetime.now().strftime('%Y%m%d%H%M%S')

    @property
    def decode_password(self):
        lipa_time = self.get_lipa_time()
        password = f"{self.Business_short_code}{self.Shortcode_password}{lipa_time}"
        return base64.b64encode(password.encode()).decode()
