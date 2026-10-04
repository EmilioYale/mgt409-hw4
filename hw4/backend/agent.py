"""Campus Customs chat agent: model + system prompt + tools + audit trail.

main.py calls run_chat(); everything about how the agent is built and logged lives here.
"""

from __future__ import annotations

import json
import os
import threading
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path

from dotenv import load_dotenv
from openai import AsyncOpenAI
from pydantic_ai import Agent, RunContext
from pydantic_ai.exceptions import ModelHTTPError, UsageLimitExceeded
from pydantic_ai.messages import (
    ModelMessage,
    ModelRequest,
    ModelResponse,
    TextPart,
    ToolCallPart,
    ToolReturnPart,
    UserPromptPart,
)
from pydantic_ai.models.openai import OpenAIResponsesModel
from pydantic_ai.providers.openai import OpenAIProvider
from pydantic_ai.usage import UsageLimits

import tools
from models import AgentReply, ChatTurn, ProductCard, ShopDeps

BACKEND_DIR = Path(__file__).resolve().parent
ROOT = BACKEND_DIR.parent  # hw4/
PROMPT_PATH = BACKEND_DIR / "prompts" / "prompt.md"
AUDIT_PATH = ROOT / "output" / "audit_trail.json"

# .env in hw4/ wins; otherwise the nearest one in a parent folder (e.g. the course folder).
for folder in [ROOT, *ROOT.parents]:
    if (folder / ".env").exists():
        load_dotenv(folder / ".env")
        break

MODEL_NAME = os.getenv("OPENAI_MODEL", "gpt-5.6-luna")
REQUEST_LIMIT = 6  # max model round-trips per chat turn (loop limit)
TOOL_CALLS_LIMIT = 8  # max tool executions per chat turn
HISTORY_TURNS = 12  # most recent messages sent back to the model as context


def make_model() -> OpenAIResponsesModel:
    """OpenAI through Portkey if PORTKEY_API_KEY is set, otherwise straight to OpenAI with OPENAI_API_KEY."""
    portkey_key = os.getenv("PORTKEY_API_KEY")
    if portkey_key:
        client = AsyncOpenAI(api_key=portkey_key, base_url="https://api.portkey.ai/v1",
                             default_headers={"x-portkey-api-key": portkey_key})
    elif os.getenv("OPENAI_API_KEY"):
        client = AsyncOpenAI()
    else:
        raise RuntimeError("No API key found. Put PORTKEY_API_KEY (or OPENAI_API_KEY) in hw4/.env — see .env.example.")
    return OpenAIResponsesModel(MODEL_NAME, provider=OpenAIProvider(openai_client=client))


agent: Agent[ShopDeps, AgentReply] = Agent(
    deps_type=ShopDeps,
    output_type=AgentReply,
    tools=tools.TOOLS,
    retries=2,
)


@agent.instructions
def system_prompt() -> str:
    """prompts/prompt.md, re-read each turn so prompt edits apply without restarting Uvicorn."""
    return PROMPT_PATH.read_text(encoding="utf-8")


@agent.instructions
def context(ctx: RunContext[ShopDeps]) -> str:
    """Per-request context appended to the system prompt: who is chatting and which page they're on."""
    c = ctx.deps.customer
    who = (f"Logged-in customer: {c.first_name} {c.last_name} <{c.email}>, member since {c.member_since}."
           if c.logged_in else "The shopper is a guest (not logged in). Their chat is not saved.")
    page = ctx.deps.page
    if page and page.product_id:
        where = (f"They are on the product page for '{page.product_name or page.product_id}' "
                 f"(product_id: {page.product_id}). 'This' / 'it' means this product.")
    elif page:
        where = f"They are on the page {page.path}."
    else:
        where = "Page unknown."
    return f"## Context\n- {who}\n- {where}"


# ---------------------------------------------------------------------------
# Audit trail: output/audit_trail.json is a JSON array that only ever grows.
# ---------------------------------------------------------------------------

_audit_lock = threading.Lock()


def _clip(value, limit: int = 300) -> str:
    text = value if isinstance(value, str) else json.dumps(value, default=str)
    return text if len(text) <= limit else text[: limit - 1] + "…"


def _summarise_result(content) -> str:
    """Short, human-readable tool result for the audit log."""
    if hasattr(content, "model_dump"):
        data = content.model_dump()
        if "results" in data:  # SearchResults
            return _clip(f"{data['total_matches']} matches: " + ", ".join(r["product_id"] for r in data["results"]))
        if "summary" in data:  # StockCheck
            return _clip(data["summary"])
        if "alternatives" in data:
            return _clip("alternatives: " + ", ".join(a["card"]["product_id"] for a in data["alternatives"]))
        if "description" in data:  # ProductDetail
            return _clip(f"{data['name']} ${data['price']:.2f}, stock {data['total_stock']}")
        return _clip(data)
    return _clip(content)


def audit(entries: list[dict]) -> None:
    """Append entries to the JSON array without rewriting earlier ones (seek to the closing bracket)."""
    AUDIT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with _audit_lock:
        if not AUDIT_PATH.exists() or AUDIT_PATH.stat().st_size == 0:
            AUDIT_PATH.write_text("[\n]\n", encoding="utf-8")
        with AUDIT_PATH.open("r+b") as f:
            size = f.seek(0, os.SEEK_END)
            f.seek(max(0, size - 256))
            tail = f.read()
            close = size - len(tail) + tail.rfind(b"]")  # position of the array's closing bracket
            empty = tail[: tail.rfind(b"]")].rstrip().endswith(b"[")
            chunk = ",\n".join("  " + json.dumps(e, ensure_ascii=False) for e in entries).encode("utf-8")
            f.seek(close)
            f.truncate()  # only the closing "]" is removed; earlier entries are never touched
            f.write((b"" if empty else b",\n") + chunk + b"\n]\n")


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="milliseconds")


def _audit_run(deps: ShopDeps, message: str, new_messages: list[ModelMessage], stop_reason: str,
               output: AgentReply | None, usage, started: float, error: str | None = None) -> None:
    who = deps.customer.email if deps.customer.logged_in else "guest"
    entries = [{"time": _now(), "run_id": deps.run_id, "event": "run_start", "user": who, "model": MODEL_NAME,
                "page": deps.page.path if deps.page else None, "message": _clip(message, 200)}]
    finish_reason = None
    for msg in new_messages:
        if isinstance(msg, ModelResponse):
            finish_reason = msg.finish_reason or finish_reason
            for part in msg.parts:
                if isinstance(part, ToolCallPart) and part.tool_name != "final_result":
                    entries.append({"time": msg.timestamp.isoformat(timespec="milliseconds"), "run_id": deps.run_id,
                                    "event": "tool_call", "tool": part.tool_name, "args": _clip(part.args_as_dict())})
        elif isinstance(msg, ModelRequest):
            for part in msg.parts:
                if isinstance(part, ToolReturnPart) and part.tool_name != "final_result":
                    entries.append({"time": part.timestamp.isoformat(timespec="milliseconds"), "run_id": deps.run_id,
                                    "event": "tool_result", "tool": part.tool_name,
                                    "result": _summarise_result(part.content)})
    end = {"time": _now(), "run_id": deps.run_id, "event": "run_end", "stop_reason": stop_reason,
           "finish_reason": finish_reason, "duration_s": round(time.perf_counter() - started, 2)}
    if usage is not None:
        end["usage"] = {"requests": usage.requests, "tool_calls": usage.tool_calls,
                        "input_tokens": usage.input_tokens, "output_tokens": usage.output_tokens}
    if output is not None:
        end["shown_products"] = output.show_product_ids
        end["reply"] = _clip(output.message, 200)
    if error:
        end["error"] = _clip(error, 300)
    entries.append(end)
    audit(entries)


# ---------------------------------------------------------------------------
# Running one chat turn
# ---------------------------------------------------------------------------


def history_to_messages(turns: list[ChatTurn]) -> list[ModelMessage]:
    """Rebuild PydanticAI message history from stored chat turns (DB rows or the guest's browser copy)."""
    messages: list[ModelMessage] = []
    for turn in turns[-HISTORY_TURNS:]:
        if turn.role == "user":
            messages.append(ModelRequest(parts=[UserPromptPart(content=turn.content)]))
        else:
            text = turn.content
            if turn.products:
                text += "\n[Cards shown: " + ", ".join(p.product_id for p in turn.products) + "]"
            messages.append(ModelResponse(parts=[TextPart(content=text)]))
    return messages


async def run_chat(message: str, history: list[ChatTurn], deps: ShopDeps) -> tuple[str, list[ProductCard]]:
    """Run one agent turn and return (reply text, product cards hydrated from the DB)."""
    started = time.perf_counter()
    limits = UsageLimits(request_limit=REQUEST_LIMIT, tool_calls_limit=TOOL_CALLS_LIMIT)
    try:
        result = await agent.run(message, deps=deps, model=make_model(),
                                 message_history=history_to_messages(history), usage_limits=limits)
    except UsageLimitExceeded as exc:
        _audit_run(deps, message, [], "usage_limit", None, None, started, error=str(exc))
        return ("Sorry, that one took me too many steps. Could you ask in a simpler way, "
                "e.g. one product or one size at a time?", [])
    except ModelHTTPError as exc:
        if "content_filter" not in str(exc.body):
            _audit_run(deps, message, [], "error", None, None, started, error=f"ModelHTTPError: {exc}")
            raise
        # The provider's safety filter blocked the prompt (e.g. a jailbreak attempt): answer in scope, don't crash.
        _audit_run(deps, message, [], "content_filter", None, None, started, error="blocked by provider content filter")
        return ("I can't help with that, but I'm happy to help you find some Yale gear! "
                "Try asking about hoodies, sizes or prices.", [])
    except Exception as exc:  # model/network errors: log and give the shopper a friendly message
        _audit_run(deps, message, [], "error", None, None, started, error=f"{type(exc).__name__}: {exc}")
        raise
    reply: AgentReply = result.output
    # Cards are re-read from the DB by id, so price/stock on the page can never be model-invented;
    # unknown ids are dropped.
    cards = tools.get_cards(reply.show_product_ids[:8])
    _audit_run(deps, message, result.new_messages(), "final_result", reply, result.usage, started)
    return reply.message, cards


def new_run_id() -> str:
    return uuid.uuid4().hex[:12]
