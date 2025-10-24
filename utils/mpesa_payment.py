import os
import requests

# Load Confucius M-Pesa number from environment
CONFUCIUS_MPESA_NUMBER = os.getenv('CONFUCIUS_MPESA_NUMBER')

# Placeholder for M-Pesa API credentials (to be set in .env)
MPESA_CONSUMER_KEY = os.getenv('MPESA_CONSUMER_KEY')
MPESA_CONSUMER_SECRET = os.getenv('MPESA_CONSUMER_SECRET')
MPESA_SHORTCODE = os.getenv('MPESA_SHORTCODE')
MPESA_PASSKEY = os.getenv('MPESA_PASSKEY')

# Function to send payment request and OTP to student
# phone_number: student's phone number
# amount: fine amount
# Returns: response from M-Pesa API

def send_mpesa_payment_request(phone_number, amount):
    # This is a simplified placeholder. You need to register for Safaricom Daraja API and use real credentials.
    # See: https://developer.safaricom.co.ke/APIs
    url = "https://sandbox.safaricom.co.ke/mpesa/stkpush/v1/processrequest"
    headers = {"Authorization": "Bearer <access_token>"}
    payload = {
        "BusinessShortCode": MPESA_SHORTCODE,
        "Password": MPESA_PASSKEY,
        "Timestamp": "20251012",  # Use current timestamp
        "TransactionType": "CustomerPayBillOnline",
        "Amount": amount,
        "PartyA": phone_number,
        "PartyB": CONFUCIUS_MPESA_NUMBER,
        "PhoneNumber": phone_number,
        "CallBackURL": "https://yourdomain.com/api/mpesa/callback",
        "AccountReference": "LibraryFine",
        "TransactionDesc": "Library fine payment"
    }
    # response = requests.post(url, json=payload, headers=headers)
    # return response.json()
    return {"status": "sent", "phone_number": phone_number, "amount": amount}

# Example usage:
# send_mpesa_payment_request("0712345678", 500)
