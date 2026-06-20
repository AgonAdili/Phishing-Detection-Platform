from __future__ import annotations

import re
from typing import Dict, List

# tag -> (weight, label, regexes)
RULES = [
    {
        "tag": "urgency",
        "weight": 0.18,
        "label": "Urgency / fear pressure",
        "patterns": [
            r"\b(urgent|immediately|right away|within \d+ hours?|expires? today|"
            r"final notice|act now|as soon as possible|asap|time[- ]sensitive)\b",
            r"\b(suspend|suspended|locked? out|deactivat\w+|terminat\w+|"
            r"permanently deleted)\b",
        ],
    },
    {
        "tag": "credentials",
        "weight": 0.26,
        "label": "Requests credentials / login",
        "patterns": [
            r"\b(verify your (identity|account|password)|confirm your (password|"
            r"credentials|username)|re-?enter your (password|login|credentials)|"
            r"sign in with your (corporate|email|company) (credentials|password)|"
            r"update your password|password reset)\b",
            r"\b(username and password|login details|account and login)\b",
        ],
    },
    {
        "tag": "suspicious_link",
        "weight": 0.22,
        "label": "Suspicious / mismatched link",
        "patterns": [
            r"https?://[^\s]*"
            r"(verify|secure-login|account-update|password-reset|0ffice|"
            r"-support\.|-portal\.|-security\.|tracking-update)",
            r"https?://(\d{1,3}\.){3}\d{1,3}", 
            r"http://[^\s]+",                     
        ],
    },
    {
        "tag": "financial",
        "weight": 0.2,
        "label": "Payment / financial lure",
        "patterns": [
            r"\b(invoice|wire transfer|gift cards?|bank account|billing "
            r"information|payment (failed|details)|customs fee|unpaid|reimburse "
            r"urgently|release payment)\b",
            r"\$\d",
        ],
    },
    {
        "tag": "authority",
        "weight": 0.16,
        "label": "Authority / CEO-fraud pretext",
        "patterns": [
            r"\b(ceo|cfo|director|i'?m in a meeting|keep this confidential|"
            r"quick favou?r|are you at your desk|i need you to|do this for me)\b",
        ],
    },
    {
        "tag": "generic_greeting",
        "weight": 0.1,
        "label": "Generic / impersonal greeting",
        "patterns": [
            r"^\s*(dear (user|customer|valued customer|account holder|employee)|"
            r"attention account holder|dear sir/madam)\b",
        ],
    },
    {
        "tag": "reward",
        "weight": 0.12,
        "label": "Too-good-to-be-true reward",
        "patterns": [
            r"\b(congratulations|you have been selected|claim your (bonus|reward|"
            r"prize)|you('| ha)ve won)\b",
        ],
    },
    {
        "tag": "no_reply_pressure",
        "weight": 0.08,
        "label": "Do-not-reply / monitored mailbox",
        "patterns": [
            r"\b(do not (reply|ignore)|monitored mailbox|this is your final)\b",
        ],
    },
]


def detect_indicators(text: str) -> List[Dict]:
    low = text.lower()
    found: List[Dict] = []
    for rule in RULES:
        matches: List[str] = []
        for pat in rule["patterns"]:
            for m in re.finditer(pat, low, flags=re.IGNORECASE | re.MULTILINE):
                snippet = m.group(0).strip()
                if snippet and snippet not in matches:
                    matches.append(snippet[:80])
        if matches:
            found.append({
                "tag": rule["tag"],
                "label": rule["label"],
                "weight": rule["weight"],
                "matches": matches[:4],
            })
    return found


def heuristic_score(text: str) -> float:
    indicators = detect_indicators(text)
    score = sum(ind["weight"] for ind in indicators)
    # diminishing returns -> squash into 0..1
    return round(min(1.0, score), 4)
