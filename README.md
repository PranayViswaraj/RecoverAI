# RecoverAI — Autonomous Revenue Recovery Agent

RecoverAI is a hackathon-ready prototype for the **AI Revenue Recovery** track.

It detects revenue at risk, analyzes the reason, estimates recovery probability, selects a bounded intervention, executes a simulated or Razorpay Test Mode action, records the result, and exposes the recovery metrics in a merchant dashboard.

## Architecture

```text
Next.js Dashboard
       |
       v
    FastAPI
       |
       +--> SQLite
       |
       +--> Revenue Agent
       |      +--> customer/payment tools
       |      +--> recovery decision
       |      +--> ROI + confidence
       |      +--> guardrails
       |
       +--> Razorpay Test Mode (optional)
       |
       +--> Webhook / payment_link.paid
```

## Stack

- Frontend: Next.js + TypeScript + CSS
- Backend: Python + FastAPI
- Database: SQLite
- AI: OpenAI Responses API with function tools (optional; rule-based fallback is included)
- Payments: Razorpay Test Mode / Payment Links (optional)
- Dataset: synthetic transactions generated for the demo

## Prerequisites

- Windows 10/11, macOS, or Linux
- Python 3.11+
- Node.js 20+
- npm
- Git
- A browser
- Optional: Razorpay Test Mode account and API keys
- Optional: OpenAI API key

## 1. Start the backend

Windows PowerShell:

```powershell
cd backend
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
copy .env.example .env
python -m app.seed
uvicorn app.main:app --reload --port 8000
```

If PowerShell blocks activation:

```powershell
Set-ExecutionPolicy -Scope Process Bypass
.\.venv\Scripts\Activate.ps1
```

macOS/Linux:

```bash
cd backend
python3.11 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
python -m app.seed
uvicorn app.main:app --reload --port 8000
```

Backend:
- http://localhost:8000
- Swagger API docs: http://localhost:8000/docs

## 2. Start the frontend

Open a second terminal:

```powershell
cd frontend
npm install
copy .env.local.example .env.local
npm run dev
```

Open:
- http://localhost:3000

## 3. First demo

1. Open the dashboard.
2. Click **Run Recovery Agent**.
3. Watch the simulation process the synthetic failed payments.
4. Open **Recovery Queue** to see recommendations.
5. Click a transaction to see the **Why?** explanation.
6. Use **Execute** on safe actions.
7. Use **Approve & Execute** for guarded actions.
8. Watch Revenue at Risk, Recoverable Revenue, Recovered Revenue and Recovery Rate change.

## 4. OpenAI mode

If `OPENAI_API_KEY` is set, the backend can use an OpenAI model for structured recovery decisions.

Set in `backend/.env`:

```env
OPENAI_API_KEY=your_key
OPENAI_MODEL=gpt-5.6
```

If the key is absent or the call fails, RecoverAI automatically uses the deterministic rule engine. This keeps the demo runnable without an LLM.

## 5. Razorpay Test Mode

Set:

```env
RAZORPAY_KEY_ID=rzp_test_xxxxxxxxxx
RAZORPAY_KEY_SECRET=xxxxxxxxxx
RAZORPAY_WEBHOOK_SECRET=your_webhook_secret
DEMO_MODE=false
```

The application only creates real payment links when `DEMO_MODE=false`.

The code uses the Razorpay Payment Links API. For a hackathon, keep all keys in `.env` and never commit them.

### Webhook

The endpoint is:

```text
POST /api/webhooks/razorpay
```

For local webhook testing, expose port 8000 with a tunnel and configure the resulting HTTPS URL in Razorpay Test Mode.

The webhook handler:
- verifies `X-Razorpay-Signature`
- checks `x-razorpay-event-id` for duplicates
- handles `payment_link.paid`
- updates the associated recovery record

## 6. API endpoints

```text
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

## 7. Project structure

```text
recoverai/
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
│   │   ├── tools.py
│   │   └── __init__.py
│   ├── data/
│   ├── .env.example
│   └── requirements.txt
├── frontend/
│   ├── app/
│   │   ├── globals.css
│   │   ├── layout.tsx
│   │   └── page.tsx
│   ├── components/
│   │   └── Dashboard.tsx
│   ├── lib/
│   │   └── api.ts
│   ├── package.json
│   ├── tsconfig.json
│   ├── next-env.d.ts
│   └── .env.local.example
└── README.md
```

## What makes the project defensible in an interview

Do not describe it as "a chatbot".

Describe the closed loop:

**Detect → Understand → Predict → Decide → Act → Monitor**

The agent is bounded by rules:
- suspicious/high-risk payments are not auto-recovered
- discounts above the configured threshold require approval
- refunds above the configured threshold require approval
- every action is written to the audit trail
- every recovery decision has a reason, confidence, expected recovery and ROI

## 3-minute demo script

**0:00–0:30 — Problem**

"Payment failure is not the end of a transaction. It is a revenue-recovery decision. RecoverAI finds that lost revenue and chooses the next best action."

**0:30–1:15 — Live agent**

Click Run Recovery Agent.

Show:
- transactions scanned
- failed payments
- recoverable amount
- expected recovery
- actions selected

**1:15–2:15 — Explainability**

Open one transaction.

Show:
- failure reason
- customer history
- recovery probability
- expected recovery
- why the action was selected
- guardrail status

**2:15–2:45 — Execute**

Create a test payment link or run the simulated action.

Show the action audit trail.

**2:45–3:00 — Close**

"We are not using AI to tell a merchant what happened. We are using AI to decide and execute the next bounded revenue-recovery action."

## Important scope note

This is a prototype. The dataset is synthetic. The default mode simulates payment actions so the project can be demonstrated safely. Real Razorpay integration is optional and should remain in Test Mode for the hackathon.
