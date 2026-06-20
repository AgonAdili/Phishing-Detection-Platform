import { useMemo, useState } from "react";
import { useNavigate } from "react-router-dom";
import { api } from "../api";
import { Bar, ErrorBox, RiskBadge, Spinner, bandColor, useFetch } from "../components/ui";

export default function Users() {
  const nav = useNavigate();
  const { data, error, loading } = useFetch(() => api.users());
  const [q, setQ] = useState("");
  const [band, setBand] = useState("all");

  const filtered = useMemo(() => {
    if (!data) return [];
    return data.filter((u) => {
      const matchQ = !q || u.name.toLowerCase().includes(q.toLowerCase()) ||
        u.department.toLowerCase().includes(q.toLowerCase());
      const matchB = band === "all" || u.band === band;
      return matchQ && matchB;
    });
  }, [data, q, band]);

  if (loading) return <Spinner />;
  if (error) return <ErrorBox message={error} />;

  const counts = data.reduce((a, u) => ((a[u.band] = (a[u.band] || 0) + 1), a), {});

  return (
    <>
      <div className="page-head">
        <div>
          <h1>Users & Risk Scoring</h1>
          <p>Per-employee risk score from simulated campaign behaviour, with assigned micro-training.</p>
        </div>
      </div>

      <div className="card" style={{ marginBottom: 16 }}>
        <div className="spread" style={{ gap: 12, flexWrap: "wrap" }}>
          <input style={{ maxWidth: 280 }} placeholder="Search name or department…"
            value={q} onChange={(e) => setQ(e.target.value)} />
          <div className="row" style={{ flex: "0 0 auto" }}>
            {["all", "high", "medium", "low"].map((b) => (
              <button key={b} className={`btn sm ${band === b ? "primary" : "ghost"}`} onClick={() => setBand(b)}>
                {b === "all" ? "All" : <span style={{ textTransform: "capitalize" }}>{b}</span>}
                {b !== "all" && counts[b] ? ` (${counts[b]})` : ""}
              </button>
            ))}
          </div>
        </div>
      </div>

      <div className="card">
        <table className="tbl">
          <thead>
            <tr>
              <th>Employee</th><th>Department</th><th>Role</th>
              <th style={{ width: 200 }}>Risk score</th><th>Band</th><th className="center">Open training</th>
            </tr>
          </thead>
          <tbody>
            {filtered.map((u) => (
              <tr key={u.id} className="clickable" onClick={() => nav(`/users/${u.id}`)}>
                <td>
                  <div>{u.name}</div>
                  <div className="faint mono" style={{ fontSize: 11 }}>{u.email}</div>
                </td>
                <td className="muted">{u.department}</td>
                <td className="muted">{u.role}</td>
                <td>
                  <div className="spread" style={{ gap: 10 }}>
                    <div style={{ flex: 1 }}><Bar value={u.risk_score} color={bandColor(u.band)} /></div>
                    <span className="mono" style={{ width: 34, textAlign: "right", fontWeight: 700 }}>
                      {u.tested ? u.risk_score : "—"}
                    </span>
                  </div>
                </td>
                <td><RiskBadge band={u.band} /></td>
                <td className="center">
                  {u.open_training > 0
                    ? <span className="badge medium">{u.open_training}</span>
                    : <span className="faint">0</span>}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
        {filtered.length === 0 && <div className="empty">No employees match your filters.</div>}
      </div>
    </>
  );
}
