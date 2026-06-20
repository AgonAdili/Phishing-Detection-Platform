import { useMemo, useState } from "react";
import { useNavigate } from "react-router-dom";
import { api } from "../api";
import { Bar, ErrorBox, Spinner, fmtDate, useFetch } from "../components/ui";

function StatPill({ label, value, rate, color }) {
  return (
    <div style={{ flex: 1, minWidth: 88 }}>
      <div className="faint" style={{ fontSize: 11, textTransform: "uppercase", letterSpacing: "0.04em" }}>{label}</div>
      <div style={{ fontWeight: 700, fontSize: 18, color }}>{value}</div>
      <div className="faint" style={{ fontSize: 11 }}>{rate}%</div>
    </div>
  );
}

function Builder({ templates, departments, onClose, onCreated }) {
  const [form, setForm] = useState({
    name: "", template_id: templates[0]?.id || "", difficulty: "",
    target_type: "all", department: departments[0] || "", sample_size: 20,
  });
  const [busy, setBusy] = useState(false);
  const [err, setErr] = useState(null);
  const tmpl = templates.find((t) => t.id === Number(form.template_id));

  const set = (k) => (e) => setForm({ ...form, [k]: e.target.value });

  async function submit() {
    setBusy(true);
    setErr(null);
    try {
      const payload = {
        name: form.name || `${tmpl?.name} simulation`,
        template_id: Number(form.template_id),
        difficulty: form.difficulty || null,
        target_type: form.target_type,
        department: form.target_type === "department" ? form.department : null,
        sample_size: form.target_type === "random" ? Number(form.sample_size) : null,
      };
      const res = await api.createCampaign(payload);
      onCreated(res);
    } catch (e) {
      setErr(e.message);
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="modal-backdrop" onClick={onClose}>
      <div className="modal" onClick={(e) => e.stopPropagation()}>
        <h2>New simulated campaign</h2>
        <p className="hint">Generates tracked responses across your chosen audience. No real emails are sent.</p>

        <label className="field">
          <span>Campaign name</span>
          <input value={form.name} onChange={set("name")} placeholder={tmpl ? `${tmpl.name} simulation` : "Campaign name"} />
        </label>

        <label className="field">
          <span>Phishing template</span>
          <select value={form.template_id} onChange={set("template_id")}>
            {templates.map((t) => (
              <option key={t.id} value={t.id}>{t.name} · {t.category} · {t.difficulty}</option>
            ))}
          </select>
        </label>

        {tmpl && (
          <div className="email-preview" style={{ marginBottom: 14 }}>
            <div className="meta">From: {tmpl.sender} · Subject: {tmpl.subject}</div>
            {tmpl.body}
            <div className="matches" style={{ marginTop: 10 }}>
              {tmpl.indicators.map((i) => <span key={i} className="chip">{i}</span>)}
            </div>
          </div>
        )}

        <div className="row">
          <label className="field">
            <span>Difficulty (override)</span>
            <select value={form.difficulty} onChange={set("difficulty")}>
              <option value="">Use template default ({tmpl?.difficulty})</option>
              <option value="easy">Easy (obvious)</option>
              <option value="medium">Medium</option>
              <option value="hard">Hard (sophisticated)</option>
            </select>
          </label>
          <label className="field">
            <span>Audience</span>
            <select value={form.target_type} onChange={set("target_type")}>
              <option value="all">Whole organisation</option>
              <option value="department">Single department</option>
              <option value="random">Random sample</option>
            </select>
          </label>
        </div>

        {form.target_type === "department" && (
          <label className="field">
            <span>Department</span>
            <select value={form.department} onChange={set("department")}>
              {departments.map((d) => <option key={d} value={d}>{d}</option>)}
            </select>
          </label>
        )}
        {form.target_type === "random" && (
          <label className="field">
            <span>Sample size</span>
            <input type="number" min={1} value={form.sample_size} onChange={set("sample_size")} />
          </label>
        )}

        {err && <p className="hint" style={{ color: "var(--red)" }}>{err}</p>}
        <div className="modal-foot">
          <button className="btn ghost" onClick={onClose}>Cancel</button>
          <button className="btn primary" onClick={submit} disabled={busy}>
            {busy ? "Launching…" : "🚀 Launch simulation"}
          </button>
        </div>
      </div>
    </div>
  );
}

export default function Campaigns() {
  const nav = useNavigate();
  const campaignsQ = useFetch(() => api.campaigns());
  const templatesQ = useFetch(() => api.templates());
  const usersQ = useFetch(() => api.users());
  const [showBuilder, setShowBuilder] = useState(false);
  const [flash, setFlash] = useState(null);

  const departments = useMemo(
    () => [...new Set((usersQ.data || []).map((u) => u.department))].sort(),
    [usersQ.data]
  );

  if (campaignsQ.loading || templatesQ.loading) return <Spinner />;
  if (campaignsQ.error) return <ErrorBox message={campaignsQ.error} />;

  const campaigns = [...campaignsQ.data].reverse();

  return (
    <>
      <div className="page-head">
        <div>
          <h1>Phishing Campaigns</h1>
          <p>Build and launch simulated spear-phishing campaigns, then track engagement.</p>
        </div>
        <button className="btn primary" onClick={() => setShowBuilder(true)}>+ New campaign</button>
      </div>

      {flash && (
        <div className="card" style={{ marginBottom: 16, borderColor: "var(--brand)" }}>
          <strong>Campaign launched.</strong>{" "}
          <span className="muted">
            {flash.results.sent} sent · {flash.results.clicked} clicked · {flash.results.submitted} submitted
            credentials · {flash.results.reported} reported.
          </span>{" "}
          <a className="mono" style={{ color: "var(--brand)" }} onClick={() => nav(`/campaigns/${flash.campaign_id}`)}>
            View results →
          </a>
        </div>
      )}

      <div className="stack">
        {campaigns.map((c) => {
          const s = c.stats;
          return (
            <div key={c.id} className="card" style={{ cursor: "pointer" }} onClick={() => nav(`/campaigns/${c.id}`)}>
              <div className="spread" style={{ marginBottom: 14 }}>
                <div>
                  <div style={{ fontWeight: 650, fontSize: 15 }}>{c.name}</div>
                  <div className="faint" style={{ fontSize: 12, marginTop: 3 }}>
                    {c.template_name} · <span className="tag">{c.difficulty}</span> · {fmtDate(c.created_at)}
                  </div>
                </div>
                <span className={`badge ${c.status === "completed" ? "low" : "medium"}`}>{c.status}</span>
              </div>
              <div style={{ display: "flex", gap: 16, marginBottom: 12 }}>
                <StatPill label="Sent" value={s.sent} rate={100} />
                <StatPill label="Opened" value={s.opened} rate={s.open_rate} color="#6f5cff" />
                <StatPill label="Clicked" value={s.clicked} rate={s.click_rate} color="#f5a623" />
                <StatPill label="Submitted" value={s.submitted} rate={s.submit_rate} color="#ef4d63" />
                <StatPill label="Reported" value={s.reported} rate={s.report_rate} color="#2fbf71" />
              </div>
              <div className="spread" style={{ gap: 12 }}>
                <span className="faint" style={{ fontSize: 11, width: 90 }}>Click-through</span>
                <div style={{ flex: 1 }}><Bar value={s.click_rate} color="#f5a623" /></div>
                <span className="mono" style={{ fontSize: 12, width: 44, textAlign: "right" }}>{s.click_rate}%</span>
              </div>
            </div>
          );
        })}
      </div>

      {showBuilder && templatesQ.data && (
        <Builder
          templates={templatesQ.data}
          departments={departments}
          onClose={() => setShowBuilder(false)}
          onCreated={(res) => {
            setShowBuilder(false);
            setFlash(res);
            campaignsQ.reload();
          }}
        />
      )}
    </>
  );
}
