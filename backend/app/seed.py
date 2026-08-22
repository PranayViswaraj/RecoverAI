import csv
import random
from datetime import datetime, timedelta
from pathlib import Path
from .db import init_db, get_conn

DATA_DIR = Path(__file__).resolve().parent.parent / "data"

NAMES = [
    ("Rahul", "rahul@example.com", "+919800000001"),
    ("Priya", "priya@example.com", "+919800000002"),
    ("Arjun", "arjun@example.com", "+919800000003"),
    ("Meera", "meera@example.com", "+919800000004"),
    ("Karthik", "karthik@example.com", "+919800000005"),
    ("Ananya", "ananya@example.com", "+919800000006"),
    ("Vikram", "vikram@example.com", "+919800000007"),
    ("Neha", "neha@example.com", "+919800000008"),
]

REASONS = [
    "insufficient_funds",
    "bank_declined",
    "expired_card",
    "network_error",
    "abandoned_checkout",
    "suspicious_transaction",
]

def seed():
    init_db()
    conn = get_conn()
    conn.execute("DELETE FROM audit_log")
    conn.execute("DELETE FROM recoveries")
    conn.execute("DELETE FROM transactions")
    conn.execute("DELETE FROM customers")
    conn.execute("DELETE FROM webhook_events")

    random.seed(42)
    now = datetime.utcnow()

    for idx, (name, email, phone) in enumerate(NAMES, 1):
        successes = random.randint(2, 10)
        avg = random.choice([1200, 2500, 4500, 6500, 8500, 12000])
        ltv = successes * avg + random.randint(0, 5000)
        conn.execute(
            """INSERT INTO customers(
               customer_id,name,email,phone,lifetime_value,
               successful_payments,avg_order_value,last_purchase_days_ago,preferred_channel
            ) VALUES(?,?,?,?,?,?,?,?,?)""",
            (
                f"CUST{idx:03d}", name, email, phone, ltv, successes,
                avg, random.randint(2, 60), random.choice(["SMS", "WhatsApp", "EMAIL"])
            ),
        )

    rows = []
    for i in range(1, 101):
        customer_id = f"CUST{random.randint(1, 8):03d}"
        amount = random.choice([499, 899, 1499, 2499, 3999, 4999, 8499, 12400, 18000, 25000])
        reason = random.choices(
            REASONS,
            weights=[25, 18, 15, 12, 15, 5],
            k=1
        )[0]
        timestamp = (now - timedelta(hours=random.randint(1, 120))).isoformat()
        payment_id = f"pay_demo_{i:04d}"
        order_id = f"ORD{1000+i}"
        rows.append({
            "payment_id": payment_id,
            "customer_id": customer_id,
            "order_id": order_id,
            "amount": amount,
            "status": "FAILED",
            "failure_reason": reason,
            "transaction_type": "checkout" if reason == "abandoned_checkout" else "payment",
            "timestamp": timestamp,
        })

        conn.execute(
            """INSERT INTO transactions(
               payment_id,customer_id,order_id,amount,status,failure_reason,transaction_type,timestamp
            ) VALUES(?,?,?,?,?,?,?,?)""",
            (
                payment_id, customer_id, order_id, amount, "FAILED", reason,
                "checkout" if reason == "abandoned_checkout" else "payment", timestamp
            ),
        )

    conn.commit()
    conn.close()

    DATA_DIR.mkdir(exist_ok=True)
    with open(DATA_DIR / "transactions.csv", "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=rows[0].keys())
        writer.writeheader()
        writer.writerows(rows)

    print("Seeded 8 customers and 100 synthetic failed transactions.")
    print(f"CSV written to: {DATA_DIR / 'transactions.csv'}")

if __name__ == "__main__":
    seed()
