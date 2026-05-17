"""VAPT engagement lifecycle management — per-product storage under data/vapt_findings/<product>/."""
from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone
from pathlib import Path

from filelock import FileLock

_ROOT = Path(__file__).resolve().parent.parent
_VAPT_DIR = _ROOT / "data" / "vapt_findings"


class VaptManager:
    def __init__(self, data_dir: Path = _VAPT_DIR):
        self._dir = data_dir

    # ── internal ──────────────────────────────────────────────────────────────

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

    # ── engagement CRUD ───────────────────────────────────────────────────────

    def create(self, product: str, name: str, client_name: str,
               created_by: str, assessor_org: str = "SentinelFlux") -> dict:
        eng_id = f"eng-{uuid.uuid4().hex[:12]}"
        eng = {
            "id": eng_id,
            "product": product,
            "name": name,
            "client_name": client_name,
            "assessor_org": assessor_org,
            "status": "scoping",
            "created_at": datetime.now(timezone.utc).isoformat(),
            "created_by": created_by,
            "scope": {
                "objectives": "",
                "methodology": "OWASP WSTG v4.2 / OWASP API Security Top 10 2023",
                "test_types": [],
                "owasp_categories": [],
                "in_scope": [],
                "out_of_scope": [],
                "environment": "",
                "start_date": "",
                "end_date": "",
                "finalized_at": None,
            },
            "scans": [],
            "findings": [],
            "report_generated_at": None,
            "certificate_threshold": {"Critical": 0, "High": 0},
            "certificate_issued_at": None,
            "certificate_id": None,
            "certificate_issued_by": None,
        }
        self._save(product, eng_id, eng)
        return eng

    def get(self, product: str, eng_id: str) -> dict | None:
        return self._load(product, eng_id)

    def list_engagements(self, product: str) -> list[dict]:
        d = self._product_dir(product)
        result = []
        for f in sorted(d.glob("eng-*.json"), key=lambda p: p.stat().st_mtime, reverse=True):
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

    # ── scope ─────────────────────────────────────────────────────────────────

    def update_scope(self, product: str, eng_id: str, scope: dict) -> dict | None:
        eng = self._load(product, eng_id)
        if eng is None:
            return None
        eng["scope"].update(scope)
        self._save(product, eng_id, eng)
        return eng

    def finalize_scope(self, product: str, eng_id: str) -> dict | None:
        eng = self._load(product, eng_id)
        if eng is None:
            return None
        eng["scope"]["finalized_at"] = datetime.now(timezone.utc).isoformat()
        if eng["status"] == "scoping":
            eng["status"] = "planned"
        self._save(product, eng_id, eng)
        return eng

    # ── scan lifecycle ────────────────────────────────────────────────────────

    def add_scan(self, product: str, eng_id: str, triggered_by: str,
                 is_revalidation: bool = False) -> dict | None:
        eng = self._load(product, eng_id)
        if eng is None:
            return None
        scan = {
            "scan_id": f"scan-{uuid.uuid4().hex[:12]}",
            "triggered_at": datetime.now(timezone.utc).isoformat(),
            "triggered_by": triggered_by,
            "status": "queued",
            "is_revalidation": is_revalidation,
            "total": 0,
            "passed": 0,
            "failed": 0,
            "skipped": 0,
            "duration": 0.0,
            "finished_at": None,
        }
        eng["scans"].append(scan)
        if eng["status"] in ("planned", "reported", "remediation"):
            eng["status"] = "in_progress"
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

    # ── findings ──────────────────────────────────────────────────────────────

    def upsert_findings(self, product: str, eng_id: str, scan_id: str,
                        scan_findings: list[dict], is_revalidation: bool = False) -> dict | None:
        eng = self._load(product, eng_id)
        if eng is None:
            return None

        by_test = {f["test_id"]: f for f in eng["findings"]}
        now = datetime.now(timezone.utc).isoformat()

        for sf in scan_findings:
            tid = sf["test_id"]
            if is_revalidation:
                if tid not in by_test:
                    continue
                ef = by_test[tid]
                if sf["status"] == "confirmed_secure" and ef["status"] in ("open", "still_open"):
                    ef.update(status="fixed", verified_fixed_at=now, revalidation_scan_id=scan_id)
                elif sf["status"] == "finding" and ef["status"] not in ("fixed", "accepted_risk", "false_positive"):
                    ef.update(status="still_open", revalidation_scan_id=scan_id)
            else:
                if sf["status"] != "finding":
                    continue
                if tid in by_test:
                    # Refresh evidence from latest scan
                    by_test[tid]["evidence"] = sf.get("evidence") or by_test[tid].get("evidence", "")
                    if sf.get("screenshot_path"):
                        by_test[tid]["screenshot_path"] = sf["screenshot_path"]
                else:
                    finding = {
                        "id": f"F-{len(eng['findings']) + 1:03d}",
                        "scan_id": scan_id,
                        "test_id": tid,
                        "title": sf["title"],
                        "owasp_ref": sf["owasp_ref"],
                        "owasp_category": sf["owasp_category"],
                        "severity": sf["severity"],
                        "status": "open",
                        "description": "",
                        "evidence": sf.get("evidence", ""),
                        "screenshot_path": sf.get("screenshot_path"),
                        "remediation": "",
                        "verified_fixed_at": None,
                        "revalidation_scan_id": None,
                        "created_at": now,
                    }
                    eng["findings"].append(finding)
                    by_test[tid] = finding

        self._save(product, eng_id, eng)
        return eng

    def patch_finding(self, product: str, eng_id: str, finding_id: str, **fields) -> dict | None:
        eng = self._load(product, eng_id)
        if eng is None:
            return None
        for f in eng["findings"]:
            if f["id"] == finding_id:
                f.update(fields)
                break
        self._save(product, eng_id, eng)
        return eng

    # ── certification ─────────────────────────────────────────────────────────

    def check_certifiable(self, product: str, eng_id: str) -> tuple[bool, str]:
        eng = self._load(product, eng_id)
        if eng is None:
            return False, "Engagement not found"
        if eng["status"] == "scoping":
            return False, "Scope has not been finalized"
        if not eng.get("findings"):
            return False, "No scans have been run yet"
        threshold = eng.get("certificate_threshold", {"Critical": 0, "High": 0})
        open_by_sev: dict[str, int] = {}
        for f in eng["findings"]:
            if f["status"] in ("open", "still_open"):
                open_by_sev[f["severity"]] = open_by_sev.get(f["severity"], 0) + 1
        for sev, limit in threshold.items():
            count = open_by_sev.get(sev, 0)
            if count > limit:
                return False, f"{count} open {sev} finding(s) exceed threshold of {limit}"
        return True, "All threshold criteria met"

    def issue_certificate(self, product: str, eng_id: str, issued_by: str) -> dict | None:
        can, _ = self.check_certifiable(product, eng_id)
        if not can:
            return None
        cert_id = f"SF-CERT-{uuid.uuid4().hex[:8].upper()}"
        return self.patch(product, eng_id,
                          status="certified",
                          certificate_id=cert_id,
                          certificate_issued_at=datetime.now(timezone.utc).isoformat(),
                          certificate_issued_by=issued_by)
