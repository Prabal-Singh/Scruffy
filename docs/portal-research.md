# B2B Portal Research

Research notes for building realistic Scruffy test portals. Saved before implementing `portals/v1`.

---

## Which portal type Scruffy models

Scruffy logs into **buyer-owned supplier/vendor portals** (Archetype A) — not distributor ordering sites where retailers place carts.

| Archetype | Who logs in | Portal owner | Scruffy? |
|-----------|-------------|--------------|----------|
| **A — Supplier/vendor portal** | Supplier | Buyer (retailer, enterprise) | **Yes** |
| **B — Distributor ordering portal** | Retailer/buyer | Distributor/supplier | No |

**Archetype A flow:**

```text
Login → Orders (list) → PO detail → Line items table → (optional) Export CSV / Acknowledge
```

**Archetype B flow** (saucedemo.com — good for Playwright practice only):

```text
Login → Catalog → Cart → Checkout
```

---

## Real-world references

### Coupa Supplier Portal (primary v1 reference)

Mid-market procurement. Suppliers log in at [supplier.coupa.com](https://supplier.coupa.com) to view POs from Coupa-based buyers.

**Navigation:** `Orders` → `Purchase Orders` tab / `Order Lines` tab

**PO list columns** ([Coupa docs](https://docs.coupa.com/en/supplier-documentation/coupa-for-suppliers/the-coupa-supplier-portal-or-csp/features-and-processes-in-the-coupa-supplier-portal/purchase-orders/view-and-manage-pos)):

| Column | Meaning |
|--------|---------|
| PO Number | Clickable link to detail |
| Order Date | When buyer created PO |
| Status | Open, Acknowledged, Closed |
| Acknowledged At | Supplier acknowledgment timestamp |
| Items | Summary of line items |
| Total | Dollar total |

**Order Lines columns** ([view PO lines](https://docs.coupa.com/en/supplier-documentation/coupa-for-suppliers/the-coupa-supplier-portal-or-csp/features-and-processes-in-the-coupa-supplier-portal/purchase-orders/view-po-lines)):

| Column | Meaning |
|--------|---------|
| PO Number | Header link |
| Line | Line number |
| Item | Buyer item name/description |
| Total Item Quantity | Quantity |
| Line Total | Extended price |
| Need By | Requested delivery |
| Order Date | |
| Delivery Date | |
| Confirmation Status | |

Also: customer selector dropdown, search/filter, **Export CSV/Excel**.

### Walmart Supplier One (enterprise retail)

Large-retail vendor portal. [Supplier One docs](https://supplierone.helpdocs.io/article/ynseml4roz-getting-started), [Order Management API](https://developer.walmart.com/suppliers/reference/getallwalmartpurchaseorders).

**PO header fields:** `purchaseOrderID`, `hostPurchaseOrderId`, `purchaseOrderStatus` (ACTIVE/CANCELLED/CLOSED), `createdAt`, `mustArriveByDate`, `supplierId`, `supplierName`

**UI:** Left nav `Orders` → filterable list → PO detail with line-level breakdown. Denser than Coupa; more supply-chain status fields.

### Target Partners Online

Retailer vendor management alongside EDI. [Target EDI guide](https://www.crstl.ai/blog/target-edi-requirements). EDI for transactions; portal for visibility, compliance, chargebacks.

### Wholesale distributor portals (contrast only)

[OrderEase](https://www.orderease.com/b2b-customer-portal), [Ximple](https://www.ximplesolution.com/b2b-ordering-portal-wholesale/), [Ask the Ledger guide](https://asktheledger.com/blog/b2b-ecommerce-for-wholesale-distributors.html).

Optimize for catalog browse, quick reorder, customer-specific pricing, inventory — buyer-facing, not supplier PO extraction.

---

## PO data model (fields that matter)

Synthesized from Coupa, Oracle `PO_LINES_ALL`, Walmart APIs.

### Header (minimum viable)

```json
{
  "po_number": "PO-1042",
  "order_date": "2026-07-01",
  "status": "Open",
  "buyer_name": "Midwest Foods Co-op",
  "ship_to": "Warehouse B, 123 Industrial Pkwy",
  "requested_delivery_date": "2026-07-08",
  "currency": "USD",
  "total_amount": 482.40
}
```

### Line (minimum viable)

```json
{
  "line_number": 1,
  "buyer_item_code": "SWT-DSK",
  "description": "Sweet-Disk",
  "quantity": 24,
  "uom": "CS",
  "unit_price": 12.50,
  "line_total": 300.00
}
```

### Where SKU mapping pain comes from

- `Item` / `description` uses **buyer terminology** ("Sweet-Disk")
- Supplier SKU (`Choc-1`) often **not shown** on the portal
- Buyer item codes may appear in a separate column with inconsistent naming
- UOM varies (`CS`, `EA`, `CASE`, `each`)
- Column names differ per buyer portal

---

## v1 design decision

**Model `portals/v1` after Coupa Supplier Portal (simplified).**

### Pages

```text
/login
/orders              PO list table
/orders/{po_number}  PO header + line items
```

### Intentional messiness (test data)

| Buyer says | Buyer code | Supplier SKU (not on portal) |
|------------|------------|------------------------------|
| Sweet-Disk | SWT-DSK | Choc-1 |
| Crunch-Bar | CRN-BAR | SNK-42 |
| Fizz-Pop | FIZ-POP | BEV-7 |

### Deferred to later variants

| Variant | Challenge |
|---------|-----------|
| v2 | Messy column headers (`Qty` vs `Quantity`) |
| v3 | Pagination |
| v4 | CSV export only |
| v5 | Detail-page-only line items |

---

## Open-source pattern references (don't fork)

| Project | Borrow |
|---------|--------|
| [Bagisto B2B Suite](https://github.com/bagisto/b2b-suite) | Company PO list, SKU quick-order |
| [Spree B2B](https://github.com/spree/spree) | Buyer orgs, price lists |
| Coupa docs | Table columns, nav structure, CSV export |

---

## Testing sources

| Source | Use |
|--------|-----|
| `portals/v1` (Coupa-style) | Primary Scruffy eval + golden tests |
| saucedemo.com | Playwright mechanics only |
| practice.expandtesting.com | Login/table/download drills |
| Real customer portals | Shadow mode only, with permission |
