import time
import requests
from .config import (
    DEMO_MODE,
    RAZORPAY_KEY_ID,
    RAZORPAY_KEY_SECRET,
)

BASE_URL = "https://api.razorpay.com/v1"

class RazorpayClient:
    def __init__(self):
        self.demo_mode = DEMO_MODE
        self.key_id = RAZORPAY_KEY_ID
        self.key_secret = RAZORPAY_KEY_SECRET

    def create_payment_link(self, *, amount_inr: float, customer_name: str,
                            customer_email: str | None, customer_phone: str | None,
                            reference_id: str, description: str):
        amount_paise = int(round(amount_inr * 100))

        if self.demo_mode or not self.key_id or not self.key_secret:
            return {
                "id": f"plink_demo_{reference_id}",
                "short_url": f"https://rzp.io/i/demo-{reference_id.lower()}",
                "status": "created",
                "demo": True,
            }

        payload = {
            "amount": amount_paise,
            "currency": "INR",
            "accept_partial": False,
            "reference_id": reference_id,
            "description": description,
            "customer": {
                "name": customer_name,
                "email": customer_email,
                "contact": customer_phone,
            },
            "expire_by": int(time.time()) + 24 * 60 * 60,
            "notify": {
                "sms": False,
                "email": False,
            },
        }

        # Remove empty customer fields.
        payload["customer"] = {k: v for k, v in payload["customer"].items() if v}

        response = requests.post(
            f"{BASE_URL}/payment_links",
            auth=(self.key_id, self.key_secret),
            json=payload,
            timeout=20,
        )
        response.raise_for_status()
        return response.json()
