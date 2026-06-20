from __future__ import annotations

import json
import random
from datetime import datetime, timedelta

from database import get_db, reset_db
import services
from ml.indicators import detect_indicators

RNG = random.Random(2025)

DEPARTMENTS = {
    "Finance":     (0.55, 9, ["Accountant", "AP Specialist", "Controller"]),
    "Human Resources": (0.52, 7, ["HR Generalist", "Recruiter", "HR Manager"]),
    "Sales":       (0.50, 10, ["Account Executive", "SDR", "Sales Manager"]),
    "Executive":   (0.45, 4, ["CEO", "CFO", "COO", "VP"]),
    "Marketing":   (0.42, 7, ["Content Lead", "Designer", "Marketing Manager"]),
    "Support":     (0.40, 8, ["Support Agent", "Success Manager"]),
    "Engineering": (0.28, 10, ["Software Engineer", "SRE", "Eng Manager"]),
    "IT Security": (0.18, 4, ["Security Analyst", "SysAdmin", "IT Manager"]),
}

FIRST = ["Emma", "Liam", "Olivia", "Noah", "Ava", "Ethan", "Sophia", "Mason",
         "Isabella", "Lucas", "Mia", "Oliver", "Amelia", "Elijah", "Harper",
         "James", "Evelyn", "Benjamin", "Abigail", "Henry", "Ella", "Alexander",
         "Scarlett", "Daniel", "Grace", "Matthew", "Chloe", "Jack", "Lily",
         "Sebastian", "Aria", "David", "Zoe", "Joseph", "Nora", "Samuel",
         "Hannah", "Leo", "Layla", "Adrian", "Ruby", "Marcus", "Ivy", "Felix",
         "Maya", "Oscar", "Stella", "Hugo", "Clara", "Theo", "Nina", "Victor",
         "Elena", "Aaron", "Iris"]
LAST = ["Smith", "Johnson", "Williams", "Brown", "Jones", "Garcia", "Miller",
        "Davis", "Rodriguez", "Martinez", "Hernandez", "Lopez", "Gonzalez",
        "Wilson", "Anderson", "Thomas", "Taylor", "Moore", "Jackson", "Martin",
        "Lee", "Perez", "Thompson", "White", "Harris", "Clark", "Lewis", "Walker",
        "Hall", "Young", "King", "Wright", "Hill", "Scott", "Green", "Adams",
        "Baker", "Nelson", "Carter", "Mitchell", "Roberts", "Turner", "Phillips",
        "Campbell", "Parker", "Evans", "Edwards", "Collins", "Stewart", "Morris",
        "Rogers", "Reed", "Cook", "Bailey", "Cooper"]

TEMPLATES = [
    {
        "name": "Office365 Password Expiry",
        "category": "credential", "difficulty": "easy",
        "sender": "it-helpdesk@0ffice365-support.com",
        "subject": "ACTION REQUIRED: Your password expires today",
        "body": ("Dear user, our records show your Office365 password expires "
                 "today. To avoid being locked out of all company systems, verify "
                 "your identity and update your password immediately: "
                 "http://0ffice365-support.com/password-reset  This is your final "
                 "notice. Sent from a monitored mailbox, do not reply."),
    },
    {
        "name": "DocuSign Shared Contract",
        "category": "credential", "difficulty": "medium",
        "sender": "no-reply@docusign-files.net",
        "subject": "A document was shared with you for signature",
        "body": ("Hello, a confidential contract has been shared with you and is "
                 "awaiting your signature. Please review the secure document and "
                 "sign in with your email password to access it: "
                 "https://docusign-files.net/review  This link expires in 24 hours."),
    },
    {
        "name": "Unpaid Invoice Approval",
        "category": "invoice", "difficulty": "medium",
        "sender": "accounts@account-update-center.net",
        "subject": "Invoice #48817 awaiting your urgent approval",
        "body": ("A new invoice (#48817) is awaiting your approval. Please review "
                 "and release payment urgently to avoid late fees. Open the secure "
                 "document: http://account-update-center.net/invoice/48817"),
    },
    {
        "name": "CEO Gift Card Request",
        "category": "ceo_fraud", "difficulty": "hard",
        "sender": "ceo.office@mail-account-security.com",
        "subject": "Quick favour - are you at your desk?",
        "body": ("Hi, I'm in a meeting and can only reply by email. I need you to "
                 "purchase 5 gift cards for a client right away and send me the "
                 "codes. Keep this confidential and handle it before end of day. "
                 "Thanks. - CEO"),
    },
    {
        "name": "DHL Delivery Customs Fee",
        "category": "delivery", "difficulty": "easy",
        "sender": "tracking@delivery-tracking-update.com",
        "subject": "Your package is on hold - unpaid customs fee",
        "body": ("Your package could not be delivered due to an unpaid customs fee "
                 "of $2.99. Confirm your details to reschedule delivery within 12 "
                 "hours or it will be returned: "
                 "http://delivery-tracking-update.com/track?id=70231"),
    },
    {
        "name": "Payroll Bank Details Update",
        "category": "hr", "difficulty": "hard",
        "sender": "payroll@hr-benefits-portal.co",
        "subject": "Action needed: confirm bank details for salary",
        "body": ("We are updating our payroll system. To continue receiving your "
                 "salary without interruption, please re-enter your bank account "
                 "and login details in the secure portal: "
                 "https://hr-benefits-portal.co/payroll"),
    },
]

MODULES = [
    {"key": "phishing-basics", "title": "Phishing 101: Spot the Fakes",
     "topic": "Awareness", "minutes": 5,
     "description": "How to recognise generic greetings, lookalike senders and the "
                    "classic signs of a phishing email."},
    {"key": "malicious-links", "title": "Hover Before You Click",
     "topic": "Links & URLs", "minutes": 6,
     "description": "Inspecting links, spotting lookalike domains and mismatched "
                    "URLs before clicking anything."},
    {"key": "credential-harvesting", "title": "Protecting Your Login",
     "topic": "Credentials", "minutes": 7,
     "description": "Why no legitimate service asks for your password by email, and "
                    "how credential-harvesting pages work."},
    {"key": "social-engineering", "title": "Urgency & Pressure Tactics",
     "topic": "Social Engineering", "minutes": 6,
     "description": "How attackers use fear, urgency and authority to bypass your "
                    "judgement, and how to slow down."},
    {"key": "payment-fraud", "title": "Invoice & Payment Fraud",
     "topic": "Finance", "minutes": 8,
     "description": "Verifying invoices and payment changes through a second channel "
                    "before releasing any funds."},
    {"key": "bec-ceo-fraud", "title": "Business Email Compromise",
     "topic": "Executive Impersonation", "minutes": 7,
     "description": "Recognising CEO/CFO impersonation and gift-card scams, and the "
                    "verification steps that stop them."},
]


def _make_users(conn) -> None:
    used = set()
    for dept, (mean_s, count, roles) in DEPARTMENTS.items():
        for _ in range(count):
            while True:
                first = RNG.choice(FIRST)
                last = RNG.choice(LAST)
                email = f"{first.lower()}.{last.lower()}@acme-corp.com"
                if email not in used:
                    used.add(email)
                    break
            # susceptibility drawn around the department mean, clamped to [0.05, 0.95]
            s = max(0.05, min(0.95, RNG.gauss(mean_s, 0.14)))
            conn.execute(
                "INSERT INTO users (name, email, department, role, susceptibility, "
                "risk_score, created_at) VALUES (?,?,?,?,?,?,?)",
                (f"{first} {last}", email, dept, RNG.choice(roles), round(s, 3),
                 0, datetime.utcnow().isoformat()),
            )


def _make_templates(conn) -> None:
    for t in TEMPLATES:
        tags = sorted({i["tag"] for i in detect_indicators(f"{t['subject']}\n{t['body']}")})
        conn.execute(
            "INSERT INTO templates (name, category, difficulty, sender, subject, "
            "body, indicators, created_at) VALUES (?,?,?,?,?,?,?,?)",
            (t["name"], t["category"], t["difficulty"], t["sender"], t["subject"],
             t["body"], json.dumps(tags), datetime.utcnow().isoformat()),
        )


def _make_modules(conn) -> None:
    for m in MODULES:
        conn.execute(
            "INSERT INTO training_modules (key, title, topic, description, minutes) "
            "VALUES (?,?,?,?,?)",
            (m["key"], m["title"], m["topic"], m["description"], m["minutes"]),
        )


def _run_past_campaigns(conn) -> None:
    templates = conn.execute("SELECT * FROM templates ORDER BY id").fetchall()
    all_user_ids = [r["id"] for r in conn.execute("SELECT id FROM users").fetchall()]

    plan = [
        (0, "Q1 Baseline Awareness Test", "easy", 5, "all"),
        (2, "Finance Invoice Drill", "medium", 4, "Finance"),
        (4, "Company-wide Delivery Scam", "easy", 3, "all"),
        (1, "DocuSign Credential Test", "medium", 2, "all"),
        (3, "Executive BEC Simulation", "hard", 1, "all"),
    ]
    now = datetime.utcnow()
    for tmpl_idx, name, difficulty, months_ago, target in plan:
        tmpl = templates[tmpl_idx]
        base_time = now - timedelta(days=months_ago * 30)
        if target == "all":
            uids = all_user_ids
        else:
            uids = [r["id"] for r in conn.execute(
                "SELECT id FROM users WHERE department=?", (target,)).fetchall()]
        cur = conn.execute(
            "INSERT INTO campaigns (name, template_id, difficulty, status, "
            "target_count, created_at) VALUES (?,?,?,?,?,?)",
            (name, tmpl["id"], difficulty, "completed", 0, base_time.isoformat()),
        )
        services.simulate_campaign(conn, cur.lastrowid, tmpl, uids, difficulty,
                                   base_time=base_time, rng=RNG)


def _age_training(conn) -> None:
    now = datetime.utcnow()
    for row in conn.execute("SELECT id, assigned_at FROM training_assignments").fetchall():
        assigned = datetime.fromisoformat(row["assigned_at"])
        age_days = (now - assigned).days
        roll = RNG.random()
        if roll < 0.55:
            completed_at = (assigned + timedelta(days=RNG.randint(1, 6))).isoformat()
            conn.execute("UPDATE training_assignments SET status='completed', "
                         "completed_at=? WHERE id=?", (completed_at, row["id"]))
        elif age_days > 21 and roll < 0.75:
            conn.execute("UPDATE training_assignments SET status='overdue' WHERE id=?",
                         (row["id"],))


def run() -> None:
    reset_db()
    with get_db() as conn:
        _make_users(conn)
        _make_templates(conn)
        _make_modules(conn)
        _run_past_campaigns(conn)
        _age_training(conn)
        services.recompute_all_risk(conn)
    print("Seeded database with demo data.")


if __name__ == "__main__":
    run()
