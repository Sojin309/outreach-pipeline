#!/usr/bin/env python3
"""
Automated Cold Outreach Pipeline
=================================
One input → Ocean.io → Prospeo → Brevo
"""

import sys
import time
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.prompt import Confirm

from stages.stage1_ocean import find_lookalike_companies
from stages.stage2_prospeo import find_decision_makers
from stages.stage4_brevo import send_outreach_emails
from utils.logger import log_results

console = Console()


def print_banner():
    console.print(Panel.fit(
        "[bold cyan]🚀 Automated Cold Outreach Pipeline[/bold cyan]\n"
        "[dim]Ocean.io → Prospeo → Brevo[/dim]",
        border_style="cyan"
    ))


def get_seed_domain():
    if len(sys.argv) > 1:
        domain = sys.argv[1].strip()
    else:
        console.print("\n[bold yellow]Enter seed domain[/bold yellow] [dim](e.g. stripe.com)[/dim]")
        domain = input("  → ").strip()
    return domain.replace("https://","").replace("http://","").replace("www.","").rstrip("/")


def print_stage_header(num, title, emoji):
    console.print(f"\n[bold magenta]{'─'*50}[/bold magenta]")
    console.print(f"[bold]{emoji}  Stage {num}: {title}[/bold]")
    console.print(f"[bold magenta]{'─'*50}[/bold magenta]")


def print_companies_summary(companies):
    table = Table(title="Lookalike Companies Found", show_lines=True)
    table.add_column("Domain", style="cyan")
    table.add_column("Company Name", style="white")
    for c in companies[:10]:
        table.add_row(c.get("domain", "—"), c.get("name", "—"))
    console.print(table)
    if len(companies) > 10:
        console.print(f"[dim]...and {len(companies)-10} more[/dim]")


def print_prospects_summary(prospects):
    table = Table(title="Decision-Makers Found", show_lines=True)
    table.add_column("Name", style="cyan")
    table.add_column("Title", style="white")
    table.add_column("Email", style="green")
    table.add_column("Company", style="yellow")
    for p in prospects[:10]:
        table.add_row(
            p.get("full_name", "—"),
            p.get("job_title", "—"),
            p.get("email") or "—",
            p.get("company_domain", "—"),
        )
    console.print(table)
    if len(prospects) > 10:
        console.print(f"[dim]...and {len(prospects)-10} more[/dim]")


def safety_checkpoint(contacts):
    console.print(Panel(
        f"[bold yellow]⚠️  SAFETY CHECKPOINT[/bold yellow]\n\n"
        f"You're about to send outreach emails to [bold]{len(contacts)}[/bold] contacts.\n"
        f"Please review the list above before proceeding.",
        border_style="yellow"
    ))
    return Confirm.ask("[bold]Send emails now?[/bold]")


def main():
    print_banner()
    seed_domain = get_seed_domain()
    if not seed_domain:
        console.print("[red]No domain provided. Exiting.[/red]")
        sys.exit(1)

    console.print(f"\n[bold green]✔  Seed domain:[/bold green] {seed_domain}")
    start_time = time.time()

    # Stage 1: Ocean.io
    print_stage_header(1, "Ocean.io — Finding Lookalike Companies", "🌊")
    try:
        companies = find_lookalike_companies(seed_domain)
        if not companies:
            console.print("[red]No lookalike companies found.[/red]")
            sys.exit(1)
        console.print(f"[green]✔  Found {len(companies)} companies[/green]")
        print_companies_summary(companies)
    except Exception as e:
        console.print(f"[red]Stage 1 failed: {e}[/red]")
        sys.exit(1)

    # Stage 2: Prospeo — people + emails
    print_stage_header(2, "Prospeo — Finding Decision-Makers + Emails", "🔍")
    try:
        prospects = find_decision_makers(companies)
        if not prospects:
            console.print("[red]No prospects found.[/red]")
            sys.exit(1)
        console.print(f"[green]✔  Found {len(prospects)} prospects[/green]")
        print_prospects_summary(prospects)
    except Exception as e:
        console.print(f"[red]Stage 2 failed: {e}[/red]")
        sys.exit(1)

    # Filter contacts with emails
    contacts = [p for p in prospects if p.get("email")]
    if not contacts:
        console.print("[red]No verified emails found.[/red]")
        sys.exit(1)
    console.print(f"[green]✔  {len(contacts)} contacts with verified emails[/green]")

    # Safety checkpoint
    if not safety_checkpoint(contacts):
        console.print("\n[yellow]Emails not sent. Pipeline halted.[/yellow]")
        log_results(seed_domain, companies, prospects, contacts, sent=False)
        sys.exit(0)

    # Stage 4: Brevo
    print_stage_header(4, "Brevo — Sending Outreach Emails", "📨")
    try:
        results = send_outreach_emails(contacts, seed_domain)
        sent = [r for r in results if r.get("status") == "sent"]
        failed = [r for r in results if r.get("status") != "sent"]
        console.print(f"[green]✔  Sent: {len(sent)}[/green]  [red]Failed: {len(failed)}[/red]")
    except Exception as e:
        console.print(f"[red]Stage 4 failed: {e}[/red]")
        sys.exit(1)

    elapsed = round(time.time() - start_time, 1)
    log_results(seed_domain, companies, prospects, contacts, sent=True, send_results=results)

    console.print(Panel(
        f"[bold green]✅  Pipeline Complete![/bold green]\n\n"
        f"  Seed domain   : {seed_domain}\n"
        f"  Companies     : {len(companies)}\n"
        f"  Prospects     : {len(prospects)}\n"
        f"  Emails sent   : {len(sent)}\n"
        f"  Time elapsed  : {elapsed}s\n\n"
        f"[dim]Results saved to outreach_results.json[/dim]",
        border_style="green"
    ))


if __name__ == "__main__":
    main()
