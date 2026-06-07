"""
Stage 4 — Brevo
=================
Input  : list of contacts with verified emails + seed domain
Output : send personalized outreach emails via Brevo SMTP API

Brevo API docs: https://developers.brevo.com
"""

import os
import time
import requests
from dotenv import load_dotenv

load_dotenv()

BREVO_API_KEY = os.getenv("BREVO_API_KEY")
SENDER_NAME = os.getenv("SENDER_NAME", "Your Name")
SENDER_EMAIL = os.getenv("SENDER_EMAIL", "you@yourdomain.com")
API_DELAY = float(os.getenv("API_DELAY", 1.0))

BASE_URL = "https://api.brevo.com/v3"


def _headers():
    return {
        "api-key": BREVO_API_KEY,
        "Content-Type": "application/json",
    }


def _build_subject(contact: dict, seed_domain: str) -> str:
    """Personalized subject line."""
    first = contact.get("first_name") or contact.get("full_name", "").split()[0] or "there"
    company = contact.get("company_name") or contact.get("company_domain", "")
    return f"Quick question for {company} — {first}"


def _build_email_body(contact: dict, seed_domain: str) -> str:
    """
    Personalized cold outreach email.
    Sharp, short, human — not a generic blast.
    """
    first = contact.get("first_name") or contact.get("full_name", "").split()[0] or "there"
    title = contact.get("job_title", "your role")
    company = contact.get("company_name") or contact.get("company_domain", "their company")
    seed_company = seed_domain.split(".")[0].capitalize()

    html = f"""
<html>
<body style="font-family: Arial, sans-serif; font-size: 15px; color: #222; max-width: 600px; margin: 0 auto; line-height: 1.6;">

<p>Hi {first},</p>

<p>
  I came across {company} while looking at companies similar to {seed_company} — 
  same space, similar scale, and the same kind of growth trajectory.
</p>

<p>
  As {title}, you're probably thinking about how to get more qualified pipeline without 
  burning your team on manual research and outreach. That's exactly what we help with.
</p>

<p>
  We've helped teams like yours go from a static prospect list to a fully automated 
  sourcing-to-outreach engine — the kind that runs while your team focuses on closing.
</p>

<p><strong>Would it make sense to talk for 15 minutes?</strong></p>

<p>
  If yes, just reply and I'll send a calendar link. If the timing's off, no worries — 
  happy to reconnect whenever it makes sense.
</p>

<p>
  Either way, good luck with everything at {company}.<br><br>
  — {SENDER_NAME}
</p>

<p style="font-size: 12px; color: #999; margin-top: 30px;">
  You're receiving this because {company} was identified as a strong match 
  for the type of companies we work with. Reply "unsubscribe" to opt out.
</p>

</body>
</html>
"""
    return html.strip()


def _build_plain_text(contact: dict, seed_domain: str) -> str:
    """Plain text fallback."""
    first = contact.get("first_name") or contact.get("full_name", "").split()[0] or "there"
    title = contact.get("job_title", "your role")
    company = contact.get("company_name") or contact.get("company_domain", "")
    seed_company = seed_domain.split(".")[0].capitalize()

    return (
        f"Hi {first},\n\n"
        f"I came across {company} while looking at companies similar to {seed_company}. "
        f"Same space, similar scale.\n\n"
        f"As {title}, you're likely thinking about how to get more pipeline without burning your team. "
        f"That's exactly what we help with.\n\n"
        f"Would it make sense to talk for 15 minutes?\n\n"
        f"Just reply and I'll send a link.\n\n"
        f"— {SENDER_NAME}\n\n"
        f"---\n"
        f"Reply 'unsubscribe' to opt out."
    )


def _send_single(contact: dict, seed_domain: str) -> dict:
    """Send one email via Brevo. Returns a result dict."""
    email = contact.get("email")
    name = contact.get("full_name", "")

    payload = {
        "sender": {"name": SENDER_NAME, "email": SENDER_EMAIL},
        "to": [{"email": email, "name": name}],
        "subject": _build_subject(contact, seed_domain),
        "htmlContent": _build_email_body(contact, seed_domain),
        "textContent": _build_plain_text(contact, seed_domain),
    }

    try:
        resp = requests.post(
            f"{BASE_URL}/smtp/email",
            headers=_headers(),
            json=payload,
            timeout=30,
        )
        resp.raise_for_status()
        data = resp.json()

        return {
            "email": email,
            "name": name,
            "status": "sent",
            "message_id": data.get("messageId", ""),
        }

    except requests.exceptions.HTTPError as e:
        status_code = e.response.status_code if e.response else "?"
        if status_code == 401:
            raise ValueError("Brevo: Invalid API key (401 Unauthorized)")
        elif status_code == 429:
            print(f"  [rate-limit] Brevo: waiting 10s before retry...")
            time.sleep(10)
            return _send_single(contact, seed_domain)  # one retry
        else:
            error_msg = e.response.text[:200] if e.response else str(e)
            print(f"  [fail] {email}: {status_code} — {error_msg}")
            return {"email": email, "name": name, "status": "failed", "error": error_msg}

    except Exception as e:
        print(f"  [fail] {email}: {e}")
        return {"email": email, "name": name, "status": "failed", "error": str(e)}


def send_outreach_emails(contacts: list[dict], seed_domain: str) -> list[dict]:
    """
    Send personalized outreach emails to all contacts.
    Returns a list of send-result dicts.
    """
    if not BREVO_API_KEY or BREVO_API_KEY == "your_brevo_api_key_here":
        raise ValueError("BREVO_API_KEY is not set in .env")

    if not SENDER_EMAIL or SENDER_EMAIL == "you@yourdomain.com":
        raise ValueError("SENDER_EMAIL is not set in .env — add your verified sender address")

    results = []

    for contact in contacts:
        email = contact.get("email", "")
        print(f"  Sending to {contact.get('full_name')} <{email}>...")

        result = _send_single(contact, seed_domain)
        results.append(result)

        if result["status"] == "sent":
            print(f"  [ok] Sent → {email}")
        else:
            print(f"  [fail] {email}: {result.get('error', 'unknown error')}")

        time.sleep(API_DELAY)

    return results
