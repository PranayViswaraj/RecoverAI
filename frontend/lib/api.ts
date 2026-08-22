const API = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

async function request(path: string, options?: RequestInit) {
  const res = await fetch(`${API}${path}`, {
    ...options,
    cache: "no-store",
    headers: {
      "Content-Type": "application/json",
      ...(options?.headers || {}),
    },
  });
  if (!res.ok) {
    const body = await res.text();
    throw new Error(body || `HTTP ${res.status}`);
  }
  return res.json();
}

export const api = {
  dashboard: () => request("/api/dashboard"),
  transactions: () => request("/api/transactions"),
  queue: () => request("/api/recovery-queue"),
  detail: (id: string) => request(`/api/transactions/${id}`),
  runAgent: () => request("/api/agent/run", { method: "POST" }),
  execute: (id: string) => request(`/api/recovery/${id}/execute`, { method: "POST" }),
  approve: (id: string) => request(`/api/recovery/${id}/approve`, { method: "POST" }),
};
