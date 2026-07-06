# Fake Buyer Portals

Local test portals for Scruffy browser agent evaluation. Each portal variant simulates a different B2B buyer with intentionally messy data.

## Planned variants

| Portal | Challenge |
|--------|-----------|
| `v1` | Simple orders table, clean headers |
| `v2` | Messy column names (`Qty` vs `Quantity`) |
| `v3` | Pagination across multiple pages |
| `v4` | CSV export only (no visible table) |
| `v5` | Detail page per PO (click-through) |

## Terminology mismatch (test data)

Buyer calls it → Supplier SKU:

- Sweet-Disk → Choc-1
- Crunch-Bar → SNK-42
- Fizz-Pop → BEV-7

Coming in Phase 1b.
