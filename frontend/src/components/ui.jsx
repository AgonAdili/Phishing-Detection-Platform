import { useEffect, useState } from "react";

export function Spinner() {
  return <div className="spinner" />;
}

export function useFetch(fn, deps = []) {
  const [data, setData] = useState(null);
  const [error, setError] = useState(null);
  const [loading, setLoading] = useState(true);
  const [reloadKey, setReloadKey] = useState(0);

  useEffect(() => {
    let alive = true;
    setLoading(true);
    fn()
      .then((d) => alive && (setData(d), setError(null)))
      .catch((e) => alive && setError(e.message))
      .finally(() => alive && setLoading(false));
    return () => {
      alive = false;
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [...deps, reloadKey]);

  return { data, error, loading, reload: () => setReloadKey((k) => k + 1) };
}

export function RiskBadge({ band, children }) {
  return (
    <span className={`badge dot ${band}`}>
      {children || band}
    </span>
  );
}

export function KpiCard({ icon, label, value, sub, color }) {
  return (
    <div className="card kpi">
      <div className="ico-badge" style={color ? { color } : undefined}>{icon}</div>
      <div className="label">{label}</div>
      <div className="value" style={color ? { color } : undefined}>{value}</div>
      {sub && <div className="delta">{sub}</div>}
    </div>
  );
}

export function Bar({ value, max = 100, color }) {
  const pct = Math.min(100, max ? (value / max) * 100 : 0);
  return (
    <div className="bar-track">
      <div className="bar-fill" style={{ width: `${pct}%`, background: color }} />
    </div>
  );
}

export function bandColor(band) {
  return { low: "#2fbf71", medium: "#f5a623", high: "#ef4d63", untested: "#5b6678" }[band] || "#4f8cff";
}

export function fmtDate(iso) {
  if (!iso) return "—";
  try {
    return new Date(iso).toLocaleDateString(undefined, { month: "short", day: "numeric", year: "numeric" });
  } catch {
    return iso.slice(0, 10);
  }
}

export function ErrorBox({ message }) {
  return (
    <div className="card" style={{ borderColor: "var(--red)" }}>
      <strong style={{ color: "var(--red)" }}>Could not reach the API.</strong>
      <p className="hint" style={{ marginTop: 6 }}>{message}</p>
      <p className="faint" style={{ fontSize: 12 }}>
        Make sure the backend is running: <span className="mono">uvicorn main:app --port 8000</span>
      </p>
    </div>
  );
}
