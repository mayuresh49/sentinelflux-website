"""
Executes the follow-up action after a human approves or rejects an approval.

Called synchronously from the approve/reject HTMX endpoints so the result
can be shown immediately in the approval card.
"""
from __future__ import annotations

import json
import logging
from datetime import date
from pathlib import Path

from core.activity_log import ActivityLog
from core.db import get_conn
from utils.paths import ROOT as _ROOT_DIR

_log = logging.getLogger("sentinelflux.approval_dispatch")
_alog = ActivityLog()


_ACTION_VERBS = frozenset({
    "create", "get", "update", "delete", "patch", "list", "fetch",
    "add", "remove", "edit", "search", "validate", "verify", "check",
    "put", "post", "read", "write", "set", "reset", "refresh", "load",
})


def derive_feature(suggested_test_name: str) -> str:
    """Derive a KB feature name from a suggested test function name.

    test_create_booking → booking
    test_patch_booking  → booking
    test_login          → login
    """
    name = suggested_test_name.removeprefix("test_")
    parts = name.split("_")
    while parts and parts[0] in _ACTION_VERBS:
        parts = parts[1:]
    return "_".join(parts) or name


def dispatch(item: dict, decision: str) -> str:
    """
    Execute the follow-up action for a resolved approval.
    Returns a short human-readable summary of what was done (shown in the UI card).
    """
    atype = item.get("type", "")
    details = item.get("details") or {}

    try:
        if atype == "quarantine":
            return _apply_quarantine(item, details, decision)
        elif atype == "unquarantine":
            return _apply_unquarantine(item, details, decision)
        elif atype == "locator_heal":
            return _apply_locator_heal(item, details, decision)
        elif atype == "coverage_gap":
            return _acknowledge_coverage_gap(item, decision)
        elif atype in ("regression_review", "script_review"):
            return _log_acknowledgement(item, decision)
    except Exception as exc:
        _log.error("Approval dispatch failed for %s/%s: %s", atype, decision, exc)
        return f"Action failed: {exc}"
    return ""


# ── quarantine ──────────────────────────────────────────────────────────────

def _apply_quarantine(item: dict, details: dict, decision: str) -> str:
    test_id = details.get("test_id", "")
    if not test_id:
        return "Missing test_id in quarantine details"

    conn = get_conn()
    # Remove from pending regardless of decision
    conn.execute("DELETE FROM quarantine_pending WHERE test_id = ?", (test_id,))

    if decision == "approved":
        conn.execute(
            """INSERT OR REPLACE INTO quarantine
               (test_id, domain, product, reason, quarantined_date, consecutive_passes)
               VALUES (?, ?, ?, ?, ?, 0)""",
            (
                test_id,
                item.get("domain", ""),
                item.get("product"),
                details.get("rule", "flaky"),
                str(date.today()),
            ),
        )
        conn.commit()
        _alog.append(
            event_type="approval_action", agent="quarantine_manager",
            domain=item.get("domain"), product=item.get("product"),
            status="success", summary=f"Quarantined: {test_id}",
        )
        return f"Quarantined — {test_id} marked xfail in next run"
    else:
        conn.commit()
        _alog.append(
            event_type="approval_action", agent="quarantine_manager",
            domain=item.get("domain"), product=item.get("product"),
            status="skipped", summary=f"Quarantine rejected: {test_id}",
        )
        return f"Proposal discarded — {test_id} stays active"


def _apply_unquarantine(item: dict, details: dict, decision: str) -> str:
    test_id = details.get("test_id", "")
    if not test_id:
        return "Missing test_id in unquarantine details"

    conn = get_conn()
    conn.execute("DELETE FROM quarantine_pending WHERE test_id = ?", (test_id,))

    if decision == "approved":
        conn.execute("DELETE FROM quarantine WHERE test_id = ?", (test_id,))
        conn.commit()
        _alog.append(
            event_type="approval_action", agent="quarantine_manager",
            domain=item.get("domain"), product=item.get("product"),
            status="success", summary=f"Unquarantined: {test_id}",
        )
        return f"Unquarantined — {test_id} re-enabled in next run"
    else:
        conn.commit()
        _alog.append(
            event_type="approval_action", agent="quarantine_manager",
            domain=item.get("domain"), product=item.get("product"),
            status="skipped", summary=f"Unquarantine rejected: {test_id}",
        )
        return f"Proposal discarded — {test_id} stays quarantined"


# ── locator heal ────────────────────────────────────────────────────────────

def _apply_locator_heal(item: dict, details: dict, decision: str) -> str:
    proposal = details.get("proposal", {})
    element_name = details.get("element_name") or proposal.get("element", "")
    new_primary = proposal.get("new_primary", "")
    alternatives = proposal.get("alternatives", [])
    old_selector = proposal.get("old_selector", "")
    locator_file_path = details.get("locator_file") or proposal.get("locator_file", "")
    already_applied = not proposal.get("dry_run", True)

    if not all([element_name, locator_file_path]):
        return "Locator heal: missing element_name or locator_file in payload"

    path = Path(locator_file_path)

    if decision == "approved":
        if already_applied:
            # Healer ran without dry_run — change is already on disk, just confirm
            _alog.append(
                event_type="approval_action", agent="locator_healer",
                domain=item.get("domain"), product=item.get("product"),
                status="success", summary=f"Locator heal confirmed: {element_name}",
            )
            return f"Confirmed — '{element_name}' already updated in {path.name}"
        else:
            # dry_run=True path: apply now
            if not path.exists():
                return f"Locator file not found: {locator_file_path}"
            try:
                locators = json.loads(path.read_text(encoding="utf-8"))
                locators[element_name] = {"primary": new_primary, "alternatives": alternatives}
                path.write_text(json.dumps(locators, indent=2), encoding="utf-8")
                _alog.append(
                    event_type="approval_action", agent="locator_healer",
                    domain=item.get("domain"), product=item.get("product"),
                    status="success",
                    summary=f"Healed locator '{element_name}': {old_selector} → {new_primary}",
                )
                return f"Applied — '{element_name}' → {new_primary} in {path.name}"
            except Exception as exc:
                _log.error("Locator heal write failed: %s", exc)
                return f"Write failed: {exc}"
    else:
        if already_applied and old_selector and path.exists():
            # Undo — restore old selector as primary
            try:
                locators = json.loads(path.read_text(encoding="utf-8"))
                existing = locators.get(element_name, {})
                locators[element_name] = {
                    "primary": old_selector,
                    "alternatives": existing.get("alternatives", []),
                }
                path.write_text(json.dumps(locators, indent=2), encoding="utf-8")
                _alog.append(
                    event_type="approval_action", agent="locator_healer",
                    domain=item.get("domain"), product=item.get("product"),
                    status="skipped",
                    summary=f"Locator heal reverted: {element_name} restored to {old_selector}",
                )
                return f"Reverted — '{element_name}' restored to original selector"
            except Exception as exc:
                _log.error("Locator heal revert failed: %s", exc)
                return f"Revert failed: {exc}"
        return f"Rejected — no changes made for '{element_name}'"


# ── coverage gap ────────────────────────────────────────────────────────────

def _acknowledge_coverage_gap(item: dict, decision: str) -> str:
    gaps = (item.get("details") or {}).get("gaps", [])
    if decision != "approved":
        _alog.append(
            event_type="approval_action", agent="human",
            domain=item.get("domain"), product=item.get("product"),
            status="skipped", summary=f"Coverage gap dismissed: {item.get('title', '')}",
        )
        return "Dismissed — no tests will be generated"

    suggested = [g.get("suggested_test_name", "") for g in gaps if g.get("suggested_test_name")]
    summary = (
        f"{len(gaps)} gap(s) queued for generation — trigger from KB page: "
        + ", ".join(suggested[:5])
        + (" …" if len(suggested) > 5 else "")
    ) if suggested else f"{len(gaps)} gap(s) acknowledged"
    _alog.append(
        event_type="approval_action", agent="human",
        domain=item.get("domain"), product=item.get("product"),
        status="pending", summary=summary,
        output={"gaps": suggested},
    )
    return summary


# ── acknowledgement-only types ──────────────────────────────────────────────

def _log_acknowledgement(item: dict, decision: str) -> str:
    labels = {
        "regression_review": "Regression",
        "coverage_gap": "Coverage gap",
        "script_review": "Script review",
    }
    label = labels.get(item.get("type", ""), item.get("type", ""))
    verb = "acknowledged" if decision == "approved" else "dismissed"
    summary = f"{label} {verb}: {item.get('title', '')}"
    _alog.append(
        event_type="approval_action", agent="human",
        domain=item.get("domain"), product=item.get("product"),
        status="success" if decision == "approved" else "skipped",
        summary=summary,
    )
    return summary


