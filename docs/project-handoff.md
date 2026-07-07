# Scruffy — Project Handoff (July 2026)

This document records where the project stopped, why it was shelved, the competitive landscape, and how to pick it back up — including notes on a potential YC path.

**Status:** Shelved (not abandoned). Code is on `main`, pushed to GitHub. The prototype works end-to-end on fake portals; real customer validation in Phoenix was not completed in-repo.

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

## Why We Shelved

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
| 2026-07 | Shelve active development | Crowded market; GTM/integration bar too high for solo build-without-customers |
| 2026-07 | Keep repo + docs | Prototype works; reusable for resume, YC, or customer pilots |
| 2026-07 | Push to `main` | Preserve eval baseline and portal v1–v3 |

---

*Last updated: July 2026. Revisit when resuming customer conversations in Phoenix or applying to YC.*
