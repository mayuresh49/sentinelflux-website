"""Accessibility testing lifecycle — per-product storage under data/a11y/<product>/."""
from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone
from pathlib import Path

from filelock import FileLock

_ROOT = Path(__file__).resolve().parent.parent
_A11Y_DIR = _ROOT / "data" / "a11y"


class A11yManager:
    def __init__(self, data_dir: Path = _A11Y_DIR):
        self._dir = data_dir

    def _product_dir(self, product: str) -> Path:
        d = self._dir / product
        d.mkdir(parents=True, exist_ok=True)
        return d

    def _eng_path(self, product: str, eng_id: str) -> Path:
        return self._product_dir(product) / f"{eng_id}.json"

    def _load(self, product: str, eng_id: str) -> dict | None:
        p = self._eng_path(product, eng_id)
        if not p.exists():
            return None
        try:
            return json.loads(p.read_text(encoding="utf-8"))
        except Exception:
            return None

    def _save(self, product: str, eng_id: str, data: dict) -> None:
        path = self._eng_path(product, eng_id)
        lock = FileLock(str(path) + ".lock")
        with lock:
            path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")

    def create(self, product: str, name: str, base_url: str,
               pages: list[str], created_by: str) -> dict:
        eng_id = f"a11y-{uuid.uuid4().hex[:12]}"
        eng = {
            "id": eng_id,
            "product": product,
            "name": name,
            "base_url": base_url,
            "pages": pages or ["/"],
            "wcag_level": "AA",
            "created_at": datetime.now(timezone.utc).isoformat(),
            "created_by": created_by,
            "scans": [],
        }
        self._save(product, eng_id, eng)
        return eng

    def get(self, product: str, eng_id: str) -> dict | None:
        return self._load(product, eng_id)

    def list_engagements(self, product: str) -> list[dict]:
        d = self._product_dir(product)
        result = []
        for f in sorted(d.glob("a11y-*.json"), key=lambda p: p.stat().st_mtime, reverse=True):
            try:
                result.append(json.loads(f.read_text(encoding="utf-8")))
            except Exception:
                pass
        return result

    def patch(self, product: str, eng_id: str, **fields) -> dict | None:
        eng = self._load(product, eng_id)
        if eng is None:
            return None
        eng.update(fields)
        self._save(product, eng_id, eng)
        return eng

    def delete(self, product: str, eng_id: str) -> bool:
        path = self._eng_path(product, eng_id)
        if path.exists():
            path.unlink()
            lk = Path(str(path) + ".lock")
            if lk.exists():
                lk.unlink()
            return True
        return False

    def add_scan(self, product: str, eng_id: str, triggered_by: str) -> dict | None:
        eng = self._load(product, eng_id)
        if eng is None:
            return None
        scan = {
            "scan_id": f"scan-{uuid.uuid4().hex[:12]}",
            "triggered_by": triggered_by,
            "triggered_at": datetime.now(timezone.utc).isoformat(),
            "status": "queued",
            "finished_at": None,
            "wcag_level": eng.get("wcag_level", "AA"),
            "total_violations": 0,
            "violations_by_impact": {"critical": 0, "serious": 0, "moderate": 0, "minor": 0},
            "pages_results": [],
            "error": None,
        }
        eng["scans"].append(scan)
        self._save(product, eng_id, eng)
        return scan

    def patch_scan(self, product: str, eng_id: str, scan_id: str, **fields) -> None:
        eng = self._load(product, eng_id)
        if eng is None:
            return
        for s in eng["scans"]:
            if s["scan_id"] == scan_id:
                s.update(fields)
                break
        self._save(product, eng_id, eng)

    def delete_scan(self, product: str, eng_id: str, scan_id: str) -> bool:
        eng = self._load(product, eng_id)
        if eng is None:
            return False
        before = len(eng["scans"])
        eng["scans"] = [s for s in eng["scans"] if s["scan_id"] != scan_id]
        if len(eng["scans"]) == before:
            return False
        self._save(product, eng_id, eng)
        return True
