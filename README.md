# 🚀 Automated Cold Outreach Pipeline

One input. Four stages. A complete outreach engine — zero humans in the loop.

```
company.domain → Ocean.io → Prospeo → Eazyreach → Brevo → 📧 sent
```

---

## Setup

### 1. Clone & install dependencies

```bash
cd outreach_pipeline
pip install -r requirements.txt
```

### 2. Configure API keys

```bash
cp .env.example .env
```

Open `.env` and fill in all four API keys + your sender email:

```env
OCEAN_API_KEY=...
PROSPEO_API_KEY=...
EAZYREACH_API_KEY=...
BREVO_API_KEY=...

SENDER_NAME=Your Name
SENDER_EMAIL=you@yourdomain.com
```

### 3. API Key Locations

| Service    | Where to get your key |
|------------|----------------------|
| Ocean.io   | https://ocean.io → Settings → API |
| Prospeo    | https://app.prospeo.io/api → API Key |
| Eazyreach  | https://eazyreach.app → Settings → API |
| Brevo      | https://app.brevo.com → Settings → API Keys |

> ⚠️ **Brevo**: You must verify your sender email in Brevo before it can send.

---

## Running the Pipeline

```bash
# Pass domain as argument
python main.py stripe.com

# Or run interactively
python main.py
# → Enter seed domain: stripe.com
```

### What happens

1. **Ocean.io** finds up to 10 companies similar to your seed domain
2. **Prospeo** finds C-suite / VP decision-makers at each company
3. **Eazyreach** resolves each LinkedIn profile to a verified work email
4. **Safety checkpoint** — shows you a summary before any email fires
5. **Brevo** sends a personalized outreach email to each contact

---

## Output

- Console: live progress + summary tables
- `outreach_results.json`: full data for every stage saved locally

---

## Configuration (`.env`)

| Variable | Default | Description |
|----------|---------|-------------|
| `MAX_COMPANIES` | 10 | Max lookalikes from Ocean.io |
| `MAX_PROSPECTS_PER_COMPANY` | 3 | Max decision-makers per company |
| `API_DELAY` | 1.0 | Seconds between API calls (rate limit buffer) |

---

## Project Structure

```
outreach_pipeline/
├── main.py                  # Entry point — orchestrates all stages
├── requirements.txt
├── .env.example             # Copy → .env and fill keys
├── stages/
│   ├── stage1_ocean.py      # Ocean.io: find lookalike companies
│   ├── stage2_prospeo.py    # Prospeo: find decision-makers
│   ├── stage3_eazyreach.py  # Eazyreach: resolve work emails
│   └── stage4_brevo.py      # Brevo: send personalized emails
└── utils/
    └── logger.py            # Saves results to JSON
```

---

## Edge Cases Handled

- **Missing LinkedIn URLs** → prospect is skipped (not crashed)
- **Rate limits** → automatic retry with backoff on all APIs  
- **Unresolvable emails** → contact dropped before send stage
- **Partial failures** → pipeline continues; failed sends logged
- **Duplicate contacts** → de-duplicated by LinkedIn URL
- **Safety checkpoint** → explicit confirm before any email fires

---
