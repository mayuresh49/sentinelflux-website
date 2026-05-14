"""JSON API for Knowledge Base file browsing, editing, and increment management."""
from __future__ import annotations

import html
import tempfile
from pathlib import Path

import yaml
from fastapi import APIRouter, File, Form, HTTPException, UploadFile
from pydantic import BaseModel

router = APIRouter(prefix="/kb", tags=["knowledge-base"])

_ROOT_DIR = Path(__file__).resolve().parent.parent.parent
_KB_DIR = _ROOT_DIR / "ai" / "knowledge_base"
_INCREMENTS_DIR = _KB_DIR / "increments"
_INCREMENTS_LOG = _ROOT_DIR / "framework_knowledge" / "kb_increments_log.yaml"

_SKIP_NAMES = {"__pycache__", "__init__.py", "auto_test_generator.py", "kb_loader.py"}
_TEXT_SUFFIXES = {".yaml", ".yml", ".md", ".txt"}


def _list_products() -> list[str]:
    """Return active products only. Falls back to KB dir scan if config has no products entry."""
    config_path = _ROOT_DIR / "framework_knowledge" / "config.yaml"
    if config_path.exists():
        import yaml as _yaml
        cfg = _yaml.safe_load(config_path.read_text(encoding="utf-8")) or {}
        products = cfg.get("products", [])
        if products:
            return sorted(p["name"] for p in products if p.get("active", True))
    if not _KB_DIR.exists():
        return []
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


_SAFE_NAME_RE = __import__("re").compile(r"^[a-zA-Z0-9_\-]+$")


@router.post("/upload-file")
async def upload_kb_file(
    file: UploadFile = File(...),
    product: str = Form(...),
    filename: str = Form(""),
):
    """Upload a YAML/MD/TXT file into ai/knowledge_base/<product>/."""
    product = product.strip()
    if not product or not _SAFE_NAME_RE.match(product):
        raise HTTPException(400, "Invalid product name (alphanumeric, _ and - only)")

    suffix = Path(file.filename or "").suffix.lower()
    if suffix not in _TEXT_SUFFIXES:
        raise HTTPException(400, f"Unsupported file type '{suffix}'. Use {sorted(_TEXT_SUFFIXES)}")

    raw = await file.read()
    if len(raw) > 5 * 1024 * 1024:
        raise HTTPException(413, "File too large (max 5 MB)")

    out_filename = filename.strip() or Path(file.filename).name
    if Path(out_filename).suffix.lower() not in _TEXT_SUFFIXES:
        out_filename += suffix

    product_dir = (_KB_DIR / product).resolve()
    if not str(product_dir).startswith(str(_KB_DIR)):
        raise HTTPException(400, "Invalid product path")

    product_dir.mkdir(parents=True, exist_ok=True)
    out_path = product_dir / out_filename
    out_path.write_bytes(raw)

    return {"status": "uploaded", "product": product, "filename": out_filename}


@router.post("/upload-docx")
async def upload_docx(
    file: UploadFile = File(...),
    output_filename: str = Form(""),
    local_url: str = Form("http://localhost:11434"),
    model: str = Form("mistral:7b-instruct-v0.3-q4_K_M"),
):
    """Accept a .docx upload, extract text, convert to KB YAML via LLM, save to increments/."""
    if not (file.filename or "").lower().endswith(".docx"):
        raise HTTPException(400, "Only .docx files are supported")

    raw = await file.read()
    if len(raw) > 20 * 1024 * 1024:
        raise HTTPException(413, "File too large (max 20 MB)")

    # Write to a temp file so python-docx can open it
    with tempfile.NamedTemporaryFile(suffix=".docx", delete=False) as tmp:
        tmp.write(raw)
        tmp_path = Path(tmp.name)

    try:
        from ai.skills.docx_converter import DocxConverter
        from utils.ai_factory import create_ai_client

        ai_client = create_ai_client({
            "enabled": True,
            "mode": "mistral",
            "local": True,
            "local_url": local_url,
            "model": model,
        })
        converter = DocxConverter(ai_client=ai_client)
        yaml_content = converter.convert_file(tmp_path)
    except Exception as exc:
        raise HTTPException(500, f"Conversion failed: {exc}") from exc
    finally:
        tmp_path.unlink(missing_ok=True)

    # Derive output filename from upload name if not supplied
    stem = Path(file.filename).stem.lower().replace(" ", "_").replace("-", "_")
    filename = output_filename.strip() or f"{stem}.yaml"
    if not filename.endswith((".yaml", ".yml")):
        filename += ".yaml"

    _INCREMENTS_DIR.mkdir(parents=True, exist_ok=True)
    out_path = _INCREMENTS_DIR / filename
    out_path.write_text(yaml_content, encoding="utf-8")

    return {"status": "converted", "filename": filename, "yaml": yaml_content}
