from playwright.sync_api import Page


def extract_html_table(page: Page, table_selector: str = "table") -> list[dict[str, str]]:
    """Extract an HTML table into a list of row dicts keyed by header text."""
    table = page.locator(table_selector).first
    if table.count() == 0:
        return []

    headers = [
        h.strip()
        for h in table.locator("thead th").all_inner_texts()
    ]
    if not headers:
        headers = [
            h.strip()
            for h in table.locator("tr").first.locator("th, td").all_inner_texts()
        ]

    rows: list[dict[str, str]] = []
    body_rows = table.locator("tbody tr") if table.locator("tbody tr").count() else table.locator("tr")
    for i in range(body_rows.count()):
        cells = [c.strip() for c in body_rows.nth(i).locator("td").all_inner_texts()]
        if not cells:
            continue
        row = {headers[j]: cells[j] for j in range(min(len(headers), len(cells)))}
        rows.append(row)

    return rows


def extract_inventory_items(page: Page) -> list[dict[str, str]]:
    """Extract product cards from saucedemo.com inventory page."""
    items: list[dict[str, str]] = []
    cards = page.locator(".inventory_item")
    for i in range(cards.count()):
        card = cards.nth(i)
        name = card.locator(".inventory_item_name").inner_text().strip()
        description = card.locator(".inventory_item_desc").inner_text().strip()
        price = card.locator(".inventory_item_price").inner_text().strip()
        items.append({"name": name, "description": description, "price": price})
    return items
