"use client";

declare namespace JSX {
  interface IntrinsicElements {
    [elementName: string]: any;
  }
}

import { useEffect, useMemo, useState } from "react";
import { api } from "../lib/api";

type DashboardData = {
  revenue_at_risk: number;
  recoverable_revenue: number;
  recovered_revenue: number;
  recovery_rate: number;
  failed_payments: number;
  recoverable_count: number;
  pending_actions: number;
  escalated_count: number;
  expected_recovery: number;
};

type QueueItem = {
  payment_id: string;
  order_id: string;
  amount: number;
  failure_reason: string;
  name: string;
  lifetime_value: number;
  successful_payments: number;
  recommended_action: string;
  recovery_probability: number;
  confidence: number;
  expected_recovery: number;
  expected_roi: number;
  guardrail_status: string;
  action_status: string;
  explanation: string;
};

const money = (n: number) =>
  new Intl.NumberFormat("en-IN", {
    style: "currency",
    currency: "INR",
    maximumFractionDigits: 0,
  }).format(n || 0);

function Stat({ label, value, note }: { label: string; value: string; note: string }) {
  return (
    <div className="stat">
      <div className="muted">{label}</div>
      <div className="statValue">{value}</div>
      <div className="small">{note}</div>
    </div>
  );
}

export default function Dashboard() {
  const [data, setData] = useState<DashboardData | null>(null);
  const [queue, setQueue] = useState<QueueItem[]>([]);
  const [selected, setSelected] = useState<QueueItem | null>(null);
  const [running, setRunning] = useState(false);
  const [message, setMessage] = useState("");

  async function refresh() {
    const [d, q] = await Promise.all([api.dashboard(), api.queue()]);
    setData(d);
    setQueue(q);
    if (selected) {
      const latest = q.find((x: QueueItem) => x.payment_id === selected.payment_id);
      setSelected(latest || null);
    }
  }

  useEffect(() => {
    refresh().catch((e) => setMessage(e.message));
  }, []);

  async function runAgent() {
    setRunning(true);
    setMessage("Scanning transactions → analyzing failures → choosing actions...");
    try {
      await api.runAgent();
      await refresh();
      setMessage("Agent run completed. Recovery decisions are ready.");
    } catch (e: any) {
      setMessage(e.message);
    } finally {
      setRunning(false);
    }
  }

  async function execute(id: string) {
    try {
      const result = await api.execute(id);
      setMessage(result.message || "Action executed.");
      await refresh();
    } catch (e: any) {
      try {
        const parsed = JSON.parse(e.message);
        setMessage(parsed.detail || "Human approval required.");
      } catch {
        setMessage("Action could not be executed.");
      }
    }
  }

  async function approve(id: string) {
    try {
      const result = await api.approve(id);
      setMessage(result.action === "FLAG_FOR_REVIEW" ? "Escalation retained." : "Approved action executed.");
      await refresh();
    } catch (e: any) {
      setMessage(e.message);
    }
  }

  const top = useMemo(() => queue.slice(0, 8), [queue]);

  return (
    <main className="shell">
      <header className="topbar">
        <div>
          <div className="eyebrow">TRACK 03 · AI REVENUE RECOVERY</div>
          <h1>RecoverAI</h1>
          <p className="subtitle">Detect revenue at risk. Decide the intervention. Recover it.</p>
        </div>
        <button className="primary" onClick={runAgent} disabled={running}>
          {running ? "Running Agent..." : "▶ Run Recovery Agent"}
        </button>
      </header>

      {message && <div className="toast">{message}</div>}

      <section className="stats">
        <Stat label="Revenue at Risk" value={money(data?.revenue_at_risk || 0)} note={`${data?.failed_payments || 0} failed transactions`} />
        <Stat label="Recoverable" value={money(data?.recoverable_revenue || 0)} note={`${data?.recoverable_count || 0} candidates`} />
        <Stat label="Expected Recovery" value={money(data?.expected_recovery || 0)} note="Current decision queue" />
        <Stat label="Recovered" value={money(data?.recovered_revenue || 0)} note={`${(data?.recovery_rate || 0).toFixed(1)}% recovery rate`} />
      </section>

      <section className="grid">
        <div className="panel">
          <div className="panelHead">
            <div>
              <h2>Recovery Queue</h2>
              <p className="muted">Highest expected recovery first</p>
            </div>
            <span className="pill">{queue.length} candidates</span>
          </div>

          <div className="tableWrap">
            <table>
              <thead>
                <tr>
                  <th>Customer</th>
                  <th>Amount</th>
                  <th>Failure</th>
                  <th>Probability</th>
                  <th>Action</th>
                  <th>Guardrail</th>
                </tr>
              </thead>
              <tbody>
                {top.map((item) => (
                  <tr key={item.payment_id} onClick={() => setSelected(item)}>
                    <td>
                      <b>{item.name}</b>
                      <div className="small">{item.order_id}</div>
                    </td>
                    <td>{money(item.amount)}</td>
                    <td>{item.failure_reason.replaceAll("_", " ")}</td>
                    <td>{(item.recovery_probability * 100).toFixed(0)}%</td>
                    <td><span className="action">{item.recommended_action.replaceAll("_", " ")}</span></td>
                    <td>
                      <span className={item.guardrail_status === "AUTO" ? "ok" : "warn"}>
                        {item.guardrail_status === "AUTO" ? "AUTO" : "APPROVAL"}
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>

        <aside className="panel detail">
          <div className="panelHead">
            <div>
              <h2>Why?</h2>
              <p className="muted">Explainable AI decision</p>
            </div>
          </div>

          {!selected ? (
            <div className="empty">Select a recovery candidate to inspect the decision.</div>
          ) : (
            <>
              <div className="decision">
                <div className="muted">AI RECOMMENDATION</div>
                <div className="bigAction">{selected.recommended_action.replaceAll("_", " ")}</div>
                <p>{selected.explanation}</p>
              </div>

              <div className="miniGrid">
                <div><span>Recovery probability</span><b>{(selected.recovery_probability * 100).toFixed(0)}%</b></div>
                <div><span>Confidence</span><b>{(selected.confidence * 100).toFixed(0)}%</b></div>
                <div><span>Expected recovery</span><b>{money(selected.expected_recovery)}</b></div>
                <div><span>Expected ROI</span><b>{selected.expected_roi.toFixed(1)}x</b></div>
              </div>

              <div className="customerCard">
                <div><b>{selected.name}</b></div>
                <div className="small">Lifetime value: {money(selected.lifetime_value)}</div>
                <div className="small">{selected.successful_payments} previous successful payments</div>
              </div>

              <div className="buttons">
                {selected.guardrail_status === "AUTO" ? (
                  <button className="primary full" onClick={() => execute(selected.payment_id)}>
                    Execute {selected.recommended_action.replaceAll("_", " ")}
                  </button>
                ) : (
                  <button className="warnButton full" onClick={() => approve(selected.payment_id)}>
                    Approve / Escalate
                  </button>
                )}
              </div>
            </>
          )}
        </aside>
      </section>

      <section className="bottom">
        <div className="flow">
          <span>DETECT</span><i>→</i><span>UNDERSTAND</span><i>→</i><span>PREDICT</span><i>→</i><span>ACT</span><i>→</i><span>MONITOR</span>
        </div>
        <p className="muted center">Bounded automation with audit trails and human approval for risky actions.</p>
      </section>
    </main>
  );
}
