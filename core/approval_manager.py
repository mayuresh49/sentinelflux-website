"""
ApprovalManager — unified human-in-the-loop gate for all agent proposals.

Extends the QuarantineManager.pending_actions pattern to all agent output types.

File: data/pending_approvals.yaml

Structure:
  pending:
    - id, type, product, domain, title, proposed_date, details
  resolved:
    - same fields + decision, resolved_date, resolved_by, notes
"""
from __future__ import annotations

import logging
import uuid
from datetime import date
from pathlib import Path
from typing import Any

import yaml
from filelock import FileLock

from utils.paths import ROOT as _ROOT_DIR

_log = logging.getLogger("sentinelflux.approval_manager")
_APPROVALS_PATH = _ROOT_DIR / "data" / "pending_approvals.yaml"

APPROVAL_TYPES = frozenset({
    "quarantine",
    "unquarantine",
    "locator_heal",
    "script_review",
    "coverage_gap",
    "regression_review",
})


class ApprovalManager:
    def __init__(self, path: Path = _APPROVALS_PATH):
        self._path = path

    def submit(
        self,
        *,
        approval_type: str,
        title: str,
        domain: str,
        product: str | None = None,
        details: dict[str, Any] | None = None,
    ) -> str:
        """Submit a new approval request. Returns the approval ID."""
        approval_id = str(uuid.uuid4())

        def _add(data: dict) -> None:
            data.setdefault("pending", []).append({
                "id": approval_id,
                "type": approval_type,
                "product": product,
                "domain": domain,
                "title": title,
                "proposed_date": str(date.today()),
                "details": details or {},
            })

        self._mutate(_add)
        _log.info("Approval submitted: %s [%s]", title, approval_id[:8])
        return approval_id

    def resolve(
        self,
        approval_id: str,
        *,
        decision: str,
        resolved_by: str = "human",
        notes: str = "",
    ) -> bool:
        """Approve or reject a pending approval. Returns True if found and resolved."""
        found: list[dict] = []

        def _resolve(data: dict) -> None:
            pending = data.get("pending", [])
            match = next((p for p in pending if p["id"] == approval_id), None)
            if not match:
                return
            found.append(match)
            data["pending"] = [p for p in pending if p["id"] != approval_id]
            data.setdefault("resolved", []).append({
                **match,
                "decision": decision,
                "resolved_date": str(date.today()),
                "resolved_by": resolved_by,
                "notes": notes,
            })

        self._mutate(_resolve)
        if not found:
            return False
        _log.info("Approval %s: %s [%s]", decision, found[0]["title"], approval_id[:8])
        return True

    def pending(self, approval_type: str | None = None) -> list[dict]:
        items = self._load().get("pending", [])
        if approval_type:
            items = [i for i in items if i["type"] == approval_type]
        return items

    def resolved(self, limit: int = 100) -> list[dict]:
        return self._load().get("resolved", [])[-limit:]

    def get(self, approval_id: str) -> dict | None:
        data = self._load()
        all_items = data.get("pending", []) + data.get("resolved", [])
        return next((i for i in all_items if i["id"] == approval_id), None)

    def _load(self) -> dict:
        """Read-only load — safe for query methods, not for write paths."""
        if not self._path.exists():
            return {"pending": [], "resolved": []}
        with self._path.open(encoding="utf-8") as f:
            return yaml.safe_load(f) or {"pending": [], "resolved": []}

    def _mutate(self, mutator) -> None:
        """Atomic read-modify-write under FileLock — use for all writes."""
        self._path.parent.mkdir(parents=True, exist_ok=True)
        with FileLock(str(self._path) + ".lock"):
            data = self._load()
            mutator(data)
            with self._path.open("w", encoding="utf-8") as f:
                yaml.dump(data, f, default_flow_style=False, sort_keys=False)
