import os, time, requests
from dotenv import load_dotenv
load_dotenv()

OCEAN_API_KEY = os.getenv("OCEAN_API_KEY")
MAX_COMPANIES = int(os.getenv("MAX_COMPANIES", 10))
API_DELAY = float(os.getenv("API_DELAY", 1.0))

def find_lookalike_companies(seed_domain: str) -> list[dict]:
    if not OCEAN_API_KEY or OCEAN_API_KEY == "your_ocean_api_key_here":
        raise ValueError("OCEAN_API_KEY is not set in .env")

    try:
        resp = requests.post(
            f"https://api.ocean.io/v3/search/companies?apiToken={OCEAN_API_KEY}",
            headers={"Content-Type": "application/json"},
            json={"size": MAX_COMPANIES, "companiesFilters": {"lookalikeDomains": [seed_domain]}},
            timeout=30,
        )
        resp.raise_for_status()
        data = resp.json()

        companies = []
        seen = {seed_domain}
        for item in data.get("companies", []):
            c = item.get("company", {})
            domain = c.get("domain", "")
            if not domain or domain in seen:
                continue
            seen.add(domain)
            companies.append({
                "domain": domain,
                "name": c.get("name", domain),
                "industry": ", ".join(c.get("industries", [])[:2]),
                "employee_count": c.get("companySize", ""),
                "location": c.get("primaryCountry", ""),
            })

        time.sleep(API_DELAY)
        return companies[:MAX_COMPANIES]

    except requests.exceptions.HTTPError as e:
        status = e.response.status_code if e.response else "?"
        raise RuntimeError(f"Ocean.io error {status}: {e.response.text[:200]}")
