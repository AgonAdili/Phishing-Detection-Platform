import { useParams, useNavigate } from "react-router-dom";
import { api } from "../api";
import { ErrorBox, RiskBadge, Spinner, bandColor, fmtDate, useFetch } from "../components/ui";

function historyClass(h) {
  if (h.submitted || h.clicked) return "bad";
  if (h.reported) return "good";
  return "";
}
function historyText(h) {
  if (h.submitted) return "Submitted credentials";
  if (h.clicked) return "Clicked the link";
  if (h.reported) return "Reported as phishing";
  if (h.opened) return "Opened the email";
  return "Did not engage";
}

export default function UserDetail() {
  const { id } = useParams();
  const nav = useNavigate();
  const { data, error, loading, reload } = useFetch(() => api.user(id), [id]);

  async function complete(assignmentId) {
    await api.completeTraining(assignmentId);
    reload();
  }

  if (loading) return <Spinner />;
  if (error) return <ErrorBox message={error} />;

  const st = data.stats;

  return (
    <>
      <div className="page-head">
        <div>
          <a className="faint" style={{ cursor: "pointer", fontSize: 13 }} onClick={() => nav("/users")}>← Users & Risk</a>
          <h1 style={{ marginTop: 6 }}>{data.name}</h1>
          <p>{data.role} · {data.department} · <span className="mono">{data.email}</span></p>
        </div>
        <div style={{ textAlign: "right" }}>
          <div style={{ fontSize: 40, fontWeight: 750, lineHeight: 1, color: bandColor(data.band) }}>
            {data.tested ? data.risk_score : "—"}
          </div>
          <div style={{ marginTop: 6 }}><RiskBadge band={data.band} /></div>
        </div>
      </div>

      <div className="grid cols-3" style={{ marginBottom: 16 }}>
        <div className="card kpi"><div className="label">Campaigns</div><div className="value">{st.campaigns}</div></div>
        <div className="card kpi"><div className="label">Times clicked</div><div className="value" style={{ color: "#f5a623" }}>{st.clicked}</div></div>
        <div className="card kpi"><div className="label">Credentials given</div><div className="value" style={{ color: "#ef4d63" }}>{st.submitted}</div></div>
      </div>

      <div className="grid cols-2">
        <div className="card">
          <h3>Campaign history</h3>
          <p className="hint">How this employee responded to each simulation.</p>
          {data.history.length === 0 ? (
            <div className="empty">Not yet included in any campaign.</div>
          ) : (
            <div className="timeline">
              {data.history.map((h, i) => (
                <div key={i} className={`tl-item ${historyClass(h)}`}>
                  <div className="spread">
                    <strong>{h.campaign}</strong>
                    <span className="faint" style={{ fontSize: 12 }}>{fmtDate(h.timestamp)}</span>
                  </div>
                  <div className="muted" style={{ fontSize: 13 }}>
                    {historyText(h)} · <span className="tag">{h.difficulty}</span>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>

        <div className="card">
          <h3>Recommended micro-training</h3>
          <p className="hint">Auto-assigned from the indicators this user fell for.</p>
          {data.training.length === 0 ? (
            <div className="empty">No training needed — no risky behaviour detected. 🎉</div>
          ) : (
            data.training.map((t) => (
              <div key={t.id} className="indicator" style={{ flexDirection: "column", gap: 8 }}>
                <div className="spread">
                  <div>
                    <strong>{t.title}</strong>
                    <div className="faint" style={{ fontSize: 12 }}>{t.topic} · {t.minutes} min</div>
                  </div>
                  <span className={`badge ${t.status === "completed" ? "low" : t.status === "overdue" ? "high" : "medium"}`}>
                    {t.status}
                  </span>
                </div>
                <p className="muted" style={{ fontSize: 12.5, margin: 0 }}>{t.description}</p>
                <p className="faint" style={{ fontSize: 11.5, margin: 0 }}>Reason: {t.reason}</p>
                {t.status !== "completed" && (
                  <button className="btn sm primary" style={{ alignSelf: "flex-start" }} onClick={() => complete(t.id)}>
                    Mark complete
                  </button>
                )}
              </div>
            ))
          )}
        </div>
      </div>
    </>
  );
}
