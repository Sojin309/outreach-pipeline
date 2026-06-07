#!/usr/bin/env python3
"""
Automated Cold Outreach Pipeline — DEMO MODE
=============================================
Stage 1: Manual domain input (replaces Ocean.io)
Stage 2: Prospeo — finds decision makers + emails
Stage 3: Skipped (Prospeo handles emails now)
Stage 4: Brevo — sends personalized emails
"""

import sys
import time
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.prompt import Confirm

from stages.stage2_prospeo import find_decision_makers
from stages.stage4_brevo import send_outreach_emails
from utils.logger import log_results

console = Console()


def print_banner():
    console.print(Panel.fit(
        "[bold cyan]Automated Outreach Pipeline[/bold cyan]\n"
        "[bold yellow]Prospeo (people + emails) → Brevo (send)[/bold yellow]",
        border_style="cyan"
    ))


def print_stage_header(num, title, emoji):
    console.print(f"\n[bold magenta]{'─'*50}[/bold magenta]")
    console.print(f"[bold]{emoji}  Stage {num}: {title}[/bold]")
    console.print(f"[bold magenta]{'─'*50}[/bold magenta]")


def get_company_domains():
    console.print("\n[bold yellow]Enter company domains (press Enter twice when done)[/bold yellow]")
    console.print("[dim]Example: razorpay.com[/dim]\n")
    domains = []
    while True:
        line = input("  domain → ").strip()
        if not line:
            if domains:
                break
            console.print("[red]Enter at least one domain.[/red]")
        else:
            domain = line.replace("https://","").replace("http://","").replace("www.","").rstrip("/")
            domains.append({"domain": domain, "name": domain})
            console.print(f"  [green]✔ Added: {domain}[/green]")
    return domains


def print_prospects_table(prospects):
    table = Table(title="Decision-Makers Found", show_lines=True)
    table.add_column("Name", style="cyan")
    table.add_column("Title", style="white")
    table.add_column("Email", style="green")
    table.add_column("Company", style="yellow")
    for p in prospects:
        table.add_row(
            p.get("full_name", "—"),
            p.get("job_title", "—"),
            p.get("email") or "—",
            p.get("company_domain", "—"),
        )
    console.print(table)


def main():
    print_banner()
    start_time = time.time()

    # Stage 1 — Manual domains
    print_stage_header(1, "Enter Target Company Domains", "🏢")
    companies = get_company_domains()
    console.print(f"\n[green]✔  {len(companies)} companies queued[/green]")

    # Stage 2 — Prospeo: people + emails
    print_stage_header(2, "Prospeo — Finding Decision-Makers + Emails", "🔍")
    try:
        prospects = find_decision_makers(companies)
        if not prospects:
            console.print("[red]No prospects found. Check your Prospeo API key.[/red]")
            sys.exit(1)
        console.print(f"[green]✔  Found {len(prospects)} prospects[/green]")
        print_prospects_table(prospects)
    except Exception as e:
        console.print(f"[red]Stage 2 failed: {e}[/red]")
        sys.exit(1)

    # Filter only contacts with emails
    contacts = [p for p in prospects if p.get("email")]
    if not contacts:
        console.print("[red]No verified emails found. Cannot send emails.[/red]")
        sys.exit(1)
    console.print(f"[green]✔  {len(contacts)} contacts with verified emails[/green]")

    # Safety checkpoint
    console.print(Panel(
        f"[bold yellow]⚠️  SAFETY CHECKPOINT[/bold yellow]\n\n"
        f"About to send outreach emails to [bold]{len(contacts)}[/bold] contacts.",
        border_style="yellow"
    ))
    if not Confirm.ask("[bold]Send emails now?[/bold]"):
        console.print("[yellow]Cancelled.[/yellow]")
        log_results("demo", companies, prospects, contacts, sent=False)
        sys.exit(0)

    # Stage 4 — Brevo
    print_stage_header(4, "Brevo — Sending Outreach Emails", "📨")
    try:
        results = send_outreach_emails(contacts, companies[0]["domain"])
        sent = [r for r in results if r.get("status") == "sent"]
        failed = [r for r in results if r.get("status") != "sent"]
        console.print(f"[green]✔  Sent: {len(sent)}[/green]  [red]Failed: {len(failed)}[/red]")
    except Exception as e:
        console.print(f"[red]Stage 4 failed: {e}[/red]")
        sys.exit(1)

    log_results("demo", companies, prospects, contacts, sent=True, send_results=results)
    console.print(Panel(
        f"[bold green]✅  Pipeline Complete![/bold green]\n\n"
        f"  Companies  : {len(companies)}\n"
        f"  Prospects  : {len(prospects)}\n"
        f"  Sent       : {len(sent)}\n"
        f"  Time       : {round(time.time()-start_time, 1)}s",
        border_style="green"
    ))


if __name__ == "__main__":
    main()
