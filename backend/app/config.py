import os
from dotenv import load_dotenv

load_dotenv()

APP_NAME = os.getenv("APP_NAME", "RecoverAI")
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./recoverai.db")

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-5.6")

DEMO_MODE = os.getenv("DEMO_MODE", "true").lower() == "true"

RAZORPAY_KEY_ID = os.getenv("RAZORPAY_KEY_ID", "")
RAZORPAY_KEY_SECRET = os.getenv("RAZORPAY_KEY_SECRET", "")
RAZORPAY_WEBHOOK_SECRET = os.getenv("RAZORPAY_WEBHOOK_SECRET", "")

MAX_AUTO_DISCOUNT_PERCENT = float(os.getenv("MAX_AUTO_DISCOUNT_PERCENT", "10"))
MAX_AUTO_REFUND_INR = float(os.getenv("MAX_AUTO_REFUND_INR", "5000"))
HIGH_RISK_THRESHOLD = float(os.getenv("HIGH_RISK_THRESHOLD", "0.75"))

FRONTEND_ORIGIN = os.getenv("FRONTEND_ORIGIN", "http://localhost:3000")
