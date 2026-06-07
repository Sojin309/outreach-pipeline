"""
Logger — saves full pipeline run results to JSON.
"""

import json
import os
from datetime import datetime


def log_results(
    seed_domain: str,
    companies: list,
    prospects: list,
    contacts: list,
    sent: bool,
    send_results: list = None,
):
    output = {
        "run_at": datetime.now().isoformat(),
        "seed_domain": seed_domain,
        "summary": {
            "companies_found": len(companies),
            "prospects_found": len(prospects),
            "emails_resolved": len(contacts),
            "emails_sent": len([r for r in (send_results or []) if r.get("status") == "sent"]),
            "emails_failed": len([r for r in (send_results or []) if r.get("status") != "sent"]),
            "emails_fired": sent,
        },
        "companies": companies,
        "prospects": prospects,
        "contacts": contacts,
        "send_results": send_results or [],
    }

    path = "outreach_results.json"
    with open(path, "w") as f:
        json.dump(output, f, indent=2)

    print(f"\n  Results saved → {os.path.abspath(path)}")
