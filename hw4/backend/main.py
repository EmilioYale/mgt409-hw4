"""Campus Customs API. Run from backend/:  uvicorn main:app --reload --port 8000

Routes
  GET    /api/health
  GET    /api/products              catalogue cards (+ category for filtering)
  GET    /api/products/{id}         one product with per-size stock
  GET    /media/products/{file}     product images (static, from data/products/)
  POST   /api/auth/signup           create account  -> token
  POST   /api/auth/login            log in          -> token
  GET    /api/auth/me               current user (Bearer token)
  POST   /api/auth/logout
  POST   /api/chat                  one chat turn with the agent
  GET    /api/chat/history          saved chat (logged-in users)
  DELETE /api/chat/history          clear saved chat (logged-in users)
"""

from __future__ import annotations

import hashlib
import hmac
import json
import logging
import re
import secrets
import time
from collections import defaultdict, deque

from fastapi import Depends, FastAPI, Header, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

import agent as shop_agent
import tools
from models import (
    AuthResponse,
    ChatRequest,
    ChatResponse,
    ChatTurn,
    CustomerProfile,
    LoginRequest,
    ProductCard,
    ProductDetail,
    ShopDeps,
    SignupRequest,
    UserPublic,
)

log = logging.getLogger("campus_customs")

app = FastAPI(title="Campus Customs API")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
)
app.mount("/media/products", StaticFiles(directory=tools.PRODUCTS_DIR), name="product-images")

# ---------------------------------------------------------------------------
# Startup: tables this app adds next to the seed tables
# ---------------------------------------------------------------------------


@app.on_event("startup")
def ensure_tables() -> None:
    with tools.connect() as conn:
        conn.execute(
            """CREATE TABLE IF NOT EXISTS sessions (
                   token_hash TEXT PRIMARY KEY,
                   user_id INTEGER NOT NULL,
                   created_at TEXT NOT NULL DEFAULT (datetime('now')),
                   expires_at TEXT NOT NULL,
                   FOREIGN KEY (user_id) REFERENCES users(id))"""
        )
        conn.execute(  # already in the seed DB; kept here so a fresh DB still works
            """CREATE TABLE IF NOT EXISTS chat_messages (
                   id INTEGER PRIMARY KEY AUTOINCREMENT,
                   user_id INTEGER NOT NULL,
                   role TEXT NOT NULL,
                   content TEXT NOT NULL,
                   products_json TEXT,
                   created_at TEXT NOT NULL DEFAULT (datetime('now')),
                   FOREIGN KEY (user_id) REFERENCES users(id))"""
        )
        conn.execute("CREATE INDEX IF NOT EXISTS idx_chat_user ON chat_messages(user_id, id)")


# ---------------------------------------------------------------------------
# Products
# ---------------------------------------------------------------------------


@app.get("/api/health")
def health() -> dict:
    return {"ok": True, "model": shop_agent.MODEL_NAME}


@app.get("/api/products")
def products() -> dict:
    cards = tools.list_products()
    return {
        "products": [{**c.model_dump(), "category": tools.category_of(c)} for c in cards],
        "categories": tools.categories(),
        "low_stock_threshold": tools.LOW_STOCK,
    }


@app.get("/api/products/{product_id}", response_model=ProductDetail)
def product(product_id: str) -> ProductDetail:
    detail = tools.get_product(product_id)
    if not detail:
        raise HTTPException(404, "Product not found")
    return detail


# ---------------------------------------------------------------------------
# Passwords and sessions
# ---------------------------------------------------------------------------

PBKDF2_ITERATIONS = 600_000  # new hashes (OWASP 2023 guidance for PBKDF2-SHA256)
LEGACY_ITERATIONS = 120_000  # seed DB format: pbkdf2_sha256$<salt>$<hex>
SESSION_DAYS = 7
EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


def hash_password(password: str) -> str:
    salt = secrets.token_hex(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode(), salt.encode(), PBKDF2_ITERATIONS).hex()
    return f"pbkdf2_sha256${PBKDF2_ITERATIONS}${salt}${digest}"


def verify_password(password: str, stored: str) -> bool:
    parts = stored.split("$")
    if len(parts) == 4:  # pbkdf2_sha256$iterations$salt$hex (this app)
        algo, iterations, salt, digest = parts[0], int(parts[1]), parts[2], parts[3]
    elif len(parts) == 3:  # pbkdf2_sha256$salt$hex (seed data)
        algo, iterations, salt, digest = parts[0], LEGACY_ITERATIONS, parts[1], parts[2]
    else:
        return False
    if algo != "pbkdf2_sha256":
        return False
    candidate = hashlib.pbkdf2_hmac("sha256", password.encode(), salt.encode(), iterations).hex()
    return hmac.compare_digest(candidate, digest)


def _token_hash(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()  # only the hash is stored, so a DB leak can't hijack sessions


def _user_public(row) -> UserPublic:
    first = row["first_name"] or (row["name"].split(" ", 1)[0] if row["name"] else "")
    last = row["last_name"] or (row["name"].split(" ", 1)[1] if row["name"] and " " in row["name"] else "")
    return UserPublic(id=row["id"], first_name=first, last_name=last, email=row["email"], created_at=row["created_at"])


def _new_session(conn, user_id: int) -> str:
    token = secrets.token_urlsafe(32)
    conn.execute(
        "INSERT INTO sessions (token_hash, user_id, expires_at) VALUES (?, ?, datetime('now', ?))",
        (_token_hash(token), user_id, f"+{SESSION_DAYS} days"),
    )
    return token


def current_user(authorization: str | None = Header(None)) -> UserPublic | None:
    """Optional auth: returns the user for a valid Bearer token, else None (guest)."""
    if not authorization or not authorization.lower().startswith("bearer "):
        return None
    token = authorization.split(" ", 1)[1].strip()
    with tools.connect() as conn:
        row = conn.execute(
            """SELECT u.* FROM sessions s JOIN users u ON u.id = s.user_id
               WHERE s.token_hash = ? AND s.expires_at > datetime('now')""",
            (_token_hash(token),),
        ).fetchone()
    return _user_public(row) if row else None


def require_user(user: UserPublic | None = Depends(current_user)) -> UserPublic:
    if not user:
        raise HTTPException(401, "Please log in")
    return user


@app.post("/api/auth/signup", response_model=AuthResponse)
def signup(body: SignupRequest) -> AuthResponse:
    email = body.email.strip().lower()
    if not EMAIL_RE.match(email):
        raise HTTPException(422, "Please enter a valid email address")
    first, last = body.first_name.strip(), body.last_name.strip()
    with tools.connect() as conn:
        if conn.execute("SELECT 1 FROM users WHERE lower(email) = ?", (email,)).fetchone():
            raise HTTPException(409, "An account with that email already exists")
        cur = conn.execute(
            "INSERT INTO users (name, email, password_hash, first_name, last_name) VALUES (?, ?, ?, ?, ?)",
            (f"{first} {last}", email, hash_password(body.password), first, last),
        )
        row = conn.execute("SELECT * FROM users WHERE id = ?", (cur.lastrowid,)).fetchone()
        token = _new_session(conn, row["id"])
    return AuthResponse(token=token, user=_user_public(row))


@app.post("/api/auth/login", response_model=AuthResponse)
def login(body: LoginRequest) -> AuthResponse:
    email = body.email.strip().lower()
    with tools.connect() as conn:
        row = conn.execute("SELECT * FROM users WHERE lower(email) = ?", (email,)).fetchone()
        if not row or not verify_password(body.password, row["password_hash"]):
            raise HTTPException(401, "Email or password is incorrect")  # same message either way: no account probing
        token = _new_session(conn, row["id"])
    return AuthResponse(token=token, user=_user_public(row))


@app.get("/api/auth/me", response_model=UserPublic)
def me(user: UserPublic = Depends(require_user)) -> UserPublic:
    return user


@app.post("/api/auth/logout")
def logout(authorization: str | None = Header(None)) -> dict:
    if authorization and authorization.lower().startswith("bearer "):
        with tools.connect() as conn:
            conn.execute("DELETE FROM sessions WHERE token_hash = ?", (_token_hash(authorization.split(" ", 1)[1]),))
    return {"ok": True}


# ---------------------------------------------------------------------------
# Chat
# ---------------------------------------------------------------------------

RATE_LIMIT_MESSAGES = 12  # per client, per window (usability improvement: cost & abuse guard)
RATE_LIMIT_WINDOW_S = 60
_recent: dict[str, deque[float]] = defaultdict(deque)


def _rate_limited(key: str) -> bool:
    now = time.monotonic()
    q = _recent[key]
    while q and now - q[0] > RATE_LIMIT_WINDOW_S:
        q.popleft()
    if len(q) >= RATE_LIMIT_MESSAGES:
        return True
    q.append(now)
    return False


def _cards_from_json(raw: str | None) -> list[ProductCard]:
    """Stored rows keep product ids; cards are re-hydrated so prices/stock are always current."""
    try:
        items = json.loads(raw or "[]")
    except json.JSONDecodeError:
        return []
    ids = [i["product_id"] if isinstance(i, dict) else str(i) for i in items if i]
    return tools.get_cards(ids)


def load_history(user_id: int, limit: int = 40) -> list[ChatTurn]:
    with tools.connect() as conn:
        rows = conn.execute(
            "SELECT role, content, products_json, created_at FROM chat_messages WHERE user_id = ? "
            "ORDER BY id DESC LIMIT ?",
            (user_id, limit),
        ).fetchall()
    return [
        ChatTurn(role=r["role"], content=r["content"], products=_cards_from_json(r["products_json"]), created_at=r["created_at"])
        for r in reversed(rows)
        if r["role"] in ("user", "assistant")
    ]


def save_turn(user_id: int, user_message: str, reply: str, cards: list[ProductCard]) -> None:
    products_json = json.dumps([{"product_id": c.product_id, "name": c.name} for c in cards]) if cards else None
    with tools.connect() as conn:
        conn.execute("INSERT INTO chat_messages (user_id, role, content) VALUES (?, 'user', ?)", (user_id, user_message))
        conn.execute(
            "INSERT INTO chat_messages (user_id, role, content, products_json) VALUES (?, 'assistant', ?, ?)",
            (user_id, reply, products_json),
        )


@app.get("/api/chat/history", response_model=list[ChatTurn])
def chat_history(user: UserPublic = Depends(require_user)) -> list[ChatTurn]:
    return load_history(user.id)


@app.delete("/api/chat/history")
def clear_history(user: UserPublic = Depends(require_user)) -> dict:
    with tools.connect() as conn:
        conn.execute("DELETE FROM chat_messages WHERE user_id = ?", (user.id,))
    return {"ok": True}


@app.post("/api/chat", response_model=ChatResponse)
async def chat(body: ChatRequest, request: Request, user: UserPublic | None = Depends(current_user)) -> ChatResponse:
    key = f"user:{user.id}" if user else f"ip:{request.client.host if request.client else 'unknown'}"
    if _rate_limited(key):
        raise HTTPException(429, "Whoa, that's a lot of messages! Give me a few seconds and try again.")

    message = body.message.strip()
    if user:
        customer = CustomerProfile(logged_in=True, first_name=user.first_name, last_name=user.last_name,
                                   email=user.email, member_since=user.created_at[:10])
        history = load_history(user.id, limit=shop_agent.HISTORY_TURNS)
    else:
        customer = CustomerProfile(logged_in=False)
        history = body.history  # guests: the browser sends its own recent turns; nothing is stored

    page = body.page
    if page and page.product_id:  # trust the DB, not the browser, for the product name
        detail = tools.get_product(page.product_id)
        page = page.model_copy(update={"product_name": detail.name if detail else None,
                                       "product_id": detail.product_id if detail else None})

    deps = ShopDeps(customer=customer, page=page, run_id=shop_agent.new_run_id())
    try:
        reply, cards = await shop_agent.run_chat(message, history, deps)
    except Exception:
        log.exception("chat failed")
        raise HTTPException(502, "The shop assistant is having trouble right now. Please try again in a moment.")

    if user:
        save_turn(user.id, message, reply, cards)
    return ChatResponse(reply=reply, products=cards, saved=bool(user))
