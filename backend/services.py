from __future__ import annotations

import json
import random
import sqlite3
from datetime import datetime, timedelta
from typing import Dict, List, Optional


INDICATOR_TO_MODULE = {
    "urgency": "social-engineering",
    "credentials": "credential-harvesting",
    "suspicious_link": "malicious-links",
    "financial": "payment-fraud",
    "authority": "bec-ceo-fraud",
    "generic_greeting": "phishing-basics",
    "reward": "phishing-basics",
    "no_reply_pressure": "phishing-basics",
}

DIFFICULTY_WEIGHT = {"easy": 1.15, "medium": 1.0, "hard": 0.85}


def _outcome_value(row: sqlite3.Row, difficulty: str) -> float:
    """Per-campaign outcome in roughly [-0.4 .. 1.15].

    Falling for an *easy* (obvious) lure is penalised more than falling for a
    sophisticated one.  Reporting the phish is a strong positive signal.
    """
    diff_w = DIFFICULTY_WEIGHT.get(difficulty, 1.0)
    if row["submitted"]:
        value = 1.0 * diff_w
    elif row["clicked"]:
        value = 0.6 * diff_w
    elif row["opened"]:
        value = 0.15
    else:
        value = 0.0
    if row["reported"]:
        value = min(value, 0.0) - 0.4
    return max(-0.4, value)


def recompute_user_risk(conn: sqlite3.Connection, user_id: int) -> float:
    rows = conn.execute(
        """
        SELECT e.opened, e.clicked, e.submitted, e.reported, c.difficulty, e.timestamp
        FROM events e JOIN campaigns c ON c.id = e.campaign_id
        WHERE e.user_id = ? ORDER BY e.timestamp ASC
        """,
        (user_id,),
    ).fetchall()

    if not rows:
        conn.execute("UPDATE users SET risk_score = 0 WHERE id = ?", (user_id,))
        return 0.0

    weighted_sum = 0.0
    weight_total = 0.0
    for i, row in enumerate(rows, start=1):
        w = float(i)
        weighted_sum += w * _outcome_value(row, row["difficulty"])
        weight_total += w

    mean_outcome = weighted_sum / weight_total
    score = max(0.0, min(100.0, round(mean_outcome * 100, 1)))
    conn.execute("UPDATE users SET risk_score = ? WHERE id = ?", (score, user_id))
    return score


def recompute_all_risk(conn: sqlite3.Connection) -> None:
    for (uid,) in conn.execute("SELECT id FROM users").fetchall():
        recompute_user_risk(conn, uid)


def risk_band(score: float, tested: bool = True) -> str:
    if not tested:
        return "untested"
    if score >= 67:
        return "high"
    if score >= 34:
        return "medium"
    return "low"


def assign_training(conn: sqlite3.Connection, user_id: int, indicators: List[str],
                    reason: str, when: Optional[datetime] = None) -> None:
    when = when or datetime.utcnow()
    seen = set()
    for tag in indicators:
        module_key = INDICATOR_TO_MODULE.get(tag)
        if not module_key or module_key in seen:
            continue
        seen.add(module_key)
        existing = conn.execute(
            "SELECT id FROM training_assignments WHERE user_id=? AND module_key=? "
            "AND status != 'completed'",
            (user_id, module_key),
        ).fetchone()
        if existing:
            continue
        conn.execute(
            "INSERT INTO training_assignments (user_id, module_key, reason, status, "
            "assigned_at) VALUES (?,?,?,?,?)",
            (user_id, module_key, reason, "assigned", when.isoformat()),
        )


def training_recommendations(conn: sqlite3.Connection, user_id: int) -> List[Dict]:
    rows = conn.execute(
        """
        SELECT ta.id, ta.module_key, ta.reason, ta.status, ta.assigned_at,
               ta.completed_at, m.title, m.topic, m.description, m.minutes
        FROM training_assignments ta
        JOIN training_modules m ON m.key = ta.module_key
        WHERE ta.user_id = ? ORDER BY ta.assigned_at DESC
        """,
        (user_id,),
    ).fetchall()
    return [dict(r) for r in rows]


def simulate_campaign(conn: sqlite3.Connection, campaign_id: int, template: sqlite3.Row,
                      user_ids: List[int], difficulty: str,
                      base_time: Optional[datetime] = None,
                      rng: Optional[random.Random] = None) -> Dict:
    rng = rng or random.Random()
    base_time = base_time or datetime.utcnow()
    indicators = json.loads(template["indicators"] or "[]")
    diff_open = {"easy": 0.92, "medium": 0.85, "hard": 0.78}.get(difficulty, 0.85)
    diff_click = {"easy": 1.25, "medium": 1.0, "hard": 0.75}.get(difficulty, 1.0)

    counts = {"sent": 0, "opened": 0, "clicked": 0, "submitted": 0, "reported": 0}

    for uid in user_ids:
        user = conn.execute("SELECT susceptibility FROM users WHERE id=?", (uid,)).fetchone()
        if user is None:
            continue
        s = user["susceptibility"]

        opened = clicked = submitted = reported = 0
        if rng.random() < diff_open:
            opened = 1
            p_click = min(0.97, s * diff_click)
            if rng.random() < p_click:
                clicked = 1
                if rng.random() < (s * 0.6):
                    submitted = 1
            else:
                if rng.random() < (1 - s) * 0.45:
                    reported = 1
        else:
            if rng.random() < (1 - s) * 0.1:
                reported = 1

        ts = base_time + timedelta(minutes=rng.randint(1, 2880))
        conn.execute(
            "INSERT INTO events (campaign_id, user_id, sent, opened, clicked, "
            "submitted, reported, timestamp) VALUES (?,?,?,?,?,?,?,?)",
            (campaign_id, uid, 1, opened, clicked, submitted, reported, ts.isoformat()),
        )
        counts["sent"] += 1
        counts["opened"] += opened
        counts["clicked"] += clicked
        counts["submitted"] += submitted
        counts["reported"] += reported

        if clicked or submitted:
            level = "submitted credentials to" if submitted else "clicked a link in"
            assign_training(
                conn, uid, indicators,
                reason=f"{level} the '{template['name']}' simulation",
                when=ts,
            )

    conn.execute("UPDATE campaigns SET target_count=?, status='completed' WHERE id=?",
                 (counts["sent"], campaign_id))
    return counts


def campaign_stats(conn: sqlite3.Connection, campaign_id: int) -> Dict:
    row = conn.execute(
        """
        SELECT COUNT(*) AS sent,
               COALESCE(SUM(opened),0)    AS opened,
               COALESCE(SUM(clicked),0)   AS clicked,
               COALESCE(SUM(submitted),0) AS submitted,
               COALESCE(SUM(reported),0)  AS reported
        FROM events WHERE campaign_id = ?
        """,
        (campaign_id,),
    ).fetchone()
    sent = row["sent"] or 0

    def rate(n: int) -> float:
        return round(100 * n / sent, 1) if sent else 0.0

    return {
        "sent": sent,
        "opened": row["opened"],
        "clicked": row["clicked"],
        "submitted": row["submitted"],
        "reported": row["reported"],
        "open_rate": rate(row["opened"]),
        "click_rate": rate(row["clicked"]),
        "submit_rate": rate(row["submitted"]),
        "report_rate": rate(row["reported"]),
    }


def list_campaigns_with_stats(conn: sqlite3.Connection) -> List[Dict]:
    rows = conn.execute().fetchall()
    out = []
    for r in rows:
        d = dict(r)
        d["stats"] = campaign_stats(conn, r["id"])
        out.append(d)
    return out


def dashboard_summary(conn: sqlite3.Connection) -> Dict:
    from ml.classifier import get_metrics 

    users = conn.execute("SELECT id, department, risk_score FROM users").fetchall()
    tested_ids = {row[0] for row in conn.execute(
        "SELECT DISTINCT user_id FROM events").fetchall()}

    bands = {"low": 0, "medium": 0, "high": 0, "untested": 0}
    risk_values = []
    dept_acc: Dict[str, Dict] = {}
    for u in users:
        tested = u["id"] in tested_ids
        band = risk_band(u["risk_score"], tested)
        bands[band] += 1
        if tested:
            risk_values.append(u["risk_score"])
        dep = dept_acc.setdefault(u["department"], {"users": 0, "risk_sum": 0.0, "tested": 0})
        dep["users"] += 1
        if tested:
            dep["risk_sum"] += u["risk_score"]
            dep["tested"] += 1

    # overall funnel across all campaigns
    funnel_row = conn.execute(
        """SELECT COUNT(*) sent, COALESCE(SUM(opened),0) opened,
                  COALESCE(SUM(clicked),0) clicked, COALESCE(SUM(submitted),0) submitted,
                  COALESCE(SUM(reported),0) reported FROM events"""
    ).fetchone()
    sent = funnel_row["sent"] or 0
    funnel = {
        "sent": sent,
        "opened": funnel_row["opened"],
        "clicked": funnel_row["clicked"],
        "submitted": funnel_row["submitted"],
        "reported": funnel_row["reported"],
    }

    # repeat clickers: users who clicked in >= 2 distinct campaigns
    repeat = conn.execute(
        """SELECT COUNT(*) FROM (
               SELECT user_id FROM events WHERE clicked = 1
               GROUP BY user_id HAVING COUNT(DISTINCT campaign_id) >= 2)"""
    ).fetchone()[0]

    departments = []
    for name, d in sorted(dept_acc.items()):
        avg_risk = round(d["risk_sum"] / d["tested"], 1) if d["tested"] else 0.0
        departments.append({
            "department": name, "users": d["users"],
            "avg_risk": avg_risk, "band": risk_band(avg_risk, d["tested"] > 0),
        })
    departments.sort(key=lambda x: x["avg_risk"], reverse=True)

    # training compliance
    ta = conn.execute(
        """SELECT
              SUM(CASE WHEN status='completed' THEN 1 ELSE 0 END) completed,
              SUM(CASE WHEN status='overdue'   THEN 1 ELSE 0 END) overdue,
              SUM(CASE WHEN status='assigned'  THEN 1 ELSE 0 END) assigned,
              COUNT(*) total
           FROM training_assignments"""
    ).fetchone()
    total_ta = ta["total"] or 0
    completion_rate = round(100 * (ta["completed"] or 0) / total_ta, 1) if total_ta else 0.0

    return {
        "totals": {
            "users": len(users),
            "campaigns": conn.execute("SELECT COUNT(*) FROM campaigns").fetchone()[0],
            "templates": conn.execute("SELECT COUNT(*) FROM templates").fetchone()[0],
            "emails_simulated": sent,
            "avg_risk_score": round(sum(risk_values) / len(risk_values), 1) if risk_values else 0.0,
            "repeat_clickers": repeat,
        },
        "risk_distribution": bands,
        "funnel": funnel,
        "departments": departments,
        "campaign_trend": [
            {"name": c["name"], "click_rate": c["stats"]["click_rate"],
             "report_rate": c["stats"]["report_rate"], "date": c["created_at"][:10]}
            for c in list_campaigns_with_stats(conn)
        ],
        "training": {
            "total": total_ta,
            "completed": ta["completed"] or 0,
            "assigned": ta["assigned"] or 0,
            "overdue": ta["overdue"] or 0,
            "completion_rate": completion_rate,
        },
        "classifier": get_metrics(),
    }


def compliance_report(conn: sqlite3.Connection) -> Dict:
    tested_ids = {row[0] for row in conn.execute(
        "SELECT DISTINCT user_id FROM events").fetchall()}

    dept: Dict[str, Dict] = {}
    for u in conn.execute("SELECT id, department, risk_score FROM users").fetchall():
        d = dept.setdefault(u["department"], {
            "users": 0, "tested": 0, "risk_sum": 0.0,
            "assigned": 0, "completed": 0, "overdue": 0, "high_risk": 0})
        d["users"] += 1
        if u["id"] in tested_ids:
            d["tested"] += 1
            d["risk_sum"] += u["risk_score"]
            if u["risk_score"] >= 67:
                d["high_risk"] += 1

    for r in conn.execute(
        """SELECT u.department dept, ta.status status
           FROM training_assignments ta JOIN users u ON u.id = ta.user_id"""
    ).fetchall():
        d = dept.setdefault(r["dept"], {
            "users": 0, "tested": 0, "risk_sum": 0.0,
            "assigned": 0, "completed": 0, "overdue": 0, "high_risk": 0})
        if r["status"] == "completed":
            d["completed"] += 1
        elif r["status"] == "overdue":
            d["overdue"] += 1
        else:
            d["assigned"] += 1

    departments = []
    org = {"users": 0, "assigned_total": 0, "completed": 0, "overdue": 0, "high_risk": 0}
    for name, d in sorted(dept.items()):
        assigned_total = d["assigned"] + d["completed"] + d["overdue"]
        comp_rate = round(100 * d["completed"] / assigned_total, 1) if assigned_total else 100.0
        avg_risk = round(d["risk_sum"] / d["tested"], 1) if d["tested"] else 0.0
        departments.append({
            "department": name,
            "users": d["users"],
            "avg_risk": avg_risk,
            "high_risk_users": d["high_risk"],
            "training_assigned": assigned_total,
            "training_completed": d["completed"],
            "training_overdue": d["overdue"],
            "completion_rate": comp_rate,
            "status": "compliant" if comp_rate >= 80 and d["overdue"] == 0 else "at_risk",
        })
        org["users"] += d["users"]
        org["assigned_total"] += assigned_total
        org["completed"] += d["completed"]
        org["overdue"] += d["overdue"]
        org["high_risk"] += d["high_risk"]

    departments.sort(key=lambda x: x["completion_rate"])
    org_completion = round(100 * org["completed"] / org["assigned_total"], 1) if org["assigned_total"] else 100.0

    high_risk_users = [dict(r) for r in conn.execute(
        """SELECT name, email, department, risk_score
           FROM users WHERE id IN (SELECT DISTINCT user_id FROM events)
           AND risk_score >= 67 ORDER BY risk_score DESC LIMIT 25""").fetchall()]

    return {
        "generated_at": datetime.utcnow().isoformat() + "Z",
        "organization": {
            **org,
            "overall_completion_rate": org_completion,
            "overall_status": "compliant" if org_completion >= 80 and org["overdue"] == 0 else "at_risk",
        },
        "departments": departments,
        "high_risk_users": high_risk_users,
    }
