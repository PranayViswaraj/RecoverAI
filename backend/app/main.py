import hashlib
import hmac
import json
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware

from .config import (
    APP_NAME, FRONTEND_ORIGIN, RAZORPAY_WEBHOOK_SECRET
)
from .db import init_db, get_conn
from .agent import run_agent, analyze_payment
from .tools import (
    get_payment, create_payment_link, send_message,
    retry_payment, flag_for_review
)

app = FastAPI(title=APP_NAME, version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[FRONTEND_ORIGIN, "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
def startup():
    init_db()

@app.get("/api/health")
def health():
    return {"status": "ok", "service": APP_NAME}

@app.get("/api/dashboard")
def dashboard():
    conn = get_conn()
    revenue_at_risk = conn.execute(
        "SELECT COALESCE(SUM(amount),0) FROM transactions WHERE status='FAILED'"
    ).fetchone()[0]
    recoverable = conn.execute(
        """SELECT COALESCE(SUM(t.amount),0)
           FROM transactions t JOIN recoveries r ON r.payment_id=t.payment_id
           WHERE r.recoverable=1 AND r.action_status != 'RECOVERED'"""
    ).fetchone()[0]
    recovered = conn.execute(
        "SELECT COALESCE(SUM(recovered_amount),0) FROM recoveries"
    ).fetchone()[0]
    failed = conn.execute(
        "SELECT COUNT(*) FROM transactions WHERE status='FAILED'"
    ).fetchone()[0]
    recoverable_count = conn.execute(
        "SELECT COUNT(*) FROM recoveries WHERE recoverable=1"
    ).fetchone()[0]
    pending = conn.execute(
        "SELECT COUNT(*) FROM recoveries WHERE action_status='PENDING'"
    ).fetchone()[0]
    escalated = conn.execute(
        "SELECT COUNT(*) FROM recoveries WHERE action_status='ESCALATED' OR guardrail_status='HUMAN_APPROVAL'"
    ).fetchone()[0]
    expected = conn.execute(
        "SELECT COALESCE(SUM(expected_recovery),0) FROM recoveries WHERE action_status='PENDING'"
    ).fetchone()[0]
    conn.close()

    recovery_rate = (recovered / revenue_at_risk * 100) if revenue_at_risk else 0

    return {
        "revenue_at_risk": revenue_at_risk,
        "recoverable_revenue": recoverable,
        "recovered_revenue": recovered,
        "recovery_rate": recovery_rate,
        "failed_payments": failed,
        "recoverable_count": recoverable_count,
        "pending_actions": pending,
        "escalated_count": escalated,
        "expected_recovery": expected,
    }

@app.get("/api/transactions")
def transactions():
    conn = get_conn()
    rows = conn.execute(
        """SELECT t.*, c.name, c.lifetime_value,
                  r.recoverable, r.recovery_probability,
                  r.recommended_action, r.guardrail_status, r.action_status,
                  r.expected_recovery, r.expected_roi, r.confidence
           FROM transactions t
           JOIN customers c ON c.customer_id=t.customer_id
           LEFT JOIN recoveries r ON r.payment_id=t.payment_id
           ORDER BY t.amount DESC"""
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]

@app.get("/api/recovery-queue")
def recovery_queue():
    conn = get_conn()
    rows = conn.execute(
        """SELECT t.payment_id,t.order_id,t.amount,t.failure_reason,
                  c.name,c.lifetime_value,c.successful_payments,
                  r.*
           FROM transactions t
           JOIN customers c ON c.customer_id=t.customer_id
           JOIN recoveries r ON r.payment_id=t.payment_id
           WHERE r.recoverable=1
           ORDER BY r.expected_recovery DESC"""
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]

@app.get("/api/transactions/{payment_id}")
def transaction_detail(payment_id: str):
    conn = get_conn()
    row = conn.execute(
        """SELECT t.*, c.name,c.email,c.phone,c.lifetime_value,
                  c.successful_payments,c.avg_order_value,c.last_purchase_days_ago,
                  r.*
           FROM transactions t
           JOIN customers c ON c.customer_id=t.customer_id
           LEFT JOIN recoveries r ON r.payment_id=t.payment_id
           WHERE t.payment_id=?""",
        (payment_id,),
    ).fetchone()
    audit = conn.execute(
        """SELECT * FROM audit_log WHERE payment_id=?
           ORDER BY created_at DESC""",
        (payment_id,),
    ).fetchall()
    conn.close()

    if not row:
        raise HTTPException(404, "Payment not found")
    result = dict(row)
    result["audit"] = [dict(a) for a in audit]
    return result

@app.post("/api/agent/run")
def agent_run():
    result = run_agent()
    return {
        "status": "completed",
        "processed": len(result),
        "results": result,
    }

@app.post("/api/recovery/{payment_id}/execute")
def execute_recovery(payment_id: str):
    conn = get_conn()
    recovery = conn.execute(
        "SELECT * FROM recoveries WHERE payment_id=?", (payment_id,)
    ).fetchone()
    conn.close()

    if not recovery:
        analyze_payment(payment_id)
        conn = get_conn()
        recovery = conn.execute(
            "SELECT * FROM recoveries WHERE payment_id=?", (payment_id,)
        ).fetchone()
        conn.close()

    if not recovery:
        raise HTTPException(404, "Recovery decision not found")

    if recovery["guardrail_status"] == "HUMAN_APPROVAL":
        raise HTTPException(403, "Human approval required before executing this action")

    action = recovery["recommended_action"]

    if action == "SEND_PAYMENT_LINK":
        result = create_payment_link(payment_id)
        return {
            "payment_id": payment_id,
            "action": action,
            "status": "executed",
            "message": "Payment link created.",
            "payment_link_url": result.get("short_url"),
        }
    if action == "SEND_MESSAGE":
        result = send_message(payment_id)
        return {
            "payment_id": payment_id,
            "action": action,
            "status": "simulated",
            "message": "Customer reminder simulated.",
        }
    if action == "RETRY_PAYMENT":
        result = retry_payment(payment_id)
        return {
            "payment_id": payment_id,
            "action": action,
            "status": "scheduled",
            "message": "Payment retry scheduled.",
        }
    if action == "FLAG_FOR_REVIEW":
        result = flag_for_review(payment_id, "Agent identified a high-risk transaction.")
        return {
            "payment_id": payment_id,
            "action": action,
            "status": "escalated",
            "message": "Escalated for merchant review.",
        }

    raise HTTPException(400, f"Unsupported action: {action}")

@app.post("/api/recovery/{payment_id}/approve")
def approve_recovery(payment_id: str):
    conn = get_conn()
    row = conn.execute(
        "SELECT * FROM recoveries WHERE payment_id=?", (payment_id,)
    ).fetchone()
    conn.close()
    if not row:
        raise HTTPException(404, "Recovery decision not found")

    # Approval is explicit. For high-risk items, the safe outcome remains escalation.
    if row["recommended_action"] == "FLAG_FOR_REVIEW":
        flag_for_review(payment_id, "Merchant reviewed and retained the escalation.")
        return {"status": "approved", "action": "FLAG_FOR_REVIEW"}

    conn = get_conn()
    conn.execute(
        "UPDATE recoveries SET guardrail_status='AUTO' WHERE payment_id=?",
        (payment_id,),
    )
    conn.commit()
    conn.close()

    return execute_recovery(payment_id)

@app.post("/api/webhooks/razorpay")
async def razorpay_webhook(request: Request):
    raw = await request.body()
    signature = request.headers.get("X-Razorpay-Signature", "")
    event_id = request.headers.get("x-razorpay-event-id", "")

    if RAZORPAY_WEBHOOK_SECRET:
        expected = hmac.new(
            RAZORPAY_WEBHOOK_SECRET.encode(),
            raw,
            hashlib.sha256,
        ).hexdigest()
        if not hmac.compare_digest(expected, signature):
            raise HTTPException(400, "Invalid webhook signature")

    conn = get_conn()
    if event_id:
        existing = conn.execute(
            "SELECT event_id FROM webhook_events WHERE event_id=?",
            (event_id,),
        ).fetchone()
        if existing:
            conn.close()
            return {"status": "duplicate_ignored"}

    body = json.loads(raw.decode("utf-8"))
    event_type = body.get("event", "unknown")

    if event_id:
        conn.execute(
            "INSERT INTO webhook_events(event_id,event_type) VALUES(?,?)",
            (event_id, event_type),
        )

    if event_type == "payment_link.paid":
        payload = body.get("payload", {})
        payment_link = payload.get("payment_link", {}).get("entity", {})
        reference_id = payment_link.get("reference_id", "")
        payment_id = reference_id.replace("REC-", "") if reference_id.startswith("REC-") else None

        if payment_id:
            amount = payment_link.get("amount_paid", payment_link.get("amount", 0)) / 100
            conn.execute(
                """UPDATE recoveries
                   SET action_status='RECOVERED', recovered_amount=?,
                       executed_at=CURRENT_TIMESTAMP
                   WHERE payment_id=?""",
                (amount, payment_id),
            )
            conn.execute(
                """INSERT INTO audit_log(payment_id,action,status,details)
                   VALUES(?,?,?,?)""",
                (payment_id, "PAYMENT_RECOVERED", "SUCCESS", json.dumps({
                    "event": event_type, "amount": amount
                })),
            )

    conn.commit()
    conn.close()
    return {"status": "processed", "event": event_type}
