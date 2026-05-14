from __future__ import annotations

import json
import os
import re
import subprocess
import uuid
from datetime import datetime, timezone
from pathlib import Path

import httpx
import yaml
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

router = APIRouter(prefix="/chat", tags=["chat"])

_FRAMEWORK_ROOT = Path(__file__).resolve().parent.parent.parent

# ── tool schemas ───────────────────────────────────────────────────────────────

_TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "list_directory",
            "description": "List files and sub-directories inside the SentinelFlux framework at a given path.",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {
                        "type": "string",
                        "description": (
                            "Path relative to the framework root (e.g. 'tests/api'). "
                            "Defaults to the framework root."
                        ),
                    }
                },
                "required": [],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "read_file",
            "description": "Read the text contents of a file inside the SentinelFlux framework.",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {
                        "type": "string",
                        "description": "Path relative to the framework root (e.g. 'tests/api/test_login.py').",
                    },
                    "max_lines": {
                        "type": "integer",
                        "description": "Maximum number of lines to return. Default 200.",
                    },
                },
                "required": ["path"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "list_tests",
            "description": (
                "Find all test script files (test_*.py / *_test.py) by scanning the filesystem. "
                "Optionally filter by a sub-path (e.g. 'tests/api' or 'examples/restfulbooker'). "
                "Use this to answer questions like 'what test scripts exist for product X'."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {
                        "type": "string",
                        "description": "Sub-path to scan (relative to framework root). Defaults to all.",
                    }
                },
                "required": [],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "run_shell",
            "description": (
                "Run a safe, read-only shell command inside the framework root and return its output. "
                "Destructive commands (rm, kill, sudo, mv, chmod, etc.) are blocked."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "command": {"type": "string", "description": "The shell command to run."}
                },
                "required": ["command"],
            },
        },
    },
]

_BLOCKED_COMMANDS = {
    "rm", "rmdir", "del", "format", "mkfs", "dd", "shred",
    "kill", "killall", "pkill", "shutdown", "reboot", "halt",
    "chmod", "chown", "sudo", "su", "passwd", "mv", "truncate", "wipe",
}

_TOOL_NAMES = {"list_directory", "read_file", "list_tests", "run_shell"}


# ── tool implementations ───────────────────────────────────────────────────────

def _tool_list_directory(path: str = "") -> str:
    target = (_FRAMEWORK_ROOT / path).resolve() if path else _FRAMEWORK_ROOT.resolve()
    if not str(target).startswith(str(_FRAMEWORK_ROOT)):
        return "Error: path is outside the framework root."
    try:
        entries = sorted(os.listdir(target))
        lines = [e + ("/" if (target / e).is_dir() else "") for e in entries if not e.startswith("__pycache__")]
        return "\n".join(lines) or "(empty)"
    except Exception as exc:
        return f"Error: {exc}"


def _tool_read_file(path: str, max_lines: int = 200) -> str:
    target = (_FRAMEWORK_ROOT / path).resolve()
    if not str(target).startswith(str(_FRAMEWORK_ROOT)):
        return "Error: path is outside the framework root."
    try:
        lines = []
        with open(target, "r", errors="replace") as f:
            for i, line in enumerate(f):
                if i >= max_lines:
                    lines.append(f"... (truncated after {max_lines} lines)")
                    break
                lines.append(line.rstrip())
        return "\n".join(lines)
    except Exception as exc:
        return f"Error: {exc}"


def _tool_list_tests(path: str = "") -> str:
    root = (_FRAMEWORK_ROOT / path).resolve() if path else _FRAMEWORK_ROOT.resolve()
    if not str(root).startswith(str(_FRAMEWORK_ROOT)):
        return "Error: path is outside the framework root."
    matches = []
    for dirpath, dirnames, filenames in os.walk(root):
        # skip hidden dirs and caches
        dirnames[:] = [d for d in dirnames if not d.startswith((".","__pycache__"))]
        for fname in sorted(filenames):
            if fname.startswith("test_") or fname.endswith("_test.py"):
                rel = os.path.relpath(os.path.join(dirpath, fname), _FRAMEWORK_ROOT)
                matches.append(rel)
    if not matches:
        return f"No test files found under '{path or '.'}'"
    return "\n".join(matches)


def _tool_run_shell(command: str) -> str:
    first = command.strip().split()[0].lstrip("./") if command.strip() else ""
    if first.lower() in _BLOCKED_COMMANDS:
        return f"Blocked: '{first}' is a destructive command and is not permitted."
    try:
        result = subprocess.run(
            command, shell=True, capture_output=True, text=True,
            timeout=15, cwd=str(_FRAMEWORK_ROOT),
        )
        output = (result.stdout + result.stderr)[:4000]
        return output or "(no output)"
    except subprocess.TimeoutExpired:
        return "Error: command timed out."
    except Exception as exc:
        return f"Error: {exc}"


_TOOL_REGISTRY = {
    "list_directory": _tool_list_directory,
    "read_file": _tool_read_file,
    "list_tests": _tool_list_tests,
    "run_shell": _tool_run_shell,
}


def _dispatch_tool(name: str, args: dict) -> str:
    fn = _TOOL_REGISTRY.get(name)
    if fn is None:
        return f"Unknown tool: {name}"
    try:
        return fn(**args)
    except Exception as exc:
        return f"Tool error: {exc}"


def _parse_embedded_tool_calls(content: str):
    """Fallback: some Qwen builds emit tool calls as raw JSON in content."""
    if not content:
        return None
    candidates = [content.strip()]
    for m in re.finditer(r"```(?:json)?\s*([\s\S]*?)```", content):
        candidates.append(m.group(1).strip())
    for candidate in candidates:
        try:
            obj = json.loads(candidate)
        except (json.JSONDecodeError, ValueError):
            continue
        if isinstance(obj, dict) and obj.get("name") in _TOOL_NAMES:
            return [{"name": obj["name"], "args": obj.get("arguments") or obj.get("args") or {}}]
        if isinstance(obj, list) and obj and isinstance(obj[0], dict) and obj[0].get("name") in _TOOL_NAMES:
            return [{"name": o["name"], "args": o.get("arguments") or o.get("args") or {}} for o in obj]
    return None

_CONFIG_FILE = Path(__file__).resolve().parent.parent / "chat_config.json"
_APPROVAL_FILE = Path(__file__).resolve().parent.parent.parent / "framework_knowledge" / "pending_approvals.yaml"

_SYSTEM_PROMPT = (
    "You are the SentinelFlux assistant. Answer the user's question directly using tools.\n\n"
    "RULES — follow all of them:\n"
    "1. Call a tool first. Never answer from memory when a tool can get the real data.\n"
    "2. Return the data. For 'what tests exist', list the files. For 'show me a file', show its contents. "
    "Do not explain what the user could do — just give them the answer.\n"
    "3. Never suggest fixes, renames, restructuring, or improvements unless the user's message "
    "contains words like 'fix', 'edit', 'change', 'update', 'rename', 'create', or 'modify'.\n"
    "4. If tool output contains errors or warnings, quote them verbatim and stop. Do not propose solutions.\n"
    "5. ONLY append a JSON action block when the user has explicitly asked you to edit or create a file. "
    "If the user asked a question or asked you to list something, do NOT include any JSON block.\n"
    "   Format (only when requested):\n"
    "   ```json\n"
    '   {\"action\": \"edit_file\", \"file\": \"<relative path>\", '
    '\"description\": \"<what to change>\", \"content\": \"<new content>\"}\n'
    "   ```\n"
    "Keep responses short. One sentence of context at most, then the data."
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
        while True:
            r = await client.post(
                f"{cfg['base_url'].rstrip('/')}/api/chat",
                json={"model": cfg["model"], "messages": messages, "tools": _TOOLS, "stream": False},
            )
            r.raise_for_status()
            msg = r.json()["message"]
            content = msg.get("content") or ""
            structured_calls = msg.get("tool_calls") or []

            # normalise: prefer structured tool_calls, fall back to embedded JSON
            tool_calls = []
            if structured_calls:
                for tc in structured_calls:
                    fn = tc.get("function", {})
                    args = fn.get("arguments") or {}
                    if isinstance(args, str):
                        try:
                            args = json.loads(args)
                        except json.JSONDecodeError:
                            args = {}
                    tool_calls.append({"name": fn.get("name", ""), "args": args})
            else:
                parsed = _parse_embedded_tool_calls(content)
                if parsed:
                    tool_calls = parsed
                    content = ""

            if not tool_calls:
                return content

            # append assistant turn with tool calls
            messages.append({
                "role": "assistant",
                "content": content,
                "tool_calls": [
                    {"function": {"name": tc["name"], "arguments": tc["args"]}}
                    for tc in tool_calls
                ],
            })

            # execute tools and feed results back
            for tc in tool_calls:
                result = _dispatch_tool(tc["name"], tc["args"])
                messages.append({"role": "tool", "content": result})


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
    _WRITE_ACTIONS = {"edit_file", "create_file", "write_file", "delete_file"}
    queued_id = _queue_action(action, body.context) if action and action.get("action") in _WRITE_ACTIONS else None
    return {"reply": reply or "", "queued_action_id": queued_id}
