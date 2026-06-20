// Thin API client. All calls go through the Vite proxy to the FastAPI backend.
const BASE = "/api";

async function request(path, options = {}) {
  const res = await fetch(BASE + path, {
    headers: { "Content-Type": "application/json" },
    ...options,
  });
  if (!res.ok) {
    let detail = res.statusText;
    try {
      detail = (await res.json()).detail || detail;
    } catch (_) {}
    throw new Error(detail);
  }
  return res.json();
}

export const api = {
  health: () => request("/health"),
  classifierMetrics: () => request("/classifier/metrics"),
  analyze: (subject, body) =>
    request("/classifier/analyze", {
      method: "POST",
      body: JSON.stringify({ subject, body }),
    }),

  templates: () => request("/templates"),
  createTemplate: (t) =>
    request("/templates", { method: "POST", body: JSON.stringify(t) }),

  campaigns: () => request("/campaigns"),
  campaign: (id) => request(`/campaigns/${id}`),
  createCampaign: (c) =>
    request("/campaigns", { method: "POST", body: JSON.stringify(c) }),

  users: () => request("/users"),
  user: (id) => request(`/users/${id}`),

  trainingModules: () => request("/training/modules"),
  completeTraining: (id) =>
    request(`/training/${id}/complete`, { method: "POST" }),

  dashboard: () => request("/dashboard/summary"),
  compliance: () => request("/compliance/report"),
};
