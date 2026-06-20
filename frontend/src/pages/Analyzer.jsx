import { useState } from "react";
import { api } from "../api";
import { bandColor } from "../components/ui";

const SAMPLES = {
  "Phishing — credential": {
    subject: "ACTION REQUIRED: Your password expires today",
    body:
      "Dear user, our records show your Office365 password expires today. To avoid " +
      "being locked out of all company systems, verify your identity and update your " +
      "password immediately: http://0ffice365-support.com/password-reset  This is your " +
      "final notice. Sent from a monitored mailbox, do not reply.",
  },
  "Phishing — CEO fraud": {
    subject: "Quick favour - are you at your desk?",
    body:
      "Hi, I'm in a meeting and can only reply by email. I need you to purchase 5 gift " +
      "cards for a client right away and send me the codes. Keep this confidential and " +
      "handle it before end of day. Thanks. - CEO",
  },
  "Legitimate — internal": {
    subject: "Sprint planning moved to 2pm",
    body:
      "Hello team, the sprint planning meeting is moved to 2pm tomorrow in room 4B. The " +
      "agenda is attached to the calendar invite. See you there, and ping me if that " +
      "time clashes for anyone.",
  },
};

export default function Analyzer() {
  const [subject, setSubject] = useState(SAMPLES["Phishing — credential"].subject);
  const [body, setBody] = useState(SAMPLES["Phishing — credential"].body);
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [err, setErr] = useState(null);

  async function run() {
    setLoading(true);
    setErr(null);
    try {
      setResult(await api.analyze(subject, body));
    } catch (e) {
      setErr(e.message);
    } finally {
      setLoading(false);
    }
  }

  function loadSample(name) {
    setSubject(SAMPLES[name].subject);
    setBody(SAMPLES[name].body);
    setResult(null);
  }

  const pct = result ? Math.round(result.phishing_probability * 100) : 0;
  const gColor = result ? bandColor(result.risk_band) : "#4f8cff";

  return (
    <>
      <div className="page-head">
        <div>
          <h1>Email Analyzer</h1>
          <p>Paste any email and the NLP classifier scores its phishing probability and explains why.</p>
        </div>
      </div>

      <div className="grid cols-2">
        <div className="card">
          <h3>Email under analysis</h3>
          <p className="hint">Try a sample or paste your own.</p>
          <div className="row" style={{ marginBottom: 14 }}>
            {Object.keys(SAMPLES).map((s) => (
              <button key={s} className="btn sm ghost" onClick={() => loadSample(s)}>{s}</button>
            ))}
          </div>
          <label className="field">
            <span>Subject</span>
            <input value={subject} onChange={(e) => setSubject(e.target.value)} placeholder="Email subject" />
          </label>
          <label className="field">
            <span>Body</span>
            <textarea rows={9} value={body} onChange={(e) => setBody(e.target.value)} placeholder="Paste the email body here…" />
          </label>
          <button className="btn primary" onClick={run} disabled={loading || !body.trim()}>
            {loading ? "Analyzing…" : "🔬 Analyze email"}
          </button>
          {err && <p className="hint" style={{ color: "var(--red)", marginTop: 10 }}>{err}</p>}
        </div>

        <div className="card">
          <h3>Classifier verdict</h3>
          {!result ? (
            <div className="empty">Run an analysis to see the phishing score and detected red flags.</div>
          ) : (
            <>
              <div className="gauge-wrap" style={{ marginBottom: 18 }}>
                <div className="gauge" style={{ "--p": pct, "--gcolor": gColor }}>
                  <div>
                    <div className="gval" style={{ color: gColor }}>{pct}%</div>
                    <div className="glabel">phishing</div>
                  </div>
                </div>
                <div>
                  <span className={`badge dot ${result.risk_band}`} style={{ fontSize: 13 }}>
                    {result.verdict === "phishing" ? "Likely phishing" : "Likely legitimate"}
                  </span>
                  <p className="muted" style={{ margin: "10px 0 4px" }}>
                    Risk band: <strong style={{ color: gColor, textTransform: "capitalize" }}>{result.risk_band}</strong>
                  </p>
                  <p className="faint" style={{ fontSize: 12 }}>
                    Scored by {result.backend === "ml" ? "trained ML model" : "heuristic engine"} ·
                    {" "}{result.indicator_count} red flag{result.indicator_count === 1 ? "" : "s"} found
                  </p>
                </div>
              </div>

              <div className="divider" />
              <h3 style={{ marginBottom: 10 }}>Why — detected indicators</h3>
              {result.indicators.length === 0 ? (
                <p className="muted">No classic phishing indicators detected in the text.</p>
              ) : (
                result.indicators.map((ind) => (
                  <div key={ind.tag} className="indicator">
                    <div className="iw">+{Math.round(ind.weight * 100)}</div>
                    <div style={{ flex: 1 }}>
                      <strong>{ind.label}</strong>
                      <div className="matches">
                        {ind.matches.map((m, i) => <span key={i} className="chip">{m}</span>)}
                      </div>
                    </div>
                  </div>
                ))
              )}
            </>
          )}
        </div>
      </div>
    </>
  );
}
