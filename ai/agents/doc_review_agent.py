"""DocReviewAgent — post-generation quality gate for test case documents.

Scans generated markdown docs for structural failures and rewrites thin TCs:
  - Batched headings (e.g. "### OH-WEB-036 to OH-WEB-043") — the LLM hit token limit
    and collapsed several TCs into one placeholder heading
  - Missing mandatory sections (Pre-conditions, Steps, Expected Result)
  - Thin steps — fewer than 3 numbered items
  - One-liner test cases with no real body

Run after DocGenAgent or standalone against an existing doc file.
Uses Haiku-class models for cost efficiency (each TC rewrite is a focused prompt).
"""
from __future__ import annotations

import re
from pathlib import Path

from ai.agents.base_agent import BaseAgent


# ── Section-presence patterns ─────────────────────────────────────────────────
_HEADING_RE = re.compile(r"^(#{1,4})\s+(.+)$", re.MULTILINE)
_RANGE_RE = re.compile(r"to\s+[A-Z]+-\w+-\d+", re.IGNORECASE)
_PRECOND_RE = re.compile(r"\*\*Pre-conditions", re.IGNORECASE)
_STEPS_RE = re.compile(r"\*\*Steps", re.IGNORECASE)
_EXPECTED_RE = re.compile(r"\*\*Expected Result", re.IGNORECASE)
_NUMBERED_STEP_RE = re.compile(r"^\d+\.\s+\S", re.MULTILINE)

_TC_HEADING_RE = re.compile(
    r"^#{2,4}\s+([A-Z][\w]+-[A-Z]+-\d+(?:\s+to\s+[A-Z][\w]+-[A-Z]+-\d+)?)\s+[—–-]\s+(.+)$",
    re.MULTILINE,
)

_REWRITE_PROMPT = """\
A test case in a generated document is incomplete or structurally thin.
Rewrite it so it fully meets the required format.

Feature/Form context from Knowledge Base:
{kb_context}

TC ID and current content:
{tc_block}

Rewrite the test case using EXACTLY this structure — no other text, no preamble:

### {tc_id} — {tc_title}
**Pre-conditions:**
- (user role, starting URL, required data state — minimum 1 item each)
**Test Data:**
| Field | Value |
|---|---|
| FieldName | exact value from KB |
**Steps:**
1. (specific navigation or setup action)
2. (specific user action with exact input values)
3. (assertion or verification action — add more steps as needed)
**Expected Result:** (explicit outcome — what the user sees, what message appears, what persists)
**Validation:** (specific assertions to verify correctness)
**Category:** {category}
**Status:** not_automated

Return ONLY the rewritten test case block — no markdown fences, no explanation.
"""


class DocReviewAgent(BaseAgent):
    """
    Validates a generated test case document and rewrites any thin or malformed TCs.

    run() accepts:
      doc_path: Path   — the markdown file to review and optionally fix
      fix: bool        — if True, rewrite thin TCs in-place (default True)
      kb_context: str  — pre-built KB context string for rewrite prompts

    Returns a dict with keys:
      issues: list[dict]  — each issue: {tc_id, type, description}
      fixed:  list[str]   — TC IDs that were rewritten
      doc_path: Path
    """
    name = "doc_review"

    def run(self, *, doc_path: Path, fix: bool = True, kb_context: str = "") -> dict:
        doc_path = Path(doc_path)
        if not doc_path.exists():
            return {"issues": [], "fixed": [], "doc_path": doc_path}

        content = doc_path.read_text(encoding="utf-8")
        issues, tc_blocks = self._audit(content)

        if not fix or not issues or not self.client:
            return {"issues": issues, "fixed": [], "doc_path": doc_path}

        # Rewrite only the TCs that have issues
        needs_fix = {i["tc_id"] for i in issues}
        fixed: list[str] = []
        new_content = content

        for tc_id, title, body, category in tc_blocks:
            if tc_id not in needs_fix:
                continue
            rewritten = self._rewrite_tc(tc_id, title, body, category, kb_context)
            if rewritten:
                original_block = body
                new_content = new_content.replace(original_block, rewritten, 1)
                fixed.append(tc_id)

        if fixed:
            doc_path.write_text(new_content, encoding="utf-8")
            self._log.info("DocReview: rewrote %d TCs in %s", len(fixed), doc_path)

        return {"issues": issues, "fixed": fixed, "doc_path": doc_path}

    # ── auditing ──────────────────────────────────────────────────────────────

    def _audit(self, content: str) -> tuple[list[dict], list[tuple]]:
        """Return (issues, tc_blocks). tc_blocks: [(tc_id, title, full_block, category)]."""
        issues: list[dict] = []
        tc_blocks: list[tuple] = []

        # Split doc into per-TC sections
        splits = list(_TC_HEADING_RE.finditer(content))
        for i, match in enumerate(splits):
            tc_id_raw = match.group(1).strip()
            title = match.group(2).strip()
            start = match.start()
            end = splits[i + 1].start() if i + 1 < len(splits) else len(content)
            block = content[start:end]

            # Detect batched heading (range)
            if _RANGE_RE.search(tc_id_raw):
                issues.append({
                    "tc_id": tc_id_raw,
                    "type": "batched_heading",
                    "description": f"TC range '{tc_id_raw}' collapsed into one heading — each TC needs its own section",
                })
                # Extract base ID for rewrite
                base_id = tc_id_raw.split(" to ")[0].strip() if " to " in tc_id_raw.lower() else tc_id_raw
                category = self._extract_category(block)
                tc_blocks.append((base_id, title, block, category))
                continue

            tc_id = tc_id_raw
            category = self._extract_category(block)
            tc_blocks.append((tc_id, title, block, category))

            # Check for missing mandatory sections
            if not _PRECOND_RE.search(block):
                issues.append({"tc_id": tc_id, "type": "missing_preconditions",
                               "description": "Missing **Pre-conditions** section"})
            if not _STEPS_RE.search(block):
                issues.append({"tc_id": tc_id, "type": "missing_steps",
                               "description": "Missing **Steps** section"})
            elif len(_NUMBERED_STEP_RE.findall(block)) < 3:
                issues.append({"tc_id": tc_id, "type": "thin_steps",
                               "description": f"Only {len(_NUMBERED_STEP_RE.findall(block))} step(s) — minimum 3 required"})
            if not _EXPECTED_RE.search(block):
                issues.append({"tc_id": tc_id, "type": "missing_expected_result",
                               "description": "Missing **Expected Result** section"})

        return issues, tc_blocks

    def _extract_category(self, block: str) -> str:
        m = re.search(r"\*\*Category:\*\*\s*(\w+)", block, re.IGNORECASE)
        return m.group(1) if m else "positive"

    # ── rewriting ─────────────────────────────────────────────────────────────

    def _rewrite_tc(
        self, tc_id: str, title: str, block: str, category: str, kb_context: str
    ) -> str | None:
        if not self.client:
            return None
        prompt = _REWRITE_PROMPT.format(
            kb_context=kb_context or "(No KB context provided — infer from existing block content)",
            tc_block=block.strip(),
            tc_id=tc_id,
            tc_title=title,
            category=category,
        )
        try:
            result = self.client.generate(prompt, max_tokens=1500, temperature=0.1).strip()
            # Sanity check: result must start with a heading containing tc_id
            if tc_id.split(" to ")[0] in result:
                return result
            self._log.warning("DocReview: rewrite for %s didn't contain TC ID — skipping", tc_id)
            return None
        except Exception as exc:
            self._log.warning("DocReview: rewrite failed for %s: %s", tc_id, exc)
            return None
