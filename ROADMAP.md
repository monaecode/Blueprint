# ROADMAP — Blueprint: from MVP agent to subscription SaaS

The MVP in this repo is the **scanning + reporting engine**. Everything below
turns it into a sellable product for small businesses.

## Phase 1 — Harden the engine (portfolio polish)
- [ ] LangGraph observability: per-node timing/retries in the graph path
- [ ] Nuclei template allow-list curation (review which "safe" templates are
      actually safe against fragile small-business sites)
- [ ] Report quality pass: client logo, branded styling, trend section
      ("3 fewer High findings than last month")
- [ ] Re-scan / diff mode: compare against the previous report, highlight
      new vs. remediated findings
- [ ] False-positive learning: per-client suppression rules with analyst review

## Phase 2 — Web app (the sellable product)
- [ ] Next.js dashboard (Vercel): signup, scan history, report downloads
- [ ] FastAPI backend: job queue (Celery/RQ), scan workers in sandboxed Docker
- [ ] Auth (Auth.js/Clerk), Postgres for clients/scans/findings
- [ ] **Domain-ownership verification**: client proves control via DNS TXT
      record (like Google Search Console) *before* any scan is scheduled —
      this replaces the manual scope file for self-serve signup
- [ ] In-app authorization flow: click-to-sign engagement terms, stored per scan
- [ ] Scheduled scans: monthly/quarterly cron per subscription tier

## Phase 3 — Billing & packaging
- [ ] Stripe subscriptions:
      **$99/mo** — monthly automated scan + PDF report
      **$249/mo** — quarterly deep scan + 30-min remediation call
- [ ] Founding-customer pricing ($49/mo for first 10) to get testimonials
- [ ] One-page sales site: sample (redacted) report as the hero asset

## Phase 4 — Trust & compliance (what closes deals)
- [ ] Report encryption at rest, per-client data retention policy
- [ ] Terms of service + scope-of-testing agreement reviewed by a lawyer
- [ ] Status page + scan SLAs
- [ ] SOC 2 readiness for the SaaS itself (dogfooding opportunity)

## Phase 5 — Growth loops
- [ ] "Fix verified" re-scans as an upsell after remediation
- [ ] Partner channel: MSPs/IT consultants white-label the reports
- [ ] Content: publish anonymized "state of small-business security" stats
      from aggregate (opt-in) scan data

## Deliberately out of scope
- Active exploitation / payload execution (liability + illegality risk)
- Bug-bounty style continuous testing without per-engagement authorization
- Scanning anything the client hasn't proven they own
