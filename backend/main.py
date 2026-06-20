from __future__ import annotations

import json
import random
from datetime import datetime
from typing import List, Optional

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

import services
from database import get_db, init_db
from ml import classifier
from ml.indicators import detect_indicators

app = FastAPI(title="Phishing Detection & Awareness Training API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


class AnalyzeRequest(BaseModel):
    subject: str = ""
    body: str = Field(..., min_length=1)


class TemplateCreate(BaseModel):
    name: str
    category: str = "credential"
    difficulty: str = "medium"
    sender: str
    subject: str
    body: str


class CampaignCreate(BaseModel):
    name: str
    template_id: int
    difficulty: Optional[str] = None
    target_type: str = "all"          
    department: Optional[str] = None
    sample_size: Optional[int] = None


@app.on_event("startup")
def _startup() -> None:
    init_db()
    with get_db() as conn:
        count = conn.execute("SELECT COUNT(*) FROM users").fetchone()[0]
    if count == 0:
        import seed
        seed.run()


@app.get("/api/health")
def health() -> dict:
    return {"status": "ok", "classifier_ready": classifier.is_ready(),
            "time": datetime.utcnow().isoformat() + "Z"}


@app.get("/api/classifier/metrics")
def classifier_metrics() -> dict:
    return classifier.get_metrics()


@app.post("/api/classifier/analyze")
def classifier_analyze(req: AnalyzeRequest) -> dict:
    return classifier.analyze(req.subject, req.body)


@app.get("/api/templates")
def list_templates() -> List[dict]:
    with get_db() as conn:
        rows = conn.execute("SELECT * FROM templates ORDER BY id").fetchall()
        out = []
        for r in rows:
            d = dict(r)
            d["indicators"] = json.loads(d["indicators"] or "[]")
            out.append(d)
        return out


@app.post("/api/templates")
def create_template(t: TemplateCreate) -> dict:
    tags = sorted({ind["tag"] for ind in detect_indicators(f"{t.subject}\n{t.body}")})
    with get_db() as conn:
        cur = conn.execute(
            "INSERT INTO templates (name, category, difficulty, sender, subject, "
            "body, indicators, created_at) VALUES (?,?,?,?,?,?,?,?)",
            (t.name, t.category, t.difficulty, t.sender, t.subject, t.body,
             json.dumps(tags), datetime.utcnow().isoformat()),
        )
        tid = cur.lastrowid
        row = conn.execute("SELECT * FROM templates WHERE id=?", (tid,)).fetchone()
        d = dict(row)
        d["indicators"] = json.loads(d["indicators"])
        return d


@app.get("/api/campaigns")
def list_campaigns() -> List[dict]:
    with get_db() as conn:
        return services.list_campaigns_with_stats(conn)


@app.get("/api/campaigns/{campaign_id}")
def campaign_detail(campaign_id: int) -> dict:
    with get_db() as conn:
        c = conn.execute(
            """SELECT c.*, t.name template_name, t.subject template_subject,
                      t.body template_body, t.sender template_sender, t.indicators
               FROM campaigns c JOIN templates t ON t.id = c.template_id
               WHERE c.id = ?""", (campaign_id,)).fetchone()
        if c is None:
            raise HTTPException(404, "Campaign not found")
        detail = dict(c)
        detail["indicators"] = json.loads(detail.get("indicators") or "[]")
        detail["stats"] = services.campaign_stats(conn, campaign_id)
        rows = conn.execute(
            """SELECT u.name, u.email, u.department, e.opened, e.clicked,
                      e.submitted, e.reported, e.timestamp
               FROM events e JOIN users u ON u.id = e.user_id
               WHERE e.campaign_id = ? ORDER BY e.submitted DESC, e.clicked DESC""",
            (campaign_id,)).fetchall()
        detail["targets"] = [dict(r) for r in rows]
        return detail


@app.post("/api/campaigns")
def create_campaign(c: CampaignCreate) -> dict:
    with get_db() as conn:
        tmpl = conn.execute("SELECT * FROM templates WHERE id=?", (c.template_id,)).fetchone()
        if tmpl is None:
            raise HTTPException(404, "Template not found")
        difficulty = c.difficulty or tmpl["difficulty"]

        if c.target_type == "department" and c.department:
            users = conn.execute("SELECT id FROM users WHERE department=?",
                                 (c.department,)).fetchall()
        else:
            users = conn.execute("SELECT id FROM users").fetchall()
        user_ids = [u["id"] for u in users]
        if c.target_type == "random" and c.sample_size:
            rng = random.Random()
            rng.shuffle(user_ids)
            user_ids = user_ids[: c.sample_size]
        if not user_ids:
            raise HTTPException(400, "No users match the selected target")

        cur = conn.execute(
            "INSERT INTO campaigns (name, template_id, difficulty, status, "
            "target_count, created_at) VALUES (?,?,?,?,?,?)",
            (c.name, c.template_id, difficulty, "running", 0,
             datetime.utcnow().isoformat()),
        )
        cid = cur.lastrowid
        counts = services.simulate_campaign(conn, cid, tmpl, user_ids, difficulty)
        for uid in user_ids:
            services.recompute_user_risk(conn, uid)

        return {"campaign_id": cid, "results": counts,
                "stats": services.campaign_stats(conn, cid)}


@app.get("/api/users")
def list_users() -> List[dict]:
    with get_db() as conn:
        tested_ids = {row[0] for row in conn.execute(
            "SELECT DISTINCT user_id FROM events").fetchall()}
        rows = conn.execute(
            "SELECT id, name, email, department, role, risk_score FROM users "
            "ORDER BY risk_score DESC").fetchall()
        out = []
        for r in rows:
            d = dict(r)
            tested = r["id"] in tested_ids
            d["band"] = services.risk_band(r["risk_score"], tested)
            d["tested"] = tested
            d["open_training"] = conn.execute(
                "SELECT COUNT(*) FROM training_assignments WHERE user_id=? "
                "AND status!='completed'", (r["id"],)).fetchone()[0]
            out.append(d)
        return out


@app.get("/api/users/{user_id}")
def user_detail(user_id: int) -> dict:
    with get_db() as conn:
        u = conn.execute("SELECT * FROM users WHERE id=?", (user_id,)).fetchone()
        if u is None:
            raise HTTPException(404, "User not found")
        d = {k: u[k] for k in u.keys() if k != "susceptibility"}
        history = conn.execute(
            """SELECT c.name campaign, c.difficulty, e.opened, e.clicked,
                      e.submitted, e.reported, e.timestamp
               FROM events e JOIN campaigns c ON c.id = e.campaign_id
               WHERE e.user_id = ? ORDER BY e.timestamp DESC""", (user_id,)).fetchall()
        d["history"] = [dict(r) for r in history]
        d["tested"] = len(d["history"]) > 0
        d["band"] = services.risk_band(u["risk_score"], d["tested"])
        d["training"] = services.training_recommendations(conn, user_id)
        d["stats"] = {
            "campaigns": len(d["history"]),
            "clicked": sum(1 for h in d["history"] if h["clicked"]),
            "submitted": sum(1 for h in d["history"] if h["submitted"]),
            "reported": sum(1 for h in d["history"] if h["reported"]),
        }
        return d


@app.get("/api/training/modules")
def training_modules() -> List[dict]:
    with get_db() as conn:
        return [dict(r) for r in conn.execute(
            "SELECT * FROM training_modules ORDER BY id").fetchall()]


@app.post("/api/training/{assignment_id}/complete")
def complete_training(assignment_id: int) -> dict:
    with get_db() as conn:
        row = conn.execute("SELECT user_id FROM training_assignments WHERE id=?",
                           (assignment_id,)).fetchone()
        if row is None:
            raise HTTPException(404, "Assignment not found")
        conn.execute(
            "UPDATE training_assignments SET status='completed', completed_at=? WHERE id=?",
            (datetime.utcnow().isoformat(), assignment_id))
        return {"status": "completed", "assignment_id": assignment_id}


@app.get("/api/dashboard/summary")
def dashboard() -> dict:
    with get_db() as conn:
        return services.dashboard_summary(conn)


@app.get("/api/compliance/report")
def compliance() -> dict:
    with get_db() as conn:
        return services.compliance_report(conn)


@app.post("/api/seed")
def reseed() -> dict:
    import seed
    seed.run()
    return {"status": "reseeded"}
