"""Pydantic / PydanticAI types shared by the API (main.py), the agent (agent.py) and its tools (tools.py)."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal

from pydantic import BaseModel, Field

# ---------------------------------------------------------------------------
# Catalogue types (what the shop and the agent's tools return)
# ---------------------------------------------------------------------------


class SizeStock(BaseModel):
    """One row of the inventory table for a product."""

    size: str = Field(description="Size label, e.g. XS, S, M, L, XL, XXL.")
    quantity: int = Field(description="Units on hand right now, straight from the inventory table.")
    in_stock: bool = Field(description="True when quantity > 0, so nobody has to re-derive it.")


class ProductCard(BaseModel):
    """The compact product shape the website renders as a card (Products page and chat results)."""

    product_id: str = Field(description="Primary key of the catalogue table; also the URL slug /products/{product_id}.")
    name: str
    garment_type: str = Field(description="e.g. 'pullover hoodie', 'short-sleeve t-shirt'.")
    price: float = Field(description="USD price from the catalogue table. Never invented by the model.")
    short_description: str = Field(description="First sentence of the catalogue description, trimmed for a card.")
    colors: list[str] = Field(default_factory=list)
    image_url: str = Field(description="Browser path to the product photo, served by FastAPI under /media/products/.")
    total_stock: int = Field(0, description="Units across all sizes, so cards can show 'sold out' without a second call.")


class ProductDetail(ProductCard):
    """Everything the single-item page and the get_product_details tool need."""

    description: str
    search_tags: list[str] = Field(default_factory=list)
    sizes: list[SizeStock] = Field(default_factory=list)


class StockCheck(BaseModel):
    """Result of the check_stock tool: the database's answer to 'do you have X in size Y?'."""

    product_id: str
    name: str
    price: float
    requested_size: str | None = Field(None, description="Size the shopper asked about, normalised (e.g. 'm' -> 'M').")
    requested_size_quantity: int | None = Field(None, description="Units of the requested size; 0 means sold out.")
    requested_size_in_stock: bool | None = Field(None, description="None when no size was asked about.")
    size_exists: bool = Field(True, description="False when the product is never made in the requested size.")
    sizes: list[SizeStock] = Field(description="Every size with its live quantity, so the agent can offer alternatives.")
    summary: str = Field(description="Plain-English one-liner the agent can repeat without doing arithmetic.")


class SearchResults(BaseModel):
    """Result of the search_products tool."""

    query: str
    total_matches: int = Field(description="How many products matched before the cap was applied.")
    results: list[ProductCard] = Field(description="Best matches first, capped (see MAX_SEARCH_RESULTS in tools.py).")
    note: str = Field("", description="Hint for the agent, e.g. 'no matches, try a broader word'.")


class Alternative(BaseModel):
    """A product that is in stock in the size the shopper wanted (usability improvement: alternatives tool)."""

    card: ProductCard
    quantity_in_size: int
    why: str = Field(description="Short reason this is a sensible swap, e.g. 'same garment type, also navy'.")


class AlternativesResult(BaseModel):
    product_id: str
    size: str
    original_in_stock: bool
    alternatives: list[Alternative]


class CustomerProfile(BaseModel):
    """The only customer fields the agent can see. No password hash, no internal id."""

    logged_in: bool
    first_name: str | None = None
    last_name: str | None = None
    email: str | None = None
    member_since: str | None = None


class PageContext(BaseModel):
    """Where the shopper is on the site when they send a chat message."""

    path: str = Field("/", max_length=200, description="Front-end route, e.g. /products/basic-hoodie-big-yale.")
    product_id: str | None = Field(None, max_length=120, description="Set when the shopper is on a single-item page.")
    product_name: str | None = Field(None, max_length=200)


# ---------------------------------------------------------------------------
# Agent output (structured) and run-time dependencies
# ---------------------------------------------------------------------------


class AgentReply(BaseModel):
    """What the PydanticAI agent must return each turn (its output_type)."""

    message: str = Field(description="Reply to the shopper in Campus Customs voice. Markdown allowed (bold, short lists).")
    show_product_ids: list[str] = Field(
        default_factory=list,
        max_length=8,
        description=(
            "product_ids (from tool results only) that the website should render as product cards under the reply. "
            "Empty when no cards are relevant."
        ),
    )


@dataclass
class ShopDeps:
    """Per-request dependencies injected into every tool via RunContext.deps."""

    customer: CustomerProfile
    page: PageContext | None
    run_id: str
    tool_calls: list[str] = field(default_factory=list)


# ---------------------------------------------------------------------------
# HTTP request / response bodies
# ---------------------------------------------------------------------------


class ChatTurn(BaseModel):
    role: Literal["user", "assistant"]
    content: str = Field(max_length=4000)
    products: list[ProductCard] = Field(default_factory=list)
    created_at: str | None = None


class ChatRequest(BaseModel):
    message: str = Field(min_length=1, max_length=1000)
    page: PageContext | None = None
    history: list[ChatTurn] = Field(
        default_factory=list,
        max_length=40,
        description="Guest-only: recent turns kept in the browser. Ignored for logged-in users (DB history is used).",
    )


class ChatResponse(BaseModel):
    reply: str
    products: list[ProductCard]
    saved: bool = Field(description="True when the turn was written to chat_messages (logged-in users only).")


class SignupRequest(BaseModel):
    first_name: str = Field(min_length=1, max_length=60)
    last_name: str = Field(min_length=1, max_length=60)
    email: str = Field(min_length=3, max_length=254)
    password: str = Field(min_length=8, max_length=200)


class LoginRequest(BaseModel):
    email: str = Field(max_length=254)
    password: str = Field(max_length=200)


class UserPublic(BaseModel):
    id: int
    first_name: str
    last_name: str
    email: str
    created_at: str


class AuthResponse(BaseModel):
    token: str
    user: UserPublic
