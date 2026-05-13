from __future__ import annotations

import json
import re
import uuid
from datetime import datetime, timezone
from pathlib import Path

import httpx
import yaml
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

router = APIRouter(prefix="/chat", tags=["chat"])

_CONFIG_FILE = Path(__file__).resolve().parent.parent / "chat_config.json"
_APPROVAL_FILE = Path(__file__).resolve().parent.parent.parent / "framework_knowledge" / "pending_approvals.yaml"

_SYSTEM_PROMPT = (
    "You are an AI assistant for the SentinelFlux test automation framework. "
    "You help QA engineers review and update test scripts, test documentation, "
    "Knowledge Base files, and agent configurations. "
    "When you want to suggest a concrete file change, end your response with a "
    "JSON block like:\n"
    "```json\n"
    '{\"action\": \"edit_file\", \"file\": \"<relative path>\", '
    '\"description\": \"<what to change>\", \"content\": \"<new content>\"}\n'
    "```\n"
    "This will be queued for human review before being applied. Keep responses concise and actionable."
)


def _load_config() -> dict:
    if not _CONFIG_FILE.exists():
        return {"provider": "ollama", "base_url": "http://localhost:11434", "model": "qwen2.5:14b", "api_key": ""}
    return json.loads(_CONFIG_FILE.read_text(encoding="utf-8"))


def _save_config(cfg: dict) -> None:
    _CONFIG_FILE.write_text(json.dumps(cfg, indent=2), encoding="utf-8")


class ChatMessage(BaseModel):
    role: str
    content: str


class ChatRequest(BaseModel):
    messages: list[ChatMessage]
    context: dict = {}


class ConfigUpdate(BaseModel):
    provider: str
    base_url: str
    model: str
    api_key: str = ""


async def _call_ollama(cfg: dict, messages: list[dict]) -> str:
    async with httpx.AsyncClient(timeout=120) as client:
        r = await client.post(
            f"{cfg['base_url'].rstrip('/')}/api/chat",
            json={"model": cfg["model"], "messages": messages, "stream": False},
        )
        r.raise_for_status()
        return r.json()["message"]["content"]


async def _call_openai_compat(cfg: dict, messages: list[dict]) -> str:
    async with httpx.AsyncClient(timeout=120) as client:
        r = await client.post(
            f"{cfg['base_url'].rstrip('/')}/v1/chat/completions",
            headers={"Authorization": f"Bearer {cfg['api_key']}"},
            json={"model": cfg["model"], "messages": messages},
        )
        r.raise_for_status()
        return r.json()["choices"][0]["message"]["content"]


async def _call_anthropic(cfg: dict, messages: list[dict]) -> str:
    system = next((m["content"] for m in messages if m["role"] == "system"), "")
    conv = [m for m in messages if m["role"] != "system"]
    async with httpx.AsyncClient(timeout=120) as client:
        r = await client.post(
            "https://api.anthropic.com/v1/messages",
            headers={"x-api-key": cfg["api_key"], "anthropic-version": "2023-06-01"},
            json={"model": cfg["model"], "max_tokens": 4096, "system": system, "messages": conv},
        )
        r.raise_for_status()
        return r.json()["content"][0]["text"]


async def _call_gemini(cfg: dict, messages: list[dict]) -> str:
    conv = [m for m in messages if m["role"] != "system"]
    contents = [
        {"role": "user" if m["role"] == "user" else "model", "parts": [{"text": m["content"]}]}
        for m in conv
    ]
    async with httpx.AsyncClient(timeout=120) as client:
        r = await client.post(
            f"https://generativelanguage.googleapis.com/v1beta/models/{cfg['model']}:generateContent",
            params={"key": cfg["api_key"]},
            json={"contents": contents},
        )
        r.raise_for_status()
        return r.json()["candidates"][0]["content"]["parts"][0]["text"]


def _extract_action(text: str) -> dict | None:
    match = re.search(r"```json\s*(\{.*?\})\s*```", text, re.DOTALL)
    if not match:
        return None
    try:
        data = json.loads(match.group(1))
        return data if "action" in data else None
    except json.JSONDecodeError:
        return None


def _queue_action(action: dict, context: dict) -> str:
    item_id = str(uuid.uuid4())[:8]
    item = {
        "id": item_id,
        "type": "chat_suggestion",
        "status": "pending",
        "proposed_date": datetime.now(timezone.utc).date().isoformat(),
        "title": action.get("description", action.get("action", "AI suggestion")),
        "detail": action,
        "product": context.get("product") or None,
        "domain": context.get("domain") or None,
    }
    data: dict = {"pending_actions": [], "quarantined": []}
    if _APPROVAL_FILE.exists():
        data = yaml.safe_load(_APPROVAL_FILE.read_text(encoding="utf-8")) or data
    data.setdefault("pending_actions", []).append(item)
    _APPROVAL_FILE.write_text(yaml.dump(data, default_flow_style=False, allow_unicode=True), encoding="utf-8")
    return item_id


@router.get("/config")
def get_config():
    cfg = _load_config()
    return {**cfg, "api_key": "***" if cfg.get("api_key") else ""}


@router.post("/config")
def save_config(body: ConfigUpdate):
    existing = _load_config()
    cfg = body.model_dump()
    if cfg["api_key"] == "***":
        cfg["api_key"] = existing.get("api_key", "")
    _save_config(cfg)
    return {"ok": True}


@router.post("/send")
async def send_message(body: ChatRequest):
    cfg = _load_config()
    messages = [{"role": "system", "content": _SYSTEM_PROMPT}]
    messages += [{"role": m.role, "content": m.content} for m in body.messages]

    try:
        provider = cfg.get("provider", "ollama")
        if provider == "ollama":
            reply = await _call_ollama(cfg, messages)
        elif provider in ("openai", "azure"):
            reply = await _call_openai_compat(cfg, messages)
        elif provider == "anthropic":
            reply = await _call_anthropic(cfg, messages)
        elif provider == "gemini":
            reply = await _call_gemini(cfg, messages)
        else:
            raise HTTPException(status_code=400, detail=f"Unknown provider: {provider}")
    except httpx.HTTPStatusError as e:
        raise HTTPException(status_code=502, detail=f"LLM error {e.response.status_code}: {e.response.text[:200]}")
    except httpx.RequestError as e:
        raise HTTPException(status_code=502, detail=f"LLM unreachable: {e}")

    action = _extract_action(reply)
    queued_id = _queue_action(action, body.context) if action else None
    return {"reply": reply, "queued_action_id": queued_id}
