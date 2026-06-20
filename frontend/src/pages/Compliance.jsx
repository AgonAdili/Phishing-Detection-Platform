import { api } from "../api";
import { Bar, ErrorBox, RiskBadge, Spinner, useFetch } from "../components/ui";

function downloadCSV(report) {
  const rows = [
    ["Department", "Users", "Avg Risk", "High-risk Users", "Training Assigned",
      "Training Completed", "Overdue", "Completion %", "Status"],
    ...report.departments.map((d) => [
      d.department, d.users, d.avg_risk, d.high_risk_users, d.training_assigned,
      d.training_completed, d.training_overdue, d.completion_rate, d.status,
    ]),
  ];
  const csv = rows.map((r) => r.join(",")).join("\n");
  const blob = new Blob([csv], { type: "text/csv" });
  const a = document.createElement("a");
  a.href = URL.createObjectURL(blob);
  a.download = `compliance-report-${report.generated_at.slice(0, 10)}.csv`;
  a.click();
  URL.revokeObjectURL(a.href);
}

export default function Compliance() {
  const { data, error, loading } = useFetch(() => api.compliance());
  if (loading) return <Spinner />;
  if (error) return <ErrorBox message={error} />;

  const org = data.organization;
  const compliant = org.overall_status === "compliant";

  return (
    <>
      <div className="page-head">
        <div>
          <h1>Compliance Reporting</h1>
          <p>Training completion and residual risk by department — exportable for audit.</p>
        </div>
        <button className="btn primary" onClick={() => downloadCSV(data)}>⤓ Export CSV</button>
      </div>

      <div className="card" style={{ marginBottom: 16, borderColor: compliant ? "var(--green)" : "var(--red)" }}>
        <div className="spread" style={{ flexWrap: "wrap", gap: 16 }}>
          <div>
            <div className="faint" style={{ fontSize: 12, textTransform: "uppercase", letterSpacing: "0.05em" }}>
              Organisation status
            </div>
            <div style={{ fontSize: 24, fontWeight: 750, marginTop: 4 }}>
              <span className={`badge ${compliant ? "compliant" : "at_risk"}`} style={{ fontSize: 15 }}>
                {compliant ? "Compliant" : "At risk"}
              </span>
            </div>
          </div>
          <div className="row" style={{ flex: 1, minWidth: 300, justifyContent: "flex-end" }}>
            <Metric label="Employees" value={org.users} />
            <Metric label="Completion" value={`${org.overall_completion_rate}%`}
              color={org.overall_completion_rate >= 80 ? "#2fbf71" : "#f5a623"} />
            <Metric label="Overdue" value={org.overdue} color={org.overdue ? "#ef4d63" : "#2fbf71"} />
            <Metric label="High-risk users" value={org.high_risk} color={org.high_risk ? "#ef4d63" : "#2fbf71"} />
          </div>
        </div>
      </div>

      <div className="card" style={{ marginBottom: 16 }}>
        <h3>Department compliance</h3>
        <p className="hint">Sorted by completion rate — least compliant first.</p>
        <table className="tbl">
          <thead>
            <tr>
              <th>Department</th><th className="center">Users</th><th>Avg risk</th>
              <th style={{ width: 180 }}>Training completion</th>
              <th className="center">Overdue</th><th className="center">High-risk</th><th>Status</th>
            </tr>
          </thead>
          <tbody>
            {data.departments.map((d) => (
              <tr key={d.department}>
                <td><strong>{d.department}</strong></td>
                <td className="center muted">{d.users}</td>
                <td><span className="mono">{d.avg_risk}</span></td>
                <td>
                  <div className="spread" style={{ gap: 10 }}>
                    <div style={{ flex: 1 }}>
                      <Bar value={d.completion_rate} color={d.completion_rate >= 80 ? "#2fbf71" : "#f5a623"} />
                    </div>
                    <span className="mono" style={{ width: 40, textAlign: "right" }}>{d.completion_rate}%</span>
                  </div>
                  <div className="faint" style={{ fontSize: 11, marginTop: 3 }}>
                    {d.training_completed}/{d.training_assigned} modules
                  </div>
                </td>
                <td className="center">{d.training_overdue ? <span className="badge high">{d.training_overdue}</span> : <span className="faint">0</span>}</td>
                <td className="center">{d.high_risk_users ? <span className="badge high">{d.high_risk_users}</span> : <span className="faint">0</span>}</td>
                <td><span className={`badge ${d.status}`}>{d.status === "compliant" ? "Compliant" : "At risk"}</span></td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      <div className="card">
        <h3>High-risk employees requiring attention</h3>
        <p className="hint">Risk score ≥ 67 — prioritise for follow-up coaching.</p>
        {data.high_risk_users.length === 0 ? (
          <div className="empty">No employees currently in the high-risk band. 🎉</div>
        ) : (
          <table className="tbl">
            <thead>
              <tr><th>Employee</th><th>Department</th><th>Risk score</th><th>Band</th></tr>
            </thead>
            <tbody>
              {data.high_risk_users.map((u, i) => (
                <tr key={i}>
                  <td>
                    <div>{u.name}</div>
                    <div className="faint mono" style={{ fontSize: 11 }}>{u.email}</div>
                  </td>
                  <td className="muted">{u.department}</td>
                  <td className="mono" style={{ fontWeight: 700, color: "#ef4d63" }}>{u.risk_score}</td>
                  <td><RiskBadge band="high" /></td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </>
  );
}

function Metric({ label, value, color }) {
  return (
    <div style={{ textAlign: "right", flex: "0 0 auto", minWidth: 90 }}>
      <div className="faint" style={{ fontSize: 11, textTransform: "uppercase", letterSpacing: "0.04em" }}>{label}</div>
      <div style={{ fontSize: 26, fontWeight: 750, color: color || "var(--text)" }}>{value}</div>
    </div>
  );
}
