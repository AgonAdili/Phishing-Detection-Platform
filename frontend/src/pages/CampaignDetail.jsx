import { useParams, useNavigate } from "react-router-dom";
import { api } from "../api";
import { ErrorBox, Spinner, fmtDate, useFetch } from "../components/ui";

function outcome(t) {
  if (t.submitted) return { label: "Submitted credentials", cls: "high" };
  if (t.clicked) return { label: "Clicked link", cls: "medium" };
  if (t.reported) return { label: "Reported phishing", cls: "low" };
  if (t.opened) return { label: "Opened only", cls: "untested" };
  return { label: "No action", cls: "untested" };
}

export default function CampaignDetail() {
  const { id } = useParams();
  const nav = useNavigate();
  const { data, error, loading } = useFetch(() => api.campaign(id), [id]);

  if (loading) return <Spinner />;
  if (error) return <ErrorBox message={error} />;

  const s = data.stats;
  const stages = [
    { k: "Sent", v: s.sent, r: 100, c: "#4f8cff" },
    { k: "Opened", v: s.opened, r: s.open_rate, c: "#6f5cff" },
    { k: "Clicked", v: s.clicked, r: s.click_rate, c: "#f5a623" },
    { k: "Submitted", v: s.submitted, r: s.submit_rate, c: "#ef4d63" },
    { k: "Reported", v: s.reported, r: s.report_rate, c: "#2fbf71" },
  ];

  return (
    <>
      <div className="page-head">
        <div>
          <a className="faint" style={{ cursor: "pointer", fontSize: 13 }} onClick={() => nav("/campaigns")}>← Campaigns</a>
          <h1 style={{ marginTop: 6 }}>{data.name}</h1>
          <p>{data.template_name} · <span className="tag">{data.difficulty}</span> · {fmtDate(data.created_at)}</p>
        </div>
      </div>

      <div className="grid cols-3" style={{ marginBottom: 16 }}>
        {stages.map((st) => (
          <div key={st.k} className="card kpi">
            <div className="label">{st.k}</div>
            <div className="value" style={{ color: st.c }}>{st.v}</div>
            <div className="delta">{st.r}% of recipients</div>
          </div>
        ))}
      </div>

      <div className="grid cols-2">
        <div className="card">
          <h3>The lure</h3>
          <p className="hint">Exactly what recipients received in this simulation.</p>
          <div className="email-preview">
            <div className="meta">From: {data.template_sender} · Subject: {data.template_subject}</div>
            {data.template_body}
            <div className="matches" style={{ marginTop: 12 }}>
              {(data.indicators || []).map((i) => <span key={i} className="chip">{i}</span>)}
            </div>
          </div>
        </div>

        <div className="card">
          <h3>Recipient outcomes</h3>
          <p className="hint">Sorted by severity — credential submitters first.</p>
          <div style={{ maxHeight: 420, overflow: "auto" }}>
            <table className="tbl">
              <thead>
                <tr><th>Employee</th><th>Department</th><th>Outcome</th></tr>
              </thead>
              <tbody>
                {data.targets.map((t, i) => {
                  const o = outcome(t);
                  return (
                    <tr key={i}>
                      <td>
                        <div>{t.name}</div>
                        <div className="faint mono" style={{ fontSize: 11 }}>{t.email}</div>
                      </td>
                      <td className="muted">{t.department}</td>
                      <td><span className={`badge ${o.cls}`}>{o.label}</span></td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </>
  );
}
