import json
import math
import sqlite3
from datetime import datetime
from .db import get_conn
from .razorpay_client import RazorpayClient

def get_customer(customer_id: str):
    conn = get_conn()
    row = conn.execute(
        "SELECT * FROM customers WHERE customer_id = ?", (customer_id,)
    ).fetchone()
    conn.close()
    return dict(row) if row else None

def get_payment(payment_id: str):
    conn = get_conn()
    row = conn.execute(
        """SELECT t.*, c.name, c.email, c.phone, c.lifetime_value,
                  c.successful_payments, c.avg_order_value,
                  c.last_purchase_days_ago, c.preferred_channel
           FROM transactions t
           JOIN customers c ON c.customer_id=t.customer_id
           WHERE t.payment_id=?""",
        (payment_id,),
    ).fetchone()
    conn.close()
    return dict(row) if row else None

def create_payment_link(payment_id: str):
    payment = get_payment(payment_id)
    if not payment:
        raise ValueError("Payment not found")

    client = RazorpayClient()
    result = client.create_payment_link(
        amount_inr=payment["amount"],
        customer_name=payment["name"],
        customer_email=payment["email"],
        customer_phone=payment["phone"],
        reference_id=f"REC-{payment_id}",
        description=f"RecoverAI recovery for {payment['order_id']}",
    )

    conn = get_conn()
    conn.execute(
        """UPDATE recoveries
           SET razorpay_payment_link_id=?, razorpay_payment_link_url=?,
               action_status='EXECUTED', executed_at=CURRENT_TIMESTAMP
           WHERE payment_id=?""",
        (result.get("id"), result.get("short_url"), payment_id),
    )
    conn.execute(
        """INSERT INTO audit_log(payment_id, action, status, details)
           VALUES (?, ?, ?, ?)""",
        (payment_id, "CREATE_PAYMENT_LINK", "SUCCESS", json.dumps(result)),
    )
    conn.commit()
    conn.close()

    return result

def send_message(payment_id: str, channel: str = "SMS"):
    payment = get_payment(payment_id)
    if not payment:
        raise ValueError("Payment not found")
    conn = get_conn()
    conn.execute(
        """UPDATE recoveries SET action_status='EXECUTED', executed_at=CURRENT_TIMESTAMP
           WHERE payment_id=?""",
        (payment_id,),
    )
    conn.execute(
        """INSERT INTO audit_log(payment_id, action, status, details)
           VALUES (?, ?, ?, ?)""",
        (payment_id, f"SEND_{channel.upper()}", "SIMULATED",
         f"Reminder prepared for {payment['name']}")),
    conn.commit()
    conn.close()
    return {"status": "simulated", "channel": channel}

def retry_payment(payment_id: str):
    payment = get_payment(payment_id)
    if not payment:
        raise ValueError("Payment not found")
    conn = get_conn()
    conn.execute(
        """UPDATE recoveries SET action_status='EXECUTED', executed_at=CURRENT_TIMESTAMP
           WHERE payment_id=?""",
        (payment_id,),
    )
    conn.execute(
        """INSERT INTO audit_log(payment_id, action, status, details)
           VALUES (?, ?, ?, ?)""",
        (payment_id, "RETRY_PAYMENT", "SCHEDULED",
         "Retry scheduled for the next eligible window"),
    )
    conn.commit()
    conn.close()
    return {"status": "scheduled", "retry_window": "30 minutes"}

def flag_for_review(payment_id: str, reason: str):
    conn = get_conn()
    conn.execute(
        """UPDATE recoveries SET action_status='ESCALATED'
           WHERE payment_id=?""",
        (payment_id,),
    )
    conn.execute(
        """INSERT INTO audit_log(payment_id, action, status, details)
           VALUES (?, ?, ?, ?)""",
        (payment_id, "FLAG_FOR_REVIEW", "ESCALATED", reason),
    )
    conn.commit()
    conn.close()
    return {"status": "escalated", "reason": reason}

def calculate_recovery(payment: dict):
    amount = float(payment["amount"])
    reason = (payment.get("failure_reason") or "").lower()
    successes = int(payment["successful_payments"])
    ltv = float(payment["lifetime_value"])
    days = int(payment["last_purchase_days_ago"])

    probability = 0.25
    action = "SEND_PAYMENT_LINK"
    cost = 20.0
    risk = 0.10

    if reason == "insufficient_funds":
        probability = 0.72 if successes >= 3 else 0.55
        action = "SEND_PAYMENT_LINK"
        cost = 20
    elif reason == "bank_declined":
        probability = 0.61 if successes >= 5 else 0.45
        action = "RETRY_PAYMENT"
        cost = 5
    elif reason == "expired_card":
        probability = 0.58
        action = "SEND_PAYMENT_LINK"
        cost = 20
    elif reason == "network_error":
        probability = 0.70
        action = "RETRY_PAYMENT"
        cost = 5
    elif reason == "abandoned_checkout":
        probability = 0.64
        action = "SEND_MESSAGE"
        cost = 15
    elif reason == "suspicious_transaction":
        probability = 0.08
        action = "FLAG_FOR_REVIEW"
        cost = 0
        risk = 0.92
    else:
        probability = 0.40

    if ltv > 15000:
        probability += 0.05
    if days <= 14:
        probability += 0.03
    probability = max(0.02, min(probability, 0.95))

    if reason == "suspicious_transaction":
        probability = 0.08

    expected = amount * probability
    roi = (expected - cost) / cost if cost > 0 else 0

    guardrail = "AUTO"
    if risk >= 0.75 or action == "FLAG_FOR_REVIEW":
        guardrail = "HUMAN_APPROVAL"

    explanation = (
        f"Customer has {successes} previous successful payments, "
        f"lifetime value ₹{ltv:,.0f}, and the current failure is "
        f"'{payment.get('failure_reason')}'. "
        f"Estimated recovery probability is {probability:.0%}. "
        f"The selected action is {action.replace('_', ' ').title()} "
        f"because it matches the failure pattern while keeping intervention cost low."
    )

    return {
        "recoverable": probability >= 0.35 and risk < 0.75,
        "recovery_probability": probability,
        "recommended_action": action,
        "explanation": explanation,
        "confidence": min(0.95, 0.68 + successes * 0.03),
        "expected_recovery": expected,
        "action_cost": cost,
        "expected_roi": roi,
        "risk_score": risk,
        "guardrail_status": guardrail,
    }

def save_decision(payment_id: str, decision: dict):
    conn = get_conn()
    conn.execute(
        """INSERT INTO recoveries(
            payment_id,recoverable,recovery_probability,recommended_action,
            explanation,confidence,expected_recovery,action_cost,expected_roi,
            risk_score,guardrail_status,action_status
        ) VALUES(?,?,?,?,?,?,?,?,?,?,?,'PENDING')
        ON CONFLICT(payment_id) DO UPDATE SET
            recoverable=excluded.recoverable,
            recovery_probability=excluded.recovery_probability,
            recommended_action=excluded.recommended_action,
            explanation=excluded.explanation,
            confidence=excluded.confidence,
            expected_recovery=excluded.expected_recovery,
            action_cost=excluded.action_cost,
            expected_roi=excluded.expected_roi,
            risk_score=excluded.risk_score,
            guardrail_status=excluded.guardrail_status
        """,
        (
            payment_id,
            int(decision["recoverable"]),
            decision["recovery_probability"],
            decision["recommended_action"],
            decision["explanation"],
            decision["confidence"],
            decision["expected_recovery"],
            decision["action_cost"],
            decision["expected_roi"],
            decision["risk_score"],
            decision["guardrail_status"],
        ),
    )
    conn.execute(
        """INSERT INTO audit_log(payment_id, action, status, details)
           VALUES (?, ?, ?, ?)""",
        (payment_id, "AI_ANALYSIS", "SUCCESS", json.dumps(decision)),
    )
    conn.commit()
    conn.close()
