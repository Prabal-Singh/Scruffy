# Fake Buyer Portals

Local test portals for Scruffy browser agent evaluation.

## v1 — Midwest Foods Vendor Portal

Coupa-style supplier portal. A supplier logs in to view purchase orders issued by the buyer.

### Start the portal

```bash
pip install -e ".[portal]"
python portals/v1/server.py
# → http://127.0.0.1:8000
```

### Credentials

| Field | Value |
|-------|-------|
| Email | `vendor@scruffy.test` |
| Password | `scruffy123` |

### Scrape a PO

```bash
# portal must be running
python scripts/scrape_buyer_portal.py
python scripts/scrape_buyer_portal.py --headed --po PO-1042
```

### Test data (buyer terminology ≠ supplier SKU)

| Buyer description | Buyer code | Supplier SKU (not shown on portal) |
|-------------------|------------|-------------------------------------|
| Sweet-Disk | SWT-DSK | Choc-1 |
| Crunch-Bar | CRN-BAR | SNK-42 |
| Fizz-Pop | FIZ-POP | BEV-7 |

See [docs/portal-research.md](../docs/portal-research.md) for design rationale.

## v2 — Pacific Retail Supplier Portal

Same Coupa-style layout and `data-testid`s as v1, but **messy column headers** and **inconsistent UOM labels** (`CASE`, `each`, `EA`).

### Start the portal

```bash
pip install -e ".[portal]"
python portals/v2/server.py
# → http://127.0.0.1:8001
```

Credentials are the same as v1.

### Scrape a PO

```bash
python scripts/scrape_buyer_portal.py --url http://127.0.0.1:8001
python scripts/scrape_buyer_portal.py --url http://127.0.0.1:8001 --headed --po PO-1042
```

### What v2 tests

| v1 header | v2 header |
|-----------|-----------|
| PO Number | PO # |
| Order Date | Date Placed |
| Status | State |
| Line Items | Line Count |
| Total | Amount |
| Item Code | Buyer SKU |
| Description | Product Name |
| Qty | Quantity |
| UOM | Unit |
| Unit Price | Unit Cost |
| Line Total | Ext. Amount |
