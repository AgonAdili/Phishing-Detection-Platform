import {
  Bar, BarChart, CartesianGrid, Cell, Legend, Line, LineChart, Pie, PieChart,
  ResponsiveContainer, Tooltip, XAxis, YAxis,
} from "recharts";
import { api } from "../api";
import { ErrorBox, KpiCard, Spinner, useFetch } from "../components/ui";

const AXIS = { stroke: "#5b6678", fontSize: 12 };
const GRID = "#243044";
const tooltipStyle = {
  background: "#121826", border: "1px solid #243044", borderRadius: 10,
  color: "#e6ebf2", fontSize: 12,
};

function Section({ title, hint, children, style }) {
  return (
    <div className="card" style={style}>
      <h3>{title}</h3>
      {hint && <p className="hint">{hint}</p>}
      {children}
    </div>
  );
}

export default function Dashboard() {
  const { data, error, loading } = useFetch(() => api.dashboard());

  if (loading) return <Spinner />;
  if (error) return <ErrorBox message={error} />;

  const t = data.totals;
  const cls = data.classifier;
  const cm = cls.confusion_matrix;

  const funnelData = [
    { stage: "Sent", v: data.funnel.sent, c: "#4f8cff" },
    { stage: "Opened", v: data.funnel.opened, c: "#6f5cff" },
    { stage: "Clicked", v: data.funnel.clicked, c: "#f5a623" },
    { stage: "Submitted", v: data.funnel.submitted, c: "#ef4d63" },
    { stage: "Reported", v: data.funnel.reported, c: "#2fbf71" },
  ];
  const riskData = [
    { name: "Low", value: data.risk_distribution.low, c: "#2fbf71" },
    { name: "Medium", value: data.risk_distribution.medium, c: "#f5a623" },
    { name: "High", value: data.risk_distribution.high, c: "#ef4d63" },
    { name: "Untested", value: data.risk_distribution.untested, c: "#5b6678" },
  ].filter((d) => d.value > 0);

  return (
    <>
      <div className="page-head">
        <div>
          <h1>Security Awareness Dashboard</h1>
          <p>Organisation-wide phishing resilience, campaign performance and ML classifier health.</p>
        </div>
      </div>

      <div className="grid kpis" style={{ marginBottom: 16 }}>
        <KpiCard icon="👥" label="Employees" value={t.users} sub={`${t.repeat_clickers} repeat clickers`} />
        <KpiCard icon="⚠️" label="Avg Risk Score" value={t.avg_risk_score}
          color={t.avg_risk_score >= 67 ? "#ef4d63" : t.avg_risk_score >= 34 ? "#f5a623" : "#2fbf71"}
          sub="0 = safe · 100 = high risk" />
        <KpiCard icon="📨" label="Emails Simulated" value={t.emails_simulated} sub={`${t.campaigns} campaigns`} />
        <KpiCard icon="🎓" label="Training Completion" value={`${data.training.completion_rate}%`}
          color={data.training.completion_rate >= 80 ? "#2fbf71" : "#f5a623"}
          sub={`${data.training.overdue} overdue`} />
        <KpiCard icon="🤖" label="Classifier Accuracy"
          value={cls.accuracy != null ? `${(cls.accuracy * 100).toFixed(1)}%` : "—"}
          color="#4f8cff" sub={cls.backend === "ml" ? "ML model active" : "heuristic fallback"} />
      </div>

      <div className="grid cols-2" style={{ marginBottom: 16 }}>
        <Section title="Phishing Engagement Funnel"
          hint="What recipients did across every simulated campaign.">
          <ResponsiveContainer width="100%" height={260}>
            <BarChart data={funnelData} margin={{ top: 6, right: 10, left: -18, bottom: 0 }}>
              <CartesianGrid strokeDasharray="3 3" stroke={GRID} vertical={false} />
              <XAxis dataKey="stage" tick={AXIS} axisLine={{ stroke: GRID }} tickLine={false} />
              <YAxis tick={AXIS} axisLine={false} tickLine={false} />
              <Tooltip contentStyle={tooltipStyle} cursor={{ fill: "rgba(255,255,255,0.04)" }} />
              <Bar dataKey="v" name="Recipients" radius={[6, 6, 0, 0]} isAnimationActive={false}>
                {funnelData.map((d, i) => <Cell key={i} fill={d.c} />)}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </Section>

        <Section title="Workforce Risk Distribution"
          hint="Employees grouped by current risk band.">
          <ResponsiveContainer width="100%" height={260}>
            <PieChart>
              <Pie data={riskData} dataKey="value" nameKey="name" innerRadius={62} outerRadius={92}
                paddingAngle={3} stroke="none" isAnimationActive={false}>
                {riskData.map((d, i) => <Cell key={i} fill={d.c} />)}
              </Pie>
              <Tooltip contentStyle={tooltipStyle} />
              <Legend iconType="circle" wrapperStyle={{ fontSize: 12, color: "#8b97ab" }} />
            </PieChart>
          </ResponsiveContainer>
        </Section>
      </div>

      <div className="grid cols-2" style={{ marginBottom: 16 }}>
        <Section title="Department Vulnerability"
          hint="Average per-employee risk score by department.">
          <ResponsiveContainer width="100%" height={280}>
            <BarChart data={data.departments} layout="vertical"
              margin={{ top: 4, right: 16, left: 20, bottom: 0 }}>
              <CartesianGrid strokeDasharray="3 3" stroke={GRID} horizontal={false} />
              <XAxis type="number" domain={[0, 100]} tick={AXIS} axisLine={false} tickLine={false} />
              <YAxis type="category" dataKey="department" tick={AXIS} width={108}
                axisLine={false} tickLine={false} />
              <Tooltip contentStyle={tooltipStyle} cursor={{ fill: "rgba(255,255,255,0.04)" }} />
              <Bar dataKey="avg_risk" name="Avg risk" radius={[0, 6, 6, 0]} barSize={16} isAnimationActive={false}>
                {data.departments.map((d, i) => (
                  <Cell key={i} fill={d.avg_risk >= 67 ? "#ef4d63" : d.avg_risk >= 34 ? "#f5a623" : "#2fbf71"} />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </Section>

        <Section title="Campaign Trend Over Time"
          hint="Click-through vs. report rate, oldest → newest campaign.">
          <ResponsiveContainer width="100%" height={280}>
            <LineChart data={data.campaign_trend} margin={{ top: 6, right: 18, left: -18, bottom: 0 }}>
              <CartesianGrid strokeDasharray="3 3" stroke={GRID} vertical={false} />
              <XAxis dataKey="date" tick={AXIS} axisLine={{ stroke: GRID }} tickLine={false} />
              <YAxis tick={AXIS} axisLine={false} tickLine={false} unit="%" />
              <Tooltip contentStyle={tooltipStyle} />
              <Legend iconType="plainline" wrapperStyle={{ fontSize: 12, color: "#8b97ab" }} />
              <Line type="monotone" dataKey="click_rate" name="Click rate" stroke="#ef4d63" strokeWidth={2.5} dot={{ r: 3 }} isAnimationActive={false} />
              <Line type="monotone" dataKey="report_rate" name="Report rate" stroke="#2fbf71" strokeWidth={2.5} dot={{ r: 3 }} isAnimationActive={false} />
            </LineChart>
          </ResponsiveContainer>
        </Section>
      </div>

      <Section title="NLP Phishing Classifier"
        hint={`${cls.model || "model"} · ${cls.samples_total || "?"} labelled emails · ${cls.backend === "ml" ? "trained model" : "heuristic fallback"}`}>
        <div className="grid cols-3" style={{ alignItems: "stretch" }}>
          <div>
            {[["Accuracy", cls.accuracy], ["Precision", cls.precision],
              ["Recall", cls.recall], ["F1 score", cls.f1], ["ROC AUC", cls.roc_auc]].map(([k, v]) => (
              <div key={k} className="spread" style={{ padding: "7px 0", borderBottom: "1px solid var(--border)" }}>
                <span className="muted">{k}</span>
                <span className="mono" style={{ fontWeight: 700 }}>
                  {v != null ? (v * 100).toFixed(2) + "%" : "—"}
                </span>
              </div>
            ))}
          </div>
          {cm ? (
            <div style={{ gridColumn: "span 2" }}>
              <p className="hint">Confusion matrix on held-out test set ({cls.samples_test} emails)</p>
              <div className="cm-grid">
                <div className="cm-cell tn"><div className="n">{cm.true_negative}</div><div className="l">True negative (legit ✓)</div></div>
                <div className="cm-cell fp"><div className="n">{cm.false_positive}</div><div className="l">False positive</div></div>
                <div className="cm-cell fn"><div className="n">{cm.false_negative}</div><div className="l">False negative (missed)</div></div>
                <div className="cm-cell tp"><div className="n">{cm.true_positive}</div><div className="l">True positive (phish ✓)</div></div>
              </div>
            </div>
          ) : (
            <div className="empty" style={{ gridColumn: "span 2" }}>{cls.note}</div>
          )}
        </div>
      </Section>
    </>
  );
}
