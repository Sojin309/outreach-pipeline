"""
Stage 3 — Eazyreach
=====================
Input  : list of prospect dicts with linkedin_url
Output : same list enriched with verified work email

Eazyreach API docs: https://eazyreach.app
"""

import os
import time
import requests
from dotenv import load_dotenv

load_dotenv()

EAZYREACH_API_KEY = os.getenv("EAZYREACH_API_KEY")
API_DELAY = float(os.getenv("API_DELAY", 1.0))

BASE_URL = "https://api.eazyreach.app/v1"


def _headers():
    return {
        "Authorization": f"Bearer {EAZYREACH_API_KEY}",
        "Content-Type": "application/json",
    }


def _resolve_single(linkedin_url: str) -> str | None:
    """
    Resolve a LinkedIn URL to a verified work email via Eazyreach.
    Returns the email string or None if not found.
    """
    try:
        payload = {"linkedin_url": linkedin_url}

        resp = requests.post(
            f"{BASE_URL}/find-email",
            headers=_headers(),
            json=payload,
            timeout=30,
        )
        resp.raise_for_status()
        data = resp.json()

        # Try common response keys
        email = (
            data.get("email")
            or data.get("work_email")
            or data.get("data", {}).get("email")
            or None
        )

        # Only return verified emails
        status = (
            data.get("verification_status")
            or data.get("status")
            or data.get("data", {}).get("status")
            or "unknown"
        ).lower()

        if email and status in ("valid", "verified", "deliverable", "unknown"):
            return email

        return None

    except requests.exceptions.HTTPError as e:
        status_code = e.response.status_code if e.response else "?"
        if status_code == 401:
            raise ValueError("Eazyreach: Invalid API key (401 Unauthorized)")
        elif status_code == 402:
            raise RuntimeError("Eazyreach: Out of credits. Contact the team for a top-up.")
        elif status_code == 429:
            print(f"  [rate-limit] Eazyreach: waiting 5s...")
            time.sleep(5)
            return _resolve_single(linkedin_url)  # one retry
        else:
            print(f"  [warn] Eazyreach error {status_code} for {linkedin_url[:60]}: {e.response.text[:100]}")
            return None

    except requests.exceptions.RequestException as e:
        print(f"  [warn] Network error: {e}")
        return None


def resolve_emails(prospects: list[dict]) -> list[dict]:
    """
    Enrich each prospect with a verified work email.
    Drops prospects where no email could be resolved.
    """
    if not EAZYREACH_API_KEY or EAZYREACH_API_KEY == "your_eazyreach_api_key_here":
        raise ValueError("EAZYREACH_API_KEY is not set in .env")

    contacts = []

    for prospect in prospects:
        linkedin_url = prospect.get("linkedin_url", "")

        if not linkedin_url:
            print(f"  [skip] {prospect.get('full_name')} — no LinkedIn URL")
            continue

        print(f"  Resolving {prospect.get('full_name')} ({linkedin_url[:50]}...)...")
        email = _resolve_single(linkedin_url)

        if email:
            contact = {**prospect, "email": email}
            contacts.append(contact)
            print(f"  [ok] {prospect.get('full_name')} → {email}")
        else:
            print(f"  [skip] {prospect.get('full_name')} — email not found")

        time.sleep(API_DELAY)

    return contacts
