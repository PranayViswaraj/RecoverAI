# RecoverAI — AI Revenue Recovery Agent

**Detect revenue at risk. Decide the intervention. Recover it.**

RecoverAI is an AI-powered revenue recovery agent that identifies failed or abandoned payments still worth pursuing — then analyzes context, predicts recovery probability, selects the right intervention, applies safety guardrails, and tracks the recovered revenue.

> Turn failed payments into measurable recovery opportunities.

---

## The Problem

A failed payment doesn't always mean lost revenue. It could be insufficient funds, a temporary bank decline, an expired card, a timeout, or an abandoned checkout — each recoverable in a different way.

Traditional systems stop at:

```
Payment Failed → Show Failed Transaction
```

RecoverAI turns this into:

```
Payment Failure → Understand → Predict Recovery Probability
→ Select Intervention → Apply Guardrails → Execute
→ Track Outcome → Measure Recovered Revenue
```

---

## What RecoverAI Does

For every failed transaction, RecoverAI evaluates amount, failure reason, customer payment history, and behavior — then produces a structured decision:

| Field | Value |
|---|---|
| Transaction | ₹25,000 |
| Failure | Insufficient Funds |
| Recovery Probability | 77% |
| Expected Recovery | ₹19,250 |
| Recommended Action | Send Payment Link |
| Guardrail | AUTO |

Instead of "failed," RecoverAI sees a **high-value recovery opportunity.**

---

## How It Works

### 1. Detect
Flags failed, abandoned, or at-risk transactions as recovery candidates.

### 2. Understand
Pulls payment context (amount, status, failure reason, history) and customer context (past payments, value, behavior) to separate genuine recovery candidates from risky ones.

### 3. Predict
Estimates recovery probability and expected recovery value:

```
Expected Recovery = Transaction Amount × Recovery Probability
₹25,000 × 0.77 = ₹19,250
```

### 4. Decide
Matches each situation to the right action:

| Situation | Action |
|---|---|
| Insufficient funds | Send payment link |
| Temporary decline | Retry payment |
| Abandoned checkout | Recovery message |
| Expired payment method | Request updated payment |
| High-risk transaction | Human review |
| Low recovery probability | Do not auto-pursue |

### 5. Apply Guardrails
The AI proposes — it doesn't decide alone.

```
AI PROPOSAL → GUARDRAIL CHECK
   ├── LOW RISK  → AUTO EXECUTION
   └── HIGH RISK → HUMAN APPROVAL
        └── EXECUTE → AUDIT TRAIL
```

### 6. Execute
Safe actions run automatically; guarded actions wait for merchant approval.

### 7. Monitor
Tracks recovery status, amount recovered, action taken, and outcome — closing the loop: **Detect → Decide → Act → Recover → Measure.**

---

## Merchant Dashboard

| Metric | Example | Answers |
|---|---|---|
| **Revenue at Risk** | ₹7,29,525 | How much revenue is at risk? |
| **Recoverable** | ₹7,02,028 | How much can realistically be recovered? |
| **Expected Recovery** | ₹4,75,683 | What do we expect to recover? |
| **Recovered** | ₹0 → grows | What have we actually recovered? |

### Recovery Queue
Prioritized by expected recovery value:

| Customer | Amount | Failure | Probability | Action | Guardrail |
|---|---|---|---|---|---|
| Ananya | ₹25,000 | Insufficient funds | 77% | Send Payment Link | AUTO |
| Customer B | ₹12,500 | Bank decline | 64% | Retry Payment | AUTO |
| Customer C | ₹40,000 | High risk | 21% | Review | APPROVAL |

This turns *"here are 100 failed payments"* into *"here are the opportunities most worth acting on."*

---

## Explainable Decisions

Every recommendation comes with a **"Why?"**:

```
Failure:              Insufficient funds
Customer history:     Multiple successful payments
Recovery probability: 77%
Recommended action:   Send Payment Link
Guardrail:            AUTO
Reason:                Strong payment history + recoverable failure type
```

Explainable. Transparent. Auditable.

---

## Architecture

```
Transaction Data + Customer Context
            ↓
     AI Recovery Agent
            ↓
     Structured Decision
            ↓
    Guardrail Validation
            ↓
      Recovery Action
```

**Deterministic Fallback** — works without an OpenAI key via a rule-based engine, so the app stays demoable and predictable even offline:

```
Recovery Request → AI Available?
   ├── YES → OpenAI Agent
   └── NO  → Rule Engine
        └── Structured Decision → Guardrails → Recovery Action
```

---

## Tech Stack

| Layer | Technology |
|---|---|
| Frontend | Next.js + TypeScript |
| Backend | Python + FastAPI |
| Database | SQLite |
| AI | OpenAI Responses API |
| AI Fallback | Deterministic Rule Engine |
| Payments | Razorpay Test Mode |
| Data | Synthetic Transactions |
| Docs | FastAPI / Swagger |

---

## Project Structure

```
RecoverAI/
├── backend/
│   ├── app/
│   │   ├── agent.py
│   │   ├── config.py
│   │   ├── db.py
│   │   ├── main.py
│   │   ├── models.py
│   │   ├── razorpay_client.py
│   │   ├── schemas.py
│   │   ├── seed.py
│   │   └── tools.py
│   ├── data/
│   ├── .env.example
│   └── requirements.txt
├── frontend/
│   ├── app/
│   │   ├── globals.css
│   │   ├── layout.tsx
│   │   └── page.tsx
│   ├── components/Dashboard.tsx
│   ├── lib/api.ts
│   └── package.json
├── docs/images/
└── README.md
```

---

## Getting Started

### Prerequisites
* Python 3.11+
* Node.js 20+
* npm, Git

### Backend
```bash
cd backend
python -m venv .venv
source .venv/bin/activate      # Windows: .venv\Scripts\activate

pip install -r requirements.txt
cp .env.example .env           # Windows: copy .env.example .env

python -m app.seed
uvicorn app.main:app --reload --port 8000
```
Runs at `http://localhost:8000` · Docs at `/docs`

### Frontend
```bash
cd frontend
npm install
cp .env.local.example .env.local   # Windows: copy .env.local.example .env.local
npm run dev
```
Runs at `http://localhost:3000`

---

## Configuration

**OpenAI** (optional — falls back to rule engine if unset)
```env
OPENAI_API_KEY=your_api_key
OPENAI_MODEL=gpt-5.6
```

**Razorpay Test Mode** (optional)
```env
RAZORPAY_KEY_ID=rzp_test_xxxxxxxxxx
RAZORPAY_KEY_SECRET=xxxxxxxxxx
RAZORPAY_WEBHOOK_SECRET=your_webhook_secret
DEMO_MODE=false
```
Keep `DEMO_MODE=true` until the Razorpay flow is ready. **Never commit API keys.**

---

## API Endpoints

```
GET  /api/health
GET  /api/dashboard
GET  /api/transactions
GET  /api/recovery-queue
GET  /api/transactions/{payment_id}

POST /api/agent/run
POST /api/recovery/{payment_id}/execute
POST /api/recovery/{payment_id}/approve
POST /api/webhooks/razorpay
```
Interactive docs: `http://localhost:8000/docs`

---

## Demo Walkthrough

1. Open `http://localhost:3000`
2. Click **Run Recovery Agent**
3. Review the **Recovery Queue** (customer, amount, failure, probability, action, guardrail)
4. Inspect a transaction — failure reason, history, probability, reasoning
5. **Execute** (safe actions) or **Approve & Execute** (guarded actions)
6. Watch the dashboard update: Revenue at Risk → Recoverable → Expected Recovery → Recovered → Recovery Rate

---

## What Makes RecoverAI Different

| System | Says |
|---|---|
| Traditional dashboard | "Payment failed." |
| Basic analytics | "₹25,000 failed due to insufficient funds." |
| Chatbot | "You should contact the customer." |
| **RecoverAI** | "This ₹25,000 payment has a 77% recovery probability. Send a payment link — it satisfies guardrails. Expected recovery: ₹19,250." |

```
DATA → INTELLIGENCE → DECISION → ACTION → OUTCOME
```

---

## Business Value

Shifts merchants from reactive monitoring to proactive recovery — measuring success by **recovered revenue**, not just decisions generated:

* How much revenue is at risk?
* How much is recoverable?
* What should we do?
* How much do we expect to recover?
* How much did we actually recover?

---

## Security & Safety

* AI actions are bounded by application-level rules
* High-risk actions require human approval
* All decisions are recorded and auditable
* Credentials live in environment variables, never in code
* Razorpay integration targets Test Mode only
* Demo Mode uses no real money; data is fully synthetic

> Production deployment would additionally require: authentication, authorization, secret management, rate limiting, monitoring, compliance controls, database security, payment-provider security, and audit infrastructure.

---

## Prototype Scope

Currently a **hackathon-ready prototype** using synthetic data and simulated actions by default, with Razorpay Test Mode available for live payment-link demos.

```
Failed Payment → AI Analysis → Recovery Prediction
→ Intervention Selection → Guardrail Validation
→ Recovery Action → Revenue Tracking
```

---

## Future Possibilities

* Subscription payment recovery
* Checkout abandonment recovery
* Invoice & B2B receivables recovery
* Payment retry optimization
* WhatsApp/SMS & multilingual recovery
* Merchant-specific recovery policies
* Advanced ML-based recovery prediction
* Real-time recovery analytics

---

## Summary

RecoverAI combines Payment Intelligence + AI Reasoning + Recovery Prediction + Financial Guardrails + Bounded Automation into one closed-loop system:

```
REVENUE AT RISK → DETECT → UNDERSTAND → PREDICT → DECIDE
→ GUARDRAILS → ACT → MONITOR → RECOVERED REVENUE
```

**Don't just identify failed payments. Recover the revenue behind them.**
