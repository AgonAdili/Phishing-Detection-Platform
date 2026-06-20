from __future__ import annotations

import random
from typing import List, Tuple

BRANDS = ["Microsoft 365", "Office365", "Okta", "DocuSign", "DHL", "FedEx",
          "PayPal", "Amazon", "the IT Helpdesk", "Workday", "Zoom", "Dropbox",
          "the Payroll team", "Apple", "Netflix", "LinkedIn"]

NAMES = ["Alex", "Jordan", "Sam", "Taylor", "Morgan", "Chris", "Pat", "Robin",
         "Jamie", "Casey", "Drew", "Lee"]

FAKE_DOMAINS = ["secure-login-verify.com", "account-update-center.net",
                "0ffice365-support.com", "mail-account-security.com",
                "paysecure-portal.com", "hr-benefits-portal.co",
                "docusign-files.net", "delivery-tracking-update.com"]

# --- phishing building blocks -------------------------------------------------
PHISH_OPENERS = [
    "Dear user,", "Dear valued customer,", "Hello,", "Attention Account Holder,",
    "Dear employee,", "URGENT - Action Required,",
]

PHISH_BODIES = [
    "We detected an unusual sign-in to your {brand} account. Your account will be "
    "suspended within 24 hours unless you verify your identity immediately. "
    "Click here to confirm your password: http://{domain}/verify",

    "Your mailbox is almost full and outgoing messages are being blocked. "
    "Re-validate your credentials now to avoid losing access: https://{domain}/quota",

    "A new invoice (#{num}) is awaiting your approval. Please review and release "
    "payment urgently. Open the secure document: http://{domain}/invoice/{num}",

    "This is {name} from {brand}. I need you to purchase 5 gift cards for a client "
    "right away and send me the codes. I'm in a meeting so I can only reply by email. "
    "Keep this confidential.",

    "Your package could not be delivered due to an unpaid customs fee of $2.99. "
    "Confirm your details to reschedule delivery: http://{domain}/track?id={num}",

    "Security Alert: your password expires today. Failure to update will lock you "
    "out of all company systems. Update now: https://{domain}/password-reset",

    "You have (3) pending encrypted messages held in quarantine. Verify your "
    "account within 12 hours or they will be permanently deleted: http://{domain}/inbox",

    "We are updating our payroll system. Please re-enter your bank account and "
    "login details to continue receiving your salary: https://{domain}/payroll",

    "Congratulations! You have been selected to receive a bonus. Sign in with your "
    "corporate credentials to claim it before it expires: http://{domain}/claim",

    "Action required: your {brand} subscription payment failed. Update your billing "
    "information immediately to avoid service interruption: http://{domain}/billing",
]

PHISH_CLOSERS = [
    "Failure to act will result in permanent account suspension.",
    "This is your final notice.",
    "Do not ignore this message.",
    "Sent from a monitored mailbox, do not reply.",
    "Regards, {brand} Security Team",
]

# --- legitimate building blocks ----------------------------------------------
LEGIT_BODIES = [
    "Hi {name}, thanks for the update on the quarterly report. I've left a few "
    "comments in the shared doc — let's sync on Thursday to finalise the numbers.",

    "Hello team, the sprint planning meeting is moved to 2pm tomorrow in room 4B. "
    "Agenda is attached to the calendar invite. See you there.",

    "Hi, just confirming our lunch on Friday. Does the new place near the office "
    "work for you? Let me know and I'll book a table.",

    "Reminder: the office will be closed next Monday for the public holiday. "
    "Normal hours resume on Tuesday. Have a great long weekend, everyone.",

    "Hi {name}, your expense report for last month has been approved and will be "
    "reimbursed in the next pay cycle. No further action needed.",

    "Thanks for joining today's onboarding session. Slides and the recording are "
    "on the internal wiki under People Ops > New Joiners. Reach out with questions.",

    "Hello, the customer demo went really well. They asked about the reporting "
    "feature — could you put together a short follow-up summary by Wednesday?",

    "Hi all, IT will be performing scheduled maintenance on the VPN this Saturday "
    "between 8-10am. You may notice a brief disconnection. No action is required.",

    "Hi {name}, here are the meeting notes from this morning. I've assigned the "
    "action items in the project board. Let me know if I missed anything.",

    "Good morning, please find the agenda for next week's all-hands below. We'll "
    "cover the roadmap, hiring updates, and Q&A. Submit questions in advance.",

    "Hi, the design review is rescheduled to Friday 11am. I've updated the invite. "
    "If that clashes for anyone, ping me and we'll find another slot.",

    "Welcome aboard! Your laptop and access badge are ready for pickup at the front "
    "desk. HR will walk you through the benefits enrolment during week one.",
]

HARD_CASES = [
    # --- legitimate, but contain "phishy" vocabulary ---
    ("Hi {name}, your monthly account statement is ready. You can view it by "
     "signing in to the portal as usual. Let me know if anything looks off.", 0),
    ("Reminder from IT: please complete the mandatory security training by Friday. "
     "The link is on the intranet homepage and we will never ask for your password "
     "by email.", 0),
    ("Your Amazon order has shipped and will arrive Tuesday. Track it from the "
     "Orders page in your account. Thanks for shopping with us.", 0),
    ("Hi {name}, just a reminder that your password will expire next week. You can "
     "change it yourself from the Settings page in the portal whenever convenient.", 0),
    ("Action required: please submit your timesheet before end of day so payroll "
     "can process this month on time. Thanks for the quick turnaround.", 0),
    ("Hi all, the invoice for the venue has been approved by finance and payment is "
     "scheduled for Friday. No action needed on your side.", 0),
    ("Urgent: the client demo got moved to 3pm today. Please double-check your "
     "slides and join the call link from the calendar invite a few minutes early.", 0),
    ("Hello {name}, your benefits enrolment window closes Friday. Update your "
     "selections in Workday — log in through the usual single sign-on, not a link.", 0),
    ("Hi, the shared document is ready for your review. It's in the team drive under "
     "Q3 Planning. Add your comments directly and we'll discuss on Thursday.", 0),
    ("Security notice: we have enabled multi-factor authentication for all staff. "
     "You'll be prompted to set it up next time you sign in to the company portal.", 0),
    ("Your delivery from the office supplier is scheduled for tomorrow morning. "
     "Reception will sign for it, so there's nothing you need to do.", 0),
    ("Hi {name}, finance flagged a duplicate invoice and is sorting it out with the "
     "vendor. Please hold any related payments until we confirm. Thanks.", 0),

    # --- phishing, but read calm and professional ---
    ("Hi {name}, please review the attached shared document and sign in with your "
     "email password to access it. It's time-sensitive — thanks.", 1),
    ("As part of our annual review, kindly confirm your username and password by "
     "replying to this email so we can keep your records up to date.", 1),
    ("Quick favour — are you at your desk? I need you to handle a confidential "
     "vendor payment before end of day. Reply and I'll send details. - CEO", 1),
    ("Hello {name}, we noticed your mailbox settings are out of date. Please "
     "re-enter your login on the portal page linked here to keep receiving mail.", 1),
    ("Hi, the finance team updated our banking details. Please use the new account "
     "below for this week's supplier payment and confirm once it's done.", 1),
    ("Your recent benefits update could not be saved. Verify your account by "
     "entering your credentials again here so the changes are not lost.", 1),
    ("Hi {name}, I'm travelling and can't reach the portal. Could you log in with "
     "your access and forward me the contract? It's a bit urgent. Thanks, the VP.", 1),
    ("We are migrating to a new single sign-on. To avoid losing access, confirm "
     "your current username and password through the migration form today.", 1),
    ("Hello, your scheduled payment of $480 to a new payee is pending approval. If "
     "you did not set this up, sign in here to cancel it before it is released.", 1),
    ("Hi team, please find the updated vendor invoice attached. Approve and release "
     "payment to the account on the form — the previous account is no longer valid.", 1),
    ("Your account shows an unrecognised device. For your security, re-authenticate "
     "by entering your password on the secure page we've linked for you.", 1),
    ("Hi {name}, HR here — please reconfirm your bank details for this month's "
     "salary run using the short form linked below. It only takes a minute.", 1),
]


def _fill(text: str, rng: random.Random) -> str:
    return text.format(
        brand=rng.choice(BRANDS),
        domain=rng.choice(FAKE_DOMAINS),
        name=rng.choice(NAMES),
        num=rng.randint(1000, 99999),
    )


def build_dataset(n_per_class: int = 280, seed: int = 42) -> Tuple[List[str], List[int]]:
    rng = random.Random(seed)
    texts: List[str] = []
    labels: List[int] = []

    for _ in range(n_per_class):
        opener = rng.choice(PHISH_OPENERS)
        body = _fill(rng.choice(PHISH_BODIES), rng)
        closer = _fill(rng.choice(PHISH_CLOSERS), rng)
        texts.append(f"{opener} {body} {closer}")
        labels.append(1)

    for _ in range(n_per_class):
        body = _fill(rng.choice(LEGIT_BODIES), rng)
        texts.append(body)
        labels.append(0)

    for tmpl, label in HARD_CASES:
        for _ in range(2):
            texts.append(_fill(tmpl, rng))
            labels.append(label)

    combined = list(zip(texts, labels))
    rng.shuffle(combined)
    texts, labels = zip(*combined)
    return list(texts), list(labels)
