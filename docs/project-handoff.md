# Scruffy — Project Handoff (July 2026)

This document records where the project stands, the competitive landscape, why building paused, and how to pick it back up — including notes on a potential YC path.

**Status (updated 2026-07-07):** Build frozen; **60-day demand-validation gate in progress.** After an external review (gstack, see below), the decision changed from "shelve" to "stop building, run paid shadow pilots in Phoenix." Code is on `main`, pushed to GitHub. The prototype works end-to-end on fake portals.

**Decision gate:** By ~2026-09-05, either 2 of the keep-going criteria below are met (→ resume build against a paying design partner's stack) or 15+ conversations produced zero portal credentials and zero budget discussion (→ shelve for real).

---

## What Scruffy Is

Scruffy automates the **supplier-side "Human API"**: log into buyer-owned portals (Coupa-style), extract purchase orders, normalize messy buyer terminology to canonical SKUs, and inject into the supplier's ERP.

```
Extract (Playwright agent) → Normalize (LLM + Pydantic) → Inject (ERP API)
```

**Core design:** LLM as non-deterministic router inside a deterministic shell (observe → act → validate → repeat).

---

## Where We Left Off

### Completed (as of commit `209204a`)

| Area | State |
|------|--------|
| **Phase 1** | Playwright harness, `RawPurchaseOrder` models, practice site scraper |
| **Phase 1.5** | `PageObservation`, compact DOM snapshots for agents |
| **Phase 1.75** | Ollama client (Mac → Linux box, `qwen2.5:14b`) |
| **Phase 2** | ReAct agent loop, action executor, step timing, loop guards |
| **Portals** | v1 (clean headers), v2 (messy UOM/headers), v3 (pagination) |
| **Eval infra** | `eval/cases.json`, `EvalRunner`, scored JSON reports |
| **Tests** | 35 passing (browser, portal, ollama, eval unit tests) |

### Smoke eval baseline (2026-07-06)

Run: `python scripts/run_eval.py --tag smoke`  
Model: `qwen2.5:14b` @ `http://192.168.0.7:11434`

| Case | Result | Steps | Total time |
|------|--------|-------|------------|
| v1_po_1042 | PASS | 5 | ~132s |
| v2_po_1042 | PASS | 5 | ~73s |
| v3_po_1042 | PASS | 6 | ~97s |

**3/3 passed** — agent success 100%, extraction accuracy 100%.  
Report path (local, gitignored): `eval-results/20260706T174021Z/report.json`

### Not started

- Phase 3: `CanonicalPurchaseOrder`, SKU catalog, normalization with confidence scores
- Phase 4+: MCP tool servers, LangGraph, ERP injection (NetSuite / SAP B1)
- Portal v4/v5 (CSV-export-only, detail-page-only)
- Real customer shadow mode (Phoenix suppliers — discussed, not implemented in repo)
- Production concerns: credential vault, SOC2, multi-tenant, audit logs

### Key commands to resume

```bash
pip install -e ".[dev,portal]"
playwright install chromium

python portals/v3/server.py                    # port 8002
python scripts/run_agent.py --url http://127.0.0.1:8002 --po PO-1042 --headed
python scripts/run_eval.py --tag smoke
pytest -v
```

---

## External Review Verdict (gstack, 2026-07-07)

We asked for an outside diagnostic on continue-vs-shelve. Full transcript lives outside this repo; the operative conclusions:

**Verdict: don't shelve yet — stop building.** SKU normalization and ERP injection are frozen until a paid pilot exists. The riskiest assumption is not "the market is crowded"; it is *"Phoenix suppliers will pay to fix portal re-keying."* Friction signals exist; buy signals don't. The next 4–8 weeks are sales, not code.

### The offer (not LOIs — LOIs are validation theater)

| Offer | Price | Customer gives |
|-------|-------|----------------|
| Paid shadow pilot (preferred) | $2–5K / 30 days | Portal logins for 1–3 buyers, ERP export format, 30 min/week review |
| Paid proof-of-value | $500–1K one-time | One portal, one week of POs → we deliver ERP-ready CSV |

Pitch: *"We'll ingest every PO from [Buyer X portal] and deliver ERP-ready orders within 4 hours. You approve before post. Miss a PO → full refund."*

### Keep-going criteria (need 2 within 60 days)

1. ≥1 paid pilot at $2K+/month (or $5K one-time)
2. Real portal credentials within 2 weeks of asking
3. Customer quantifies pain in hours/week or $/order (not "it's annoying")
4. Pull: customer asks to add a second portal unprompted
5. Unprompted referral to another supplier

**Shelve trigger:** 15+ conversations, zero portal creds, zero budget discussion after directly asking *"If we did this for 30 days, is there $3K in the budget?"*

### The wedge (sharpened)

Not "we automate browsers" (commodity — Skyvern, UiPath). Not email/PDF ingestion (lost — Canals, OrderPier, Modusbridge). The wedge:

> **For mid-market distributors whose buyers force them onto custom portals (not EDI, not Coupa API), we turn portal POs into ERP-ready orders with buyer-SKU → your-SKU mapping.**

Browser automation is plumbing; the **per-buyer SKU crosswalk** is the moat. Vertical ICP (e.g. SAP B1 distributors in Phoenix foodservice/industrial) is the GTM filter, not a product pivot. If discovery shows portals are <20% of order volume for the ICP, pivot the wedge, not the tech.

### This week's assignment

Three Phoenix conversations. In each, obtain:

1. Top 3 buyer portals by order volume (named)
2. Hours/week spent on portal re-key
3. Live screen-share of one portal login workflow

Offer: *"Give us read-only access to one buyer portal. We'll deliver last week's POs ERP-ready in 48 hours. $500 credit toward a pilot if we miss one."*

No portal access after 3 tries → wrong ICP or wrong wedge; adjust before writing more code.

### Discovery questions (verbatim)

- "Walk me through yesterday. How many portal logins? How long each?"
- "What % of orders arrive via buyer portal vs email, phone, EDI?"
- "Which 3 buyers force portal usage? Rank by order volume."
- "What does a mis-keyed order cost you? Last time it happened?"
- "If your best portal person quit tomorrow, what breaks?"
- "What are you spending today to solve this? FTE, overtime, errors?"
- "If this worked tomorrow, who signs the check? What budget line?"
- "Have you tried Canals / Conexiom / a VA? Why didn't it stick?"
- "Did your buyer offer EDI or API? Why didn't you take it?"
- **Kill shot:** "If we ran your top portal for 30 days and delivered every PO ERP-ready, would you pay $3,000? Who approves that?"

### YC implications

- Crowded market ≠ dead application; weak insight + no pull = dead application.
- 1–3 design partners **paying $2K+/mo with portal access** is a real story; unpaid design partners are table stakes.
- Expected partner questions and our answers:
  - *"Why won't Canals add portal scraping?"* — buyer-side auth, portal fragmentation, per-buyer SKU crosswalk; not their ICP (they own email intake).
  - *"Why won't Skyvern win?"* — horizontal RPA; we're a vertical order desk with ERP + SKU intelligence.
  - *"Show me a customer who panicked when you turned it off."* — this is what the pilot must produce.

---

## Why We Originally Considered Shelving

The problem is **real**. The prototype **works**. We shelved because the **go-to-market path as a generalist indie product** looks crowded and capital-intensive, not because the technical idea failed.

### Reasons (ranked)

1. **Many funded competitors** already sell "messy inbound order → ERP-ready order" (see below). They have ERP connectors, sales teams, and paying distributors.

2. **Browser automation is commoditized.** Skyvern, Browser-Use, Firecrawl, UiPath, and open-source agent frameworks cover portal login/scrape. Scruffy's agent loop is good engineering, not a standalone moat.

3. **The hard part isn't extraction — it's distribution + trust.** Suppliers won't hand portal credentials to an unknown vendor without SOC2, references, and ERP write-back.

4. **Email/PDF may be the bigger channel.** Several competitors argue buyer portals are shrinking as buyers auto-submit via QuickBooks/Xero integrations. Portal pain is real but may be a narrowing wedge.

5. **Building alone without customer pilots** felt like racing Canals/Proton toward a finish line they already passed.

### What we did *not* conclude

- The pain isn't fake (suppliers do waste hours on portal entry).
- The architecture isn't wrong (deterministic shell + LLM router scales).
- The codebase isn't throwaway (eval harness, portal fixtures, agent loop are reusable).

---

## Competitive Landscape (July 2026)

### Tier 1 — AI order entry (closest to Scruffy's full vision)

These products: intake (email/PDF/voice/portal) → SKU match → human review → ERP post.

| Company | Notes | Signal |
|---------|-------|--------|
| [Canals](https://www.canals.ai/) | Order entry, AP, purchasing for distributors | $35M Series A (May 2026), 100+ distributors, 8M+ orders |
| [Proton.ai](https://www.proton.ai/) | Industry cloud: CRM, PIM, order/quote entry | ~$20M raised, distribution-native |
| [Modusbridge](https://www.modusbridge.com/) | Per-field confidence, SKU cross-ref, human review | Very close to planned Phase 3 |
| [OrderPier](https://orderpier.com/) | Email PO → Dynamics / QuickBooks | Self-serve, ERP connectors |
| [PO2Order](https://po2order.com/) | Email/PDF/image → commerce platform / ERP | Self-serve positioning |
| [OrderSync](https://ordersync.io/) | "Otto" agent, multi-channel including portals | NetSuite, SAP, Dynamics connectors |
| [Nativ](https://www.gonativ.ai/) | Execution layer: email, PDF, EDI, portals → ERP | Enterprise, "live in weeks" |
| [Fask](https://fask.ai/) | Procurement ops agents across Coupa, Ariba, ERP | Portal + email + EDI |

### Tier 2 — Browser / portal automation (Scruffy's extract layer)

| Company / tool | Notes |
|----------------|-------|
| [Skyvern](https://www.skyvern.com/) | Vision + LLM browser agents for procurement portals |
| Browser-Use, Stagehand, Firecrawl | Open-source / managed agent frameworks |
| UiPath, Automation Anywhere | Legacy RPA; brittle but entrenched |
| Automatio.ai | Login + scrape behind auth walls |

### Tier 3 — Platform incumbents adding AI

| Company | Notes |
|---------|-------|
| Coupa (Navi agents) | Buyer-side AI; suppliers still use CSP manually for many tasks |
| ERP vendors (NetSuite, SAP, etc.) | Native or partner OCR/IDP modules |

### Scruffy's differentiation (if any)

| Angle | Assessment |
|-------|------------|
| Supplier logs into **buyer** portal | Less marketed than email, but Nativ/Fask/Skyvern mention portals |
| Agentic (not template RPA) | Table stakes in 2026 |
| Self-hosted / local LLM | Niche advantage for privacy-conscious suppliers; not a mass GTM |
| Eval harness + fake portals | Useful internally or as devtool; not a standalone product |

**Honest summary:** Scruffy is a strong **prototype** in a **contested category**. Winning as a horizontal "portal agent for all suppliers" requires GTM + integrations, not more portal variants.

---

## If You Pick This Up Later

### Suggested order of operations

1. **Read this doc + run smoke eval** — confirm environment still works (Ollama box, Playwright).
2. **Talk to Phoenix customers before writing code** — see "Customer discovery questions" below.
3. **Shadow mode on one real portal** — read-only extraction, compare to human-entered order; don't write to ERP yet.
4. **Phase 3 only if normalization is the bottleneck** — interview customers: is extract or SKU mapping the pain?
5. **One ERP connector** — only for the ERP your Phoenix customers actually use.
6. **Re-run eval after any model/prompt change** — that's what the infra is for.

### Customer discovery questions (Phoenix)

Use these on supplier calls before building more:

- How many buyer portals do you log into per week?
- What % of orders arrive via portal vs email vs EDI vs phone?
- Cost of a mis-keyed order (dollars, relationship, chargebacks)?
- Would you pay $X/month per portal automated? What's X?
- Who owns portal login credentials today (ops, CS, owner)?
- Would you run shadow mode (Scruffy extracts, human still enters) for 30 days?
- Which ERP? Which 2–3 buyers hurt most?

### Technical next steps (if validated)

| Priority | Work |
|----------|------|
| P0 | Shadow extraction on 1 real portal (with permission) |
| P1 | Phase 3 normalization + SKU catalog from customer data |
| P2 | Credential vault + audit log (minimum for production trust) |
| P3 | ERP write-back for one system |
| Deprioritize | More fake portal variants until real portal works |

---

## YC: Does It Still Make Sense?

**Short answer:** Customers in Phoenix change the calculus. Competition alone is not a reason to stop. **Lack of customer-driven wedge** might be.

### What YC actually weights

| Factor | Scruffy today | With Phoenix customers |
|--------|---------------|------------------------|
| Problem | Real, painful | Stronger if customers confirm $ pain |
| Market size | Huge (B2B order entry) | Same |
| Competition | Crowded | OK if you have insight competitors miss |
| Traction | Prototype + eval | **Pilots, LOIs, or revenue flip this** |
| Founder insight | Technical depth proven | Needs **customer-derived** insight |
| Speed | Good build velocity | Need customer iteration velocity |

YC funds teams entering crowded markets constantly (Canals just raised $35M — YC may still fund an adjacent play). They care whether **you** can win a wedge, not whether the category is empty.

### When pushing through *does* make sense for YC

- **3–5 Phoenix suppliers** agree to pilot shadow mode or paid pilot ($500–2k/mo).
- You can articulate a **sharp wedge**, e.g.:
  - "Southwest food distributors on SAP B1 with Coupa buyers"
  - "Suppliers where 40%+ of orders are portal-only (not email)"
  - "Replacement for a specific ops hire ($45k/yr) at 10× ROI"
- You have **metrics**: orders/month, minutes saved, error rate vs human, willingness to pay.
- Application story is: *"We talked to 20 suppliers. Portal is 35% of volume for 8 of them. We built X. Customer Y is piloting."*

### When it *doesn't* make sense

- Building more fake portals / agent features without customer calls.
- Phoenix "customers" are friends who haven't seen the product or committed to a pilot.
- Their pain is mostly **email PDF**, not portal — you'd be pitching the wrong product vs OrderPier/Canals.
- You can't get portal credentials or legal approval for automation.

### Recommended YC path (if pursuing)

1. **2 weeks customer discovery** in Phoenix — no new code.
2. **1 design partner** — shadow mode on their worst portal.
3. **Quantify** — "$ saved per order" or "hours/week" from that pilot.
4. **Apply with that story** — prototype + pilot data beats competitor fear.
5. **Phase 3 + one ERP** only for that design partner's stack.

Don't apply with "we built an agent and there are competitors." Apply with "suppliers in Phoenix pay humans $X to do Y; we automated Y for customer Z; they want to pay."

---

## Repo Map (quick reference)

```
scruffy/
├── docs/
│   ├── portal-research.md      # Why Coupa-style portals, v1 design
│   └── project-handoff.md      # This file
├── eval/cases.json             # Agent eval case registry
├── portals/v1|v2|v3/           # Fake buyer portals (:8000/8001/8002)
├── scripts/
│   ├── run_agent.py            # Single agent run (--po for target order id)
│   └── run_eval.py             # Full eval suite
└── src/scruffy/
    ├── agent/                  # ReAct loop, executor, loop_guard
    ├── eval/                   # EvalRunner, scorer, reports
    ├── browser/                # Playwright, observation, scraper
    └── llm/                    # Ollama client, prompts, BrowserAction
```

---

## Decision Log

| Date | Decision | Rationale |
|------|----------|-----------|
| 2026-07-06 | Considered shelving | Crowded market; GTM/integration bar too high for solo build-without-customers |
| 2026-07-06 | Keep repo + docs | Prototype works; reusable for resume, YC, or customer pilots |
| 2026-07-06 | Push to `main` | Preserve eval baseline and portal v1–v3 |
| 2026-07-07 | **Reverse shelve → 60-day validation gate** | External review (gstack): friction ≠ budget; test willingness to pay before killing or building. Freeze code; run paid shadow pilots in Phoenix |
| 2026-07-07 | Drop LOIs in favor of paid pilots | LOIs cost the customer nothing and prove nothing about budget |

---

*Last updated: 2026-07-07. Next review: end of the 60-day gate (~2026-09-05), or earlier if a pilot lands.*
