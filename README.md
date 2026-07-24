# Scruffy

**Replacing the "Human API" in B2B commerce.**

Scruffy is an agentic automation layer that logs into buyer portals, extracts raw purchase order (PO) data, normalizes messy text into canonical SKUs, and injects sanitized orders into supplier ERPs.

![Scruffy logo](assets/logo.png)

---

## Problem

B2B suppliers suffer from fragmented, messy order ingestion. Customers use bespoke portals and inconsistent terminology — ordering "Sweet-Disk" when the supplier SKU is `Choc-1`. Humans waste time translating and manually entering these orders.

## Solution

A three-stage pipeline:

| Stage | Tool | Output |
|-------|------|--------|
| **Extract** | Playwright (headless browser) | Raw PO text, line items, buyer metadata |
| **Normalize** | LLM + Pydantic schema | `CanonicalPO { sku, qty, uom, buyer_id }` |
| **Inject** | ERP API (SAP B1, NetSuite) | Order ID, API response |

## Core Mental Model

Agents are **non-deterministic routers inside a deterministic shell**:

```
┌─────────────────────────────────────────────────────────┐
│  DETERMINISTIC SHELL (while loop / LangGraph)           │
│                                                         │
│   observe → reason → act → observe → ... → terminal     │
│              ↑         │                                │
│              │         ▼                                │
│         [LLM router]  [MCP tools]                       │
│         non-det.      det. side effects                 │
└─────────────────────────────────────────────────────────┘
```

**Design rule:** The LLM chooses intent. Playwright executes precise actions. Pydantic validates results. A state machine decides whether to continue.

---

## Hardware

| Machine | Role |
|---------|------|
| **M4 Mac (16GB)** | Dev, orchestration, agent control loop |
| **Linux + RTX 5070 Ti** | Local LLM inference (Ollama / vLLM) over LAN |

Mac fires API requests to the Linux box for inference. Browser automation runs on the Mac.

---

## Tech Stack

| Concern | Choice |
|---------|--------|
| Browser automation | Playwright (Python) |
| Tool interface | Model Context Protocol (MCP) |
| Structured output | Pydantic + Instructor |
| Orchestration | LangGraph (explicit state machines) or raw ReAct loop |
| Lightweight agents | Smolagents (for learning spikes) |
| Testing | pytest + pytest-playwright |

### What we're NOT using (yet)

- Legacy RPA tools (UiPath, etc.)
- Overly abstracted agent frameworks
- Vector DBs for memory (file-based, inspectable state instead)
- Production ERP credentials in early phases

---

## Agent Building Approaches (Reference)

LangGraph is one option, not the only one. Most production agents share the same ReAct loop; the difference is how much infrastructure wraps it.

| Approach | When to use |
|----------|-------------|
| **Raw `while` loop** | Learning, full control, minimal deps (Claude Code uses this) |
| **LangGraph** | Named states, branching, HITL gates, auditability |
| **Smolagents** | Lightweight code-first agents |
| **MCP servers** | Standardized tool exposure (orthogonal to the loop) |
| **Temporal / durable workflows** | Long-running cloud agents (Cursor cloud agents use this) |

Claude Code and Cursor IDE agents are essentially **hand-rolled ReAct loops** with heavy investment in permissions, context management, tool concurrency, and subagent isolation — not LangGraph.

---

## Testing Strategy

Do not start by scraping real buyer portals. Use a layered approach:

```
        /\
       /  \   E2E on fake portal (few, slow)
      /----\
     /      \  DOM/fixture extraction tests (many, fast)
    /--------\
   /          \  Schema / normalization tests (many, very fast)
  /------------\
```

| Layer | Target | Purpose |
|-------|--------|---------|
| **1. Public practice sites** | saucedemo.com, practice.expandtesting.com | Learn Playwright mechanics |
| **2. Fake buyer portal** | `portals/` (local, we control it) | PO-specific extraction + agent eval |
| **3. Recorded fixtures** | Saved HTML, HAR, Playwright traces | Fast deterministic CI |
| **4. Real customer portals** | With explicit permission, sandbox creds | Validation only, shadow mode first |

### Evaluation fixtures (target set)

| Fixture | Challenge |
|---------|-----------|
| `login_basic` | Simple auth |
| `table_clean` | Straightforward extraction |
| `table_messy_headers` | Semantic column mapping |
| `pagination` | Multi-page collection |
| `csv_export` | Download parsing |
| `detail_page` | Click-through per PO |
| `hidden_export` | Menu navigation |
| `empty_orders` | Graceful no-op |
| `session_expired` | Recovery behavior |
| `broken_selector` | Retry / fail clearly |

---

## Phased Roadmap

### Phase 1 — Headless Browser Agents ✓

**Goal:** Deterministic Playwright harness. No LLM yet.

- [x] Project scaffold
- [x] Playwright on public practice site (login, table scrape, screenshot, trace)
- [x] Pydantic models for `RawPurchaseOrder`
- [x] Browser observation format (compact DOM → element map)
- [x] Fake buyer portal v1 (`portals/v1`)
- [x] Golden JSON tests against fixtures

### Phase 1.5 — Observation Layer ✓

**Goal:** Compress pages into typed snapshots for future agent loops.

- [x] `PageObservation` schema (`url`, `title`, `visible_text`, `interactive_elements`, `tables`)
- [x] `capture_page_observation()` via Playwright
- [x] `scripts/dump_observation.py` CLI
- [x] Tests against fake buyer portal pages

### Phase 1.75 — LLM connectivity ✓

**Goal:** Verify Mac → Linux Ollama path before Phase 2 agent loop.

- [x] `OllamaClient` + `BrowserAction` schema
- [x] `scripts/test_ollama.py` smoke + structured JSON test
- [x] Default inference: `http://192.168.0.7:11434` / `qwen2.5:14b`

### Phase 2 — Constrained Browser Agent (current)

**Goal:** LLM chooses from a typed action menu. Playwright executes.

- [x] Action schema: `click`, `type`, `extract_table`, `finish`, `fail`
- [x] Observation layer: URL + visible text + interactive element map
- [x] ReAct loop (`observe → LLM → act → repeat`)
- [x] `scripts/run_agent.py` CLI with step trace
- [x] Eval runner scoring extraction accuracy across portal variants

### Phase 3 — Semantic Normalization

**Goal:** Map messy buyer text to canonical SKUs.

- [ ] `CanonicalPurchaseOrder` Pydantic schema
- [ ] Instructor + local LLM on Linux box
- [ ] SKU catalog fixture
- [ ] Confidence scores + evidence fields

### Phase 4 — MCP Tool Servers

**Goal:** Expose browser + normalization as MCP tools.

- [ ] `scruffy-browser` MCP server (Playwright operations)
- [ ] `scruffy-normalize` MCP server (PO → canonical)
- [ ] Tool-callable from any agent loop

### Phase 5 — Pipeline Orchestration

**Goal:** Explicit state machine for the full ingest flow.

- [ ] LangGraph: `portal_login → po_extracted → normalized → injected → done`
- [ ] Human-in-the-loop gates for low-confidence mappings
- [ ] Audit trail per PO

### Phase 6 — ERP Injection

**Goal:** Push canonical POs into supplier systems.

- [ ] Mock ERP API
- [ ] SAP B1 / NetSuite adapter (sandbox)
- [ ] Idempotent order creation

### Phase 7 — Customer Shadow Mode

**Goal:** Run against real portals with permission.

- [ ] Read-only extraction on customer sandbox
- [ ] Compare Scruffy output vs human-entered orders
- [ ] Supervised write actions

---

## Project Structure

```
scruffy/
├── assets/              # Logo, screenshots
├── docs/                # Research notes (portal-research.md, project-handoff.md)
├── eval/                # Agent eval case registry (cases.json)
├── portals/v1/          # Fake Coupa-style buyer portal (clean headers)
├── portals/v2/          # Messy column headers + UOM variants
├── portals/v3/          # Paginated orders list (PO-1042 on page 2)
├── scripts/             # Runnable demos
├── src/scruffy/
│   ├── agent/           # ReAct loop, action executor
│   ├── eval/            # Case registry, scorer, runner, reports
│   ├── browser/         # Playwright runner, observation, scraper
│   ├── llm/             # Ollama client, prompts, BrowserAction
│   └── models/          # Pydantic schemas (PO, observation)
└── tests/               # pytest + playwright + ollama tests
```

---

## Quick Start

```bash
# Install dependencies
pip install -e ".[dev,portal]"

# Install Playwright browsers
playwright install chromium

# Start fake buyer portal (terminal 1) — v1 on :8000, v2 on :8001
python portals/v1/server.py
python portals/v2/server.py
python portals/v3/server.py

# Scrape a PO (terminal 2)
python scripts/scrape_buyer_portal.py --headed
python scripts/scrape_buyer_portal.py --url http://127.0.0.1:8001 --headed
python scripts/scrape_buyer_portal.py --url http://127.0.0.1:8002 --headed

# Dump page observation JSON (portal must be running)
python scripts/dump_observation.py --page orders
python scripts/dump_observation.py --page po --po PO-1042 --headed

# Test Linux Ollama box (Qwen)
python scripts/test_ollama.py
# or: SCRUFFY_OLLAMA_URL=http://192.168.0.7:11434 python scripts/test_ollama.py

# Run constrained browser agent (portal + Ollama required)
python scripts/run_agent.py --headed

# Run agent eval suite (manages portals; needs Ollama)
python scripts/run_eval.py --list
python scripts/run_eval.py --tag smoke
python scripts/run_eval.py --case v2_po_1042

# Run practice site scraper
python scripts/scrape_practice_site.py

# Run tests
pytest -m browser
pytest -m eval             # eval infra unit tests
pytest -m ollama          # needs Linux box online
pytest -m slow            # full agent loop E2E (portal + Ollama)
```

---

## Phase 2 — Current Focus

Scruffy now runs a **constrained ReAct loop**:

```text
observe page → ask Qwen for BrowserAction → Playwright executes → repeat → finish
```

```bash
# terminal 1
python portals/v1/server.py

# terminal 2
python scripts/run_agent.py --headed
```

Default goal: log in → open PO-1042 → extract line items.

**Inference defaults**

| Setting | Value |
|---------|-------|
| `SCRUFFY_OLLAMA_URL` | `http://192.168.0.7:11434` |
| `SCRUFFY_OLLAMA_MODEL` | `qwen2.5:14b` |

**Allowed actions:** `click`, `type`, `extract_table`, `finish`, `fail`

### Eval runner

Case registry lives in `eval/cases.json`. Each case defines portal variant, target PO, golden fixture, and tags. `EvalRunner` manages portal lifecycle, runs the agent, scores extraction accuracy, and writes timestamped JSON to `eval-results/`.

Reports include per-case metrics: step count, total duration, LLM duration, agent success, extraction pass/fail, and field-level PO mismatches.

```bash
python scripts/run_eval.py --tag smoke
# → eval-results/<run_id>/report.json
# → eval-results/<run_id>/summary.json
```

The agent trace prints each step (URL, action, reason, outcome) so you can judge whether Qwen is good enough before scaling evals across more portal variants.

### FixtureBench dogfood (external suite)

Scruffy plugs into [FixtureBench](https://github.com/Prabal-Singh/fixturebench) — the shared procurement-portal eval suite — via `scruffy.fixturebench_agent`.

```bash
pip install -e ".[portal,dev,fixturebench]"
playwright install chromium

# Deterministic Scruffy agent (CI) — published score: 4/4 smoke
PYTHONPATH=src:. fixturebench run \
  --agent scruffy.fixturebench_agent:ScruffyDeterministicAgent \
  --tag smoke

# Agentic Scruffy (needs Ollama)
PYTHONPATH=src:. fixturebench run \
  --agent scruffy.fixturebench_agent:ScruffyAgenticAdapter \
  --tag hard
```

GitHub Actions runs the smoke dogfood job on every push. Scores live in FixtureBench [`docs/scores.md`](https://github.com/Prabal-Singh/fixturebench/blob/main/docs/scores.md).

---

## Customer Discovery (Parallel Track)

While building, continue validating with suppliers:

- How many buyer portals do they log into daily?
- What % of orders arrive via portal vs email vs EDI?
- Where do SKU mismatches cause the most pain?
- What does a failed order ingestion cost them?

The prototype exists to **learn agentic concepts** and **demo the extraction problem** — not as a finalized product roadmap.

> **Build frozen — 60-day demand-validation gate (July 2026).** No new code until a paid shadow pilot lands in Phoenix. See [docs/project-handoff.md](docs/project-handoff.md) for status, competitive landscape, the external review verdict, and keep/shelve criteria.
