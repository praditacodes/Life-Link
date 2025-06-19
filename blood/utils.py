import random
from datetime import datetime, timedelta
from twilio.rest import Client
from django.conf import settings
import os
from dotenv import load_dotenv

load_dotenv()

def generate_otp():
    """Generate a 6-digit OTP"""
    return str(random.randint(100000, 999999))

def send_otp_via_sms(phone_number, otp):
    """Send OTP via SMS using Twilio"""
    try:
        account_sid = os.getenv('TWILIO_ACCOUNT_SID')
        auth_token = os.getenv('TWILIO_AUTH_TOKEN')
        twilio_number = os.getenv('TWILIO_PHONE_NUMBER')
        
        client = Client(account_sid, auth_token)
        message = client.messages.create(
            body=f'Your Blood Link verification code is: {otp}',
            from_=twilio_number,
            to=str(phone_number)
        )
        return True
    except Exception as e:
        print(f"Error sending SMS: {str(e)}")
        return False

def is_otp_valid(otp_created_at):
    """Check if OTP is still valid (5 minutes)"""
    if not otp_created_at:
        return False
    return datetime.now() - otp_created_at < timedelta(minutes=5) 