"""Database access and the tools the Campus Customs agent can call.

Every price, description and stock number the agent repeats comes from a function in this file,
which reads data/campus_customs.db. The model never computes or remembers those numbers itself.
"""

from __future__ import annotations

import json
import re
import sqlite3
from pathlib import Path

from pydantic_ai import RunContext

from models import (
    Alternative,
    AlternativesResult,
    CustomerProfile,
    ProductCard,
    ProductDetail,
    SearchResults,
    ShopDeps,
    SizeStock,
    StockCheck,
)

ROOT = Path(__file__).resolve().parent.parent  # hw4/
DATA_DIR = ROOT / "data"
DB_PATH = DATA_DIR / "campus_customs.db"
PRODUCTS_DIR = DATA_DIR / "products"

MAX_SEARCH_RESULTS = 8  # result cap: keeps the model's context (and the page) small
MAX_ALTERNATIVES = 3
SIZE_ORDER = ["XS", "S", "M", "L", "XL", "XXL"]
LOW_STOCK = 3  # "only N left" threshold, shared with the front end via the API

# ---------------------------------------------------------------------------
# Low-level database helpers
# ---------------------------------------------------------------------------


def connect() -> sqlite3.Connection:
    if not DB_PATH.exists():
        raise FileNotFoundError(f"Database not found at {DB_PATH}. Unzip the data pack into hw4/data/.")
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def _json_list(raw: str | None) -> list[str]:
    try:
        value = json.loads(raw or "[]")
        return [str(v) for v in value] if isinstance(value, list) else []
    except json.JSONDecodeError:
        return []


def _short(description: str, limit: int = 120) -> str:
    first = re.split(r"(?<=[.!?])\s", description.strip(), maxsplit=1)[0]
    return first if len(first) <= limit else first[: limit - 1].rsplit(" ", 1)[0] + "…"


def image_url(image_file_path: str) -> str:
    # catalogue stores paths like "products/foo.jpg" relative to data/; FastAPI serves data/products at /media/products
    name = Path(image_file_path).name
    return f"/media/products/{name}"


def _sizes(conn: sqlite3.Connection, product_id: str) -> list[SizeStock]:
    rows = conn.execute("SELECT size, quantity FROM inventory WHERE product_id = ?", (product_id,)).fetchall()
    rows = sorted(rows, key=lambda r: SIZE_ORDER.index(r["size"]) if r["size"] in SIZE_ORDER else 99)
    return [SizeStock(size=r["size"], quantity=r["quantity"], in_stock=r["quantity"] > 0) for r in rows]


def _stock_totals(conn: sqlite3.Connection) -> dict[str, int]:
    return {r[0]: r[1] for r in conn.execute("SELECT product_id, SUM(quantity) FROM inventory GROUP BY product_id")}


def _card(row: sqlite3.Row, total_stock: int) -> ProductCard:
    return ProductCard(
        product_id=row["product_id"],
        name=row["name"],
        garment_type=row["garment_type"],
        price=row["price"],
        short_description=_short(row["description"]),
        colors=_json_list(row["colors"]),
        image_url=image_url(row["image_file_path"]),
        total_stock=total_stock,
    )


def list_products() -> list[ProductCard]:
    with connect() as conn:
        totals = _stock_totals(conn)
        rows = conn.execute("SELECT * FROM catalogue ORDER BY name").fetchall()
        return [_card(r, totals.get(r["product_id"], 0)) for r in rows]


def get_cards(product_ids: list[str]) -> list[ProductCard]:
    """Hydrate product ids into cards from the DB, keeping order and silently dropping unknown ids."""
    if not product_ids:
        return []
    with connect() as conn:
        totals = _stock_totals(conn)
        cards = []
        for pid in dict.fromkeys(product_ids):  # de-duplicate, keep order
            row = conn.execute("SELECT * FROM catalogue WHERE product_id = ?", (pid,)).fetchone()
            if row:
                cards.append(_card(row, totals.get(pid, 0)))
        return cards


def get_product(product_id: str) -> ProductDetail | None:
    with connect() as conn:
        row = conn.execute("SELECT * FROM catalogue WHERE product_id = ?", (product_id,)).fetchone()
        if not row:
            return None
        sizes = _sizes(conn, product_id)
        card = _card(row, sum(s.quantity for s in sizes))
        return ProductDetail(
            **card.model_dump(),
            description=row["description"],
            search_tags=_json_list(row["search_tags"]),
            sizes=sizes,
        )


def resolve_product_id(identifier: str) -> str | None:
    """Accept an exact product_id, a slug-ish id, or a product name, and return the real product_id."""
    ident = identifier.strip()
    slug = re.sub(r"[^a-z0-9]+", "-", ident.lower()).strip("-")
    with connect() as conn:
        for candidate in (ident, slug):
            row = conn.execute("SELECT product_id FROM catalogue WHERE product_id = ?", (candidate,)).fetchone()
            if row:
                return row["product_id"]
        row = conn.execute("SELECT product_id FROM catalogue WHERE lower(name) = ?", (ident.lower(),)).fetchone()
        if row:
            return row["product_id"]
    hits = search_catalogue(ident, limit=1)
    return hits.results[0].product_id if hits.results else None


# ---------------------------------------------------------------------------
# Catalogue search (keyword scoring, no model call)
# ---------------------------------------------------------------------------

STOPWORDS = set(
    "a an and any are can do does for have i in is it me my of on or show some the there to want what which with "
    "you your yours got sell carry looking need please find get options option item items stuff under below than less "
    "cheap price dollars".split()
)
SYNONYMS = {
    "hoodie": ["hood"],
    "hooded": ["hood"],
    "tee": ["tshirt", "tee"],
    "tshirt": ["tshirt", "tee"],
    "shirt": ["shirt"],
    "sweater": ["sweatshirt", "crewneck"],
    "crew": ["crewneck", "crew neck"],
    "grey": ["gray", "grey"],
    "gray": ["gray", "grey"],
    "blue": ["blue", "navy"],
    "zip": ["zip"],
    "quarter": ["quarter"],
    "jacket": ["jacket", "bomber"],
    "fleece": ["fleece"],
}


def _normalise(text: str) -> str:
    text = text.lower().replace("1/4", "quarter").replace("1-4", "quarter").replace("¼", "quarter")
    text = re.sub(r"t[\s-]?shirts?", "tshirt", text)
    text = re.sub(r"[^a-z0-9]+", " ", text)
    return f" {text.strip()} "


def _tokens(query: str) -> list[str]:
    out = []
    for tok in _normalise(query).split():
        if tok in STOPWORDS or len(tok) < 2 or (tok.isdigit() and len(tok) != 4):  # keep years like 2025, drop prices
            continue
        if len(tok) > 3 and tok.endswith("s") and not tok.endswith("ss"):
            tok = tok[:-1]
        out.append(tok)
    return out


def _category(garment_type: str) -> str:
    g = garment_type.lower()
    if "hood" in g:
        return "Hoodies"
    if "quarter" in g:
        return "Quarter-zips"
    if "jacket" in g or "fleece" in g:
        return "Jackets & fleece"
    if "crew" in g or "sweatshirt" in g:  # before tees: "sweatshirt" contains "tshirt"
        return "Crewnecks"
    if re.search(r"\bt-?shirt", g) or "performance" in g:
        return "Tees"
    return "Other"


def search_catalogue(query: str, limit: int = MAX_SEARCH_RESULTS, max_price: float | None = None,
                     size_in_stock: str | None = None) -> SearchResults:
    tokens = _tokens(query)
    size = size_in_stock.strip().upper() if size_in_stock else None
    with connect() as conn:
        totals = _stock_totals(conn)
        scored: list[tuple[float, sqlite3.Row]] = []
        for row in conn.execute("SELECT * FROM catalogue"):
            fields = {
                "name": _normalise(row["name"]),
                "type": _normalise(row["garment_type"]),
                "tags": _normalise(" ".join(_json_list(row["search_tags"]))),
                "colors": _normalise(" ".join(_json_list(row["colors"]))),
                "desc": _normalise(row["description"]),
            }
            weights = {"name": 3, "type": 4, "tags": 2, "colors": 2, "desc": 1}
            score, matched = 0.0, 0
            for tok in tokens:
                alts = SYNONYMS.get(tok, [tok])
                tok_score = max((w for f, w in weights.items() if any(f" {a}" in fields[f] for a in alts)), default=0)  # word-start match
                if tok_score:
                    matched += 1
                    score += tok_score
            if tokens and matched < len(tokens):
                continue  # every meaningful word must match somewhere
            if max_price is not None and row["price"] > max_price:
                continue
            if size:
                q = conn.execute("SELECT quantity FROM inventory WHERE product_id = ? AND size = ?",
                                 (row["product_id"], size)).fetchone()
                if not q or q[0] <= 0:
                    continue
            scored.append((score, row))
    scored.sort(key=lambda t: (-t[0], t[1]["price"], t[1]["name"]))
    cards = [_card(r, totals.get(r["product_id"], 0)) for _, r in scored[:limit]]
    note = ""
    if not scored:
        note = "No products matched every word. Tell the shopper honestly and suggest a broader search (e.g. just the garment type)."
    elif len(scored) > limit:
        note = f"Showing the top {limit} of {len(scored)} matches. Offer to narrow down by color, price or size."
    return SearchResults(query=query, total_matches=len(scored), results=cards, note=note)


def categories() -> dict[str, int]:
    with connect() as conn:
        counts: dict[str, int] = {}
        for (g,) in conn.execute("SELECT garment_type FROM catalogue"):
            c = _category(g)
            counts[c] = counts.get(c, 0) + 1
    return counts


def category_of(product: ProductCard) -> str:
    return _category(product.garment_type)


# ---------------------------------------------------------------------------
# Agent tools (registered in agent.py). Each takes RunContext[ShopDeps] first.
# ---------------------------------------------------------------------------


def search_products(ctx: RunContext[ShopDeps], query: str, max_price: float | None = None,
                    size_in_stock: str | None = None) -> SearchResults:
    """Search the Campus Customs catalogue by keywords (garment type, color, sport, theme, etc.).

    Args:
        query: Short keywords, e.g. "hoodie", "navy crewneck", "harvard yale tshirt". Leave out filler words.
        max_price: Optional upper price limit in USD.
        size_in_stock: Optional size (XS, S, M, L, XL, XXL); only return products with that size in stock.
    """
    ctx.deps.tool_calls.append("search_products")
    return search_catalogue(query, max_price=max_price, size_in_stock=size_in_stock)


def get_product_details(ctx: RunContext[ShopDeps], product: str) -> ProductDetail | str:
    """Get the full description, price, colors and per-size stock for one product.

    Args:
        product: The product_id (preferred) or the product's name.
    """
    ctx.deps.tool_calls.append("get_product_details")
    pid = resolve_product_id(product)
    detail = get_product(pid) if pid else None
    return detail or f"No product found for '{product}'. Use search_products to find the right product_id."


def check_stock(ctx: RunContext[ShopDeps], product: str, size: str | None = None) -> StockCheck | str:
    """Check live stock for a product, optionally for one size. Use this for every stock/availability question.

    Args:
        product: The product_id (preferred) or the product's name.
        size: Optional size the shopper asked about (XS, S, M, L, XL, XXL).
    """
    ctx.deps.tool_calls.append("check_stock")
    pid = resolve_product_id(product)
    detail = get_product(pid) if pid else None
    if not detail:
        return f"No product found for '{product}'. Use search_products to find the right product_id."
    wanted = size.strip().upper() if size else None
    aliases = {"SMALL": "S", "MEDIUM": "M", "LARGE": "L", "EXTRA SMALL": "XS", "EXTRA LARGE": "XL", "2XL": "XXL", "XXXL": "3XL"}
    wanted = aliases.get(wanted, wanted) if wanted else None
    in_stock_sizes = [s.size for s in detail.sizes if s.in_stock]
    match = next((s for s in detail.sizes if s.size == wanted), None) if wanted else None
    if wanted and not match:
        summary = f"{detail.name} is not made in size {wanted}. Sizes in stock: {', '.join(in_stock_sizes) or 'none'}."
    elif match and not match.in_stock:
        summary = f"{detail.name} is SOLD OUT in size {wanted}. Sizes in stock: {', '.join(in_stock_sizes) or 'none'}."
    elif match:
        summary = f"{detail.name} has {match.quantity} in stock in size {wanted} (${detail.price:.2f})."
        if match.quantity <= LOW_STOCK:
            summary += " Low stock."
    else:
        summary = f"{detail.name} (${detail.price:.2f}) — sizes in stock: {', '.join(in_stock_sizes) or 'none (sold out)'}."
    return StockCheck(
        product_id=detail.product_id,
        name=detail.name,
        price=detail.price,
        requested_size=wanted,
        requested_size_quantity=match.quantity if match else (0 if wanted else None),
        requested_size_in_stock=(match.in_stock if match else False) if wanted else None,
        size_exists=bool(match) if wanted else True,
        sizes=detail.sizes,
        summary=summary,
    )


def find_in_stock_alternatives(ctx: RunContext[ShopDeps], product: str, size: str) -> AlternativesResult | str:
    """When a product is sold out in a size, find similar products that ARE in stock in that size.

    Args:
        product: The product_id (or name) the shopper wanted.
        size: The size they need (XS, S, M, L, XL, XXL).
    """
    ctx.deps.tool_calls.append("find_in_stock_alternatives")
    pid = resolve_product_id(product)
    detail = get_product(pid) if pid else None
    if not detail:
        return f"No product found for '{product}'."
    size = size.strip().upper()
    original = next((s for s in detail.sizes if s.size == size), None)
    family = _category(detail.garment_type)
    colors = {c.lower() for c in detail.colors}
    candidates: list[tuple[float, Alternative]] = []
    with connect() as conn:
        totals = _stock_totals(conn)
        for row in conn.execute("SELECT * FROM catalogue WHERE product_id != ?", (detail.product_id,)):
            if _category(row["garment_type"]) != family:
                continue
            q = conn.execute("SELECT quantity FROM inventory WHERE product_id = ? AND size = ?",
                             (row["product_id"], size)).fetchone()
            if not q or q[0] <= 0:
                continue
            shared = colors & {c.lower() for c in _json_list(row["colors"])}
            price_gap = abs(row["price"] - detail.price)
            score = 2 * len(shared) - price_gap / 20
            why = f"also a {family.lower().rstrip('s')}" + (f", also {', '.join(sorted(shared))}" if shared else "")
            why += f", ${row['price']:.0f}"
            candidates.append((score, Alternative(card=_card(row, totals.get(row["product_id"], 0)),
                                                  quantity_in_size=q[0], why=why)))
    candidates.sort(key=lambda t: -t[0])
    return AlternativesResult(
        product_id=detail.product_id,
        size=size,
        original_in_stock=bool(original and original.in_stock),
        alternatives=[a for _, a in candidates[:MAX_ALTERNATIVES]],
    )


def get_customer_profile(ctx: RunContext[ShopDeps]) -> CustomerProfile:
    """Return who is chatting: first/last name, email and member-since date, or logged_in=false for a guest."""
    ctx.deps.tool_calls.append("get_customer_profile")
    return ctx.deps.customer


TOOLS = [search_products, get_product_details, check_stock, find_in_stock_alternatives, get_customer_profile]
