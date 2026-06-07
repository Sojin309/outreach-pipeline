import os, time, requests
from dotenv import load_dotenv
load_dotenv()

PROSPEO_API_KEY = os.getenv("PROSPEO_API_KEY")
MAX_PROSPECTS = int(os.getenv("MAX_PROSPECTS_PER_COMPANY", 3))
API_DELAY = float(os.getenv("API_DELAY", 1.0))
BASE_URL = "https://api.prospeo.io"

def _headers():
    return {"X-KEY": PROSPEO_API_KEY, "Content-Type": "application/json"}

def _extract_email(email_obj):
    if isinstance(email_obj, dict):
        return email_obj.get("email", "") or ""
    return str(email_obj) if email_obj else ""

def _extract_location(loc_obj):
    if isinstance(loc_obj, dict):
        city = loc_obj.get("city", "")
        country = loc_obj.get("country", "")
        return f"{city}, {country}".strip(", ")
    return str(loc_obj) if loc_obj else ""

def _search_domain(domain):
    try:
        payload = {
            "filters": {
                "company": {"websites": {"include": [domain]}},
                "person_seniority": {"include": ["C-Suite", "Vice President", "Director", "Founder/Owner", "Partner"]},
                "person_contact_details": {"email": ["VERIFIED"]}
            },
            "page": 1
        }
        resp = requests.post(f"{BASE_URL}/search-person", headers=_headers(), json=payload, timeout=30)
        resp.raise_for_status()
        data = resp.json()
        if data.get("error"):
            print(f"  [warn] Prospeo: {data.get('error_message', 'unknown error')}")
            return []
        people = []
        for r in data.get("results", []):
            person = r.get("person", {})
            company = r.get("company", {})
            people.append({
                "full_name": person.get("full_name", ""),
                "first_name": person.get("first_name", ""),
                "last_name": person.get("last_name", ""),
                "job_title": person.get("current_job_title", ""),
                "linkedin_url": person.get("linkedin_url", ""),
                "email": _extract_email(person.get("email")),
                "location": _extract_location(person.get("location")),
                "company_name": company.get("name", domain),
                "company_domain": domain,
            })
        return people
    except requests.exceptions.HTTPError as e:
        status = e.response.status_code if e.response else "?"
        print(f"  [warn] Prospeo error {status} for {domain}: {e.response.text[:150]}")
        return []
    except Exception as e:
        print(f"  [warn] Network error for {domain}: {e}")
        return []

def find_decision_makers(companies):
    if not PROSPEO_API_KEY or PROSPEO_API_KEY == "your_prospeo_api_key_here":
        raise ValueError("PROSPEO_API_KEY is not set in .env")
    prospects = []
    seen = set()
    for company in companies:
        domain = company["domain"]
        print(f"  Searching {domain}...")
        people = _search_domain(domain)
        count = 0
        for person in people:
            if count >= MAX_PROSPECTS:
                break
            key = person.get("linkedin_url") or person.get("full_name", "")
            if key in seen:
                continue
            seen.add(key)
            prospects.append(person)
            count += 1
        time.sleep(API_DELAY)
    return prospects
