import json
from .config import OPENAI_API_KEY, OPENAI_MODEL
from .db import get_conn
from .tools import get_payment, get_customer, calculate_recovery, save_decision

def _rule_based_decision(payment_id: str):
    payment = get_payment(payment_id)
    if not payment:
        raise ValueError("Payment not found")
    return calculate_recovery(payment)

def _openai_decision(payment_id: str):
    from openai import OpenAI

    payment = get_payment(payment_id)
    customer = get_customer(payment["customer_id"])

    client = OpenAI(api_key=OPENAI_API_KEY)

    tools = [
        {
            "type": "function",
            "name": "get_customer",
            "description": "Retrieve customer history and value.",
            "parameters": {
                "type": "object",
                "properties": {"customer_id": {"type": "string"}},
                "required": ["customer_id"],
                "additionalProperties": False,
            },
            "strict": True,
        },
        {
            "type": "function",
            "name": "get_payment",
            "description": "Retrieve the failed payment and its context.",
            "parameters": {
                "type": "object",
                "properties": {"payment_id": {"type": "string"}},
                "required": ["payment_id"],
                "additionalProperties": False,
            },
            "strict": True,
        },
    ]

    instructions = """
You are RecoverAI, a bounded revenue recovery decision agent.
You are NOT a chatbot. Your job is to select one recovery action for a failed payment.

Allowed actions:
- SEND_PAYMENT_LINK
- SEND_MESSAGE
- RETRY_PAYMENT
- FLAG_FOR_REVIEW

Rules:
- Never automatically recover suspicious/high-risk transactions.
- Never invent customer facts.
- Prefer the lowest-cost action that has a reasonable recovery probability.
- Return ONLY valid JSON with:
  recoverable, recovery_probability, recommended_action, explanation,
  confidence, expected_recovery, action_cost, expected_roi, risk_score,
  guardrail_status.
"""

    prompt = json.dumps({"payment": payment, "customer": customer}, default=str)

    response = client.responses.create(
        model=OPENAI_MODEL,
        instructions=instructions,
        input=prompt,
        tools=tools,
        tool_choice="auto",
    )

    # This demo uses customer/payment data already supplied in the prompt.
    # Tool definitions are present so the model can use them when needed.
    text = response.output_text.strip()
    if text.startswith("```"):
        text = text.strip("`")
        text = text.replace("json", "", 1).strip()
    decision = json.loads(text)

    # Enforce server-side guardrails even if the model returns a bad value.
    if decision.get("risk_score", 0) >= 0.75:
        decision["guardrail_status"] = "HUMAN_APPROVAL"
        decision["recommended_action"] = "FLAG_FOR_REVIEW"

    return decision

def analyze_payment(payment_id: str):
    if OPENAI_API_KEY:
        try:
            decision = _openai_decision(payment_id)
        except Exception:
            decision = _rule_based_decision(payment_id)
    else:
        decision = _rule_based_decision(payment_id)

    save_decision(payment_id, decision)
    return decision

def run_agent(limit: int = 100):
    conn = get_conn()
    rows = conn.execute(
        """SELECT payment_id FROM transactions
           WHERE status='FAILED'
           ORDER BY amount DESC LIMIT ?""",
        (limit,),
    ).fetchall()
    conn.close()

    decisions = []
    for row in rows:
        decisions.append({
            "payment_id": row["payment_id"],
            "decision": analyze_payment(row["payment_id"]),
        })
    return decisions
