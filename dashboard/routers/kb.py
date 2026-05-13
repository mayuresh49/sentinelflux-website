"""JSON API for Knowledge Base file browsing, editing, and increment management."""
from __future__ import annotations

import html
from pathlib import Path

import yaml
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

router = APIRouter(prefix="/kb", tags=["knowledge-base"])

_ROOT_DIR = Path(__file__).resolve().parent.parent.parent
_KB_DIR = _ROOT_DIR / "ai" / "knowledge_base"
_INCREMENTS_DIR = _KB_DIR / "increments"
_INCREMENTS_LOG = _ROOT_DIR / "framework_knowledge" / "kb_increments_log.yaml"

_SKIP_NAMES = {"__pycache__", "__init__.py", "auto_test_generator.py", "kb_loader.py"}
_TEXT_SUFFIXES = {".yaml", ".yml", ".md", ".txt"}


def _list_products() -> list[str]:
    return sorted(
        d.name for d in _KB_DIR.iterdir()
        if d.is_dir() and d.name not in {"__pycache__", "increments"}
    )


def _kb_files(product: str) -> list[str]:
    d = _KB_DIR / product
    if not d.exists():
        return []
    return sorted(
        f.name for f in d.iterdir()
        if f.suffix in _TEXT_SUFFIXES and f.name not in _SKIP_NAMES
    )


def _load_increments_log() -> dict:
    if not _INCREMENTS_LOG.exists():
        return {}
    with _INCREMENTS_LOG.open(encoding="utf-8") as f:
        data = yaml.safe_load(f) or {}
    return {e["increment"]: e for e in data.get("processed", [])}


@router.get("/")
def list_kb():
    products = _list_products()
    return {
        "products": [{"product": p, "files": _kb_files(p)} for p in products]
    }


@router.get("/increments")
def list_increments():
    log = _load_increments_log()
    files: list[str] = []
    if _INCREMENTS_DIR.exists():
        files = sorted(
            f.name for f in _INCREMENTS_DIR.iterdir()
            if f.suffix in {".yaml", ".yml"} and f.name != ".gitkeep"
        )
    return {
        "increments": [
            {"filename": fn, "processed": fn in log, "log": log.get(fn)}
            for fn in files
        ]
    }


@router.get("/{product}/{filename}")
def get_file(product: str, filename: str):
    path = _KB_DIR / product / filename
    if not path.exists():
        raise HTTPException(404, "File not found")
    return {
        "product": product,
        "filename": filename,
        "content": path.read_text(encoding="utf-8"),
    }


class SaveBody(BaseModel):
    content: str


@router.put("/{product}/{filename}")
def save_file(product: str, filename: str, body: SaveBody):
    path = _KB_DIR / product / filename
    if not path.exists():
        raise HTTPException(404, "File not found")
    path.write_text(body.content, encoding="utf-8")
    return {"status": "saved"}


class IncrementBody(BaseModel):
    filename: str
    content: str


@router.post("/increments")
def create_increment(body: IncrementBody):
    if not body.filename.endswith((".yaml", ".yml")):
        raise HTTPException(400, "Filename must end with .yaml")
    _INCREMENTS_DIR.mkdir(parents=True, exist_ok=True)
    path = _INCREMENTS_DIR / body.filename
    path.write_text(body.content, encoding="utf-8")
    return {"status": "created", "filename": body.filename}
