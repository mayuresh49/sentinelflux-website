"""Performance testing engagement lifecycle — per-product storage under data/perf/<product>/."""
from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone
from pathlib import Path

from filelock import FileLock

_ROOT = Path(__file__).resolve().parent.parent
_PERF_DIR = _ROOT / "data" / "perf"


class PerfManager:
    def __init__(self, data_dir: Path = _PERF_DIR):
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

    def create(self, product: str, name: str, target_url: str, created_by: str) -> dict:
        eng_id = f"perf-{uuid.uuid4().hex[:12]}"
        eng = {
            "id": eng_id,
            "product": product,
            "name": name,
            "target_url": target_url,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "created_by": created_by,
            "profiles": [],
            "runs": [],
        }
        self._save(product, eng_id, eng)
        return eng

    def get(self, product: str, eng_id: str) -> dict | None:
        return self._load(product, eng_id)

    def list_engagements(self, product: str) -> list[dict]:
        d = self._product_dir(product)
        result = []
        for f in sorted(d.glob("perf-*.json"), key=lambda p: p.stat().st_mtime, reverse=True):
            try:
                result.append(json.loads(f.read_text(encoding="utf-8")))
            except Exception:
                pass
        return result

    def delete(self, product: str, eng_id: str) -> bool:
        path = self._eng_path(product, eng_id)
        if path.exists():
            path.unlink()
            lk = Path(str(path) + ".lock")
            if lk.exists():
                lk.unlink()
            return True
        return False

    def upsert_profile(self, product: str, eng_id: str, profile: dict) -> dict | None:
        eng = self._load(product, eng_id)
        if eng is None:
            return None
        pid = profile.get("profile_id")
        if pid:
            for i, p in enumerate(eng["profiles"]):
                if p["profile_id"] == pid:
                    eng["profiles"][i] = profile
                    break
            else:
                eng["profiles"].append(profile)
        else:
            profile["profile_id"] = f"prof-{uuid.uuid4().hex[:10]}"
            eng["profiles"].append(profile)
        self._save(product, eng_id, eng)
        return eng

    def delete_profile(self, product: str, eng_id: str, profile_id: str) -> dict | None:
        eng = self._load(product, eng_id)
        if eng is None:
            return None
        eng["profiles"] = [p for p in eng["profiles"] if p["profile_id"] != profile_id]
        self._save(product, eng_id, eng)
        return eng

    def add_run(self, product: str, eng_id: str, profile_id: str, triggered_by: str) -> dict | None:
        eng = self._load(product, eng_id)
        if eng is None:
            return None
        run = {
            "run_id": f"run-{uuid.uuid4().hex[:12]}",
            "profile_id": profile_id,
            "triggered_by": triggered_by,
            "triggered_at": datetime.now(timezone.utc).isoformat(),
            "status": "queued",
            "finished_at": None,
            "metrics": None,
            "error": None,
        }
        eng["runs"].append(run)
        self._save(product, eng_id, eng)
        return run

    def patch_run(self, product: str, eng_id: str, run_id: str, **fields) -> None:
        eng = self._load(product, eng_id)
        if eng is None:
            return
        for r in eng["runs"]:
            if r["run_id"] == run_id:
                r.update(fields)
                break
        self._save(product, eng_id, eng)

    def delete_run(self, product: str, eng_id: str, run_id: str) -> bool:
        eng = self._load(product, eng_id)
        if eng is None:
            return False
        before = len(eng["runs"])
        eng["runs"] = [r for r in eng["runs"] if r["run_id"] != run_id]
        if len(eng["runs"]) == before:
            return False
        self._save(product, eng_id, eng)
        return True
