"""
End-to-end pipeline: KB (base + increments) → test case doc → pytest script.

CLI usage:
    python -m ai.pipeline.orchestrator --feature booking --domain api
    python -m ai.pipeline.orchestrator --feature booking --domain web --env staging
    python -m ai.pipeline.orchestrator --increment feature_001_booking_v2.yaml --domain api
    python -m ai.pipeline.orchestrator --doc docs/test_cases/api/booking.md --domain api --feature booking
"""

from __future__ import annotations

import argparse
import logging
import sys
from datetime import date
from pathlib import Path

import yaml

from core.activity_log import ActivityLog
from utils.paths import ROOT as ROOT_DIR

_log = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")


def _find_highest_tc_id(docs_dir: Path, prefix: str) -> int:
    """Scan existing doc files and return the highest NNN found for the given prefix.

    Prevents ID conflicts: callers use this to compute tc_start = result + 1.
    Returns 0 if no IDs are found (so tc_start = 1).
    """
    import re
    pattern = re.compile(rf"\b{re.escape(prefix)}-(\d+)\b")
    highest = 0
    if docs_dir.exists():
        for md_file in docs_dir.glob("*.md"):
            try:
                text = md_file.read_text(encoding="utf-8", errors="ignore")
                for m in pattern.finditer(text):
                    highest = max(highest, int(m.group(1)))
            except OSError:
                pass
    return highest


def _extract_pages_from_doc(doc_text: str) -> list[str]:
    """
    Parse the reviewed test case doc for page paths mentioned in Pre-conditions blocks.

    Looks for patterns like "Starting URL: /path" or "Navigate to /path".
    Returns deduplicated list of relative paths (max 10) for the explorer to visit.
    """
    import re
    patterns = [
        r"(?:Starting\s+URL|Application\s+URL|URL)[:\s]+(/[^\s,\n\"']+)",
        r"Navigate\s+to\s+(?:the\s+)?(?:exact\s+URL\s+)?(/[^\s,\n\"']+)",
        r"Go\s+to\s+(/[^\s,\n\"']+)",
    ]
    seen: set[str] = set()
    pages: list[str] = []
    for pat in patterns:
        for m in re.finditer(pat, doc_text, re.IGNORECASE):
            path = m.group(1).rstrip(".,;)")
            if path not in seen:
                seen.add(path)
                pages.append(path)
    return pages[:10]


class TestPipelineOrchestrator:
    def __init__(self, ai_client, kb_loader=None):
        from ai.knowledge_base.kb_loader import KnowledgeBaseLoader
        self.ai_client = ai_client
        self._script_client = ai_client  # can be overridden to use a different model
        self.kb_loader = kb_loader or KnowledgeBaseLoader()
        self._alog = ActivityLog()

    def run(
        self,
        feature_name: str,
        domain: str,
        increment_file: str = None,
        skip_doc: bool = False,
        skip_script: bool = False,
        doc_path: Path = None,
        output_base: Path = None,
        tc_prefix: str = "",
        tc_start: int = 1,
        source: str = "",
        explore: bool = False,
        base_url: str = "",
        login_url: str = "",
        credentials: dict = None,
        explore_pages: list[str] = None,
    ) -> dict[str, Path]:
        """
        Full pipeline: doc gen → doc review → (optional explore) → script gen → script review.

        Exploration runs AFTER doc review so the finalized doc drives page discovery.
        If explore=True and explore_pages is empty, page URLs are extracted from the reviewed doc.

        explore=True    — run AppExplorerAgent after doc review; requires base_url.
        skip_doc=True   — reuse existing doc, only regenerate script.
        skip_script=True — regenerate doc only, never touch existing test script.

        Returns dict with keys 'doc' and 'script' (script may be None when skipped).
        """
        _log.info("Pipeline start — feature=%s domain=%s explore=%s", feature_name, domain, explore)
        product = str(output_base).split("products/")[-1].split("/")[0] if output_base and "products/" in str(output_base) else None

        try:
            if increment_file:
                self._load_increment(increment_file)

            if skip_doc and doc_path and doc_path.exists():
                _log.info("Skipping doc generation — using existing: %s", doc_path)
                out_doc = doc_path
            else:
                out_doc = self._generate_doc(
                    feature_name, domain, doc_path,
                    output_base=output_base, tc_prefix=tc_prefix, tc_start=tc_start,
                    source=source,
                )

            # Doc review runs before exploration so the finalized doc drives page discovery
            self._review_doc(out_doc, domain)
            test_case_doc = out_doc.read_text(encoding="utf-8")

            if skip_script:
                _log.info("Skipping script generation (--skip-script)")
                self._alog.append(
                    event_type="pipeline_run",
                    agent="pipeline",
                    product=product,
                    domain=domain,
                    status="success",
                    summary=f"Doc generated for {feature_name} (script skipped — hand-written exists)",
                    output={"feature": feature_name, "doc": str(out_doc.relative_to(ROOT_DIR)), "script": None},
                )
                return {"doc": out_doc, "script": None}

            # Exploration: runs AFTER doc review, BEFORE script gen.
            # The reviewed doc is the source of truth for which pages to visit.
            # If explore_pages not given, extract URLs from the finalized doc.
            exploration_context = ""
            if explore:
                pages_to_explore = explore_pages or _extract_pages_from_doc(test_case_doc)
                if pages_to_explore:
                    exploration_context = self._run_exploration(
                        base_url=base_url,
                        login_url=login_url,
                        credentials=credentials or {},
                        pages=pages_to_explore,
                        domain=domain,
                        product=product,
                        output_base=output_base,
                    )
                else:
                    _log.warning("Exploration skipped — no pages found in doc and --explore-pages not set")

            out_script = self._generate_script(
                test_case_doc, feature_name, domain, output_base=output_base, tc_prefix=tc_prefix,
                exploration_context=exploration_context,
            )
            self._normalize_script_fn_ids(out_script, out_doc, tc_prefix)
            self._review_script(out_script, domain)
            suspicious = self._validate_script_paths(out_script, domain)
            if suspicious:
                _log.warning(
                    "Path validation: %d path(s) in generated script not found in KB — "
                    "possible hallucinations: %s",
                    len(suspicious), suspicious,
                )

            if increment_file:
                self._log_increment(increment_file, feature_name, domain, out_doc, out_script)

            _log.info("Pipeline complete — doc=%s script=%s", out_doc, out_script)
            self._alog.append(
                event_type="pipeline_run",
                agent="pipeline",
                product=product,
                domain=domain,
                status="success",
                summary=f"Generated doc + script for {feature_name}",
                output={"feature": feature_name, "doc": str(out_doc.relative_to(ROOT_DIR)), "script": str(out_script.relative_to(ROOT_DIR))},
            )
            return {"doc": out_doc, "script": out_script}

        except Exception as exc:
            _log.error("Pipeline failed — feature=%s: %s", feature_name, exc)
            self._alog.append(
                event_type="pipeline_run",
                agent="pipeline",
                product=product,
                domain=domain,
                status="error",
                summary=f"Pipeline failed for {feature_name}: {exc}",
            )
            raise

    # --- steps ---

    def _run_exploration(
        self,
        base_url: str,
        login_url: str,
        credentials: dict,
        pages: list[str],
        domain: str,
        product: str | None,
        output_base: Path | None,
    ) -> str:
        """Run AppExplorerAgent — returns the combined exploration context string."""
        from ai.agents.app_explorer_agent import AppExplorerAgent
        from ai.agents.base_agent import AgentContext

        if not base_url or not pages:
            _log.warning("Exploration skipped — base_url or pages not provided")
            return ""

        ctx = AgentContext(domain=domain, product=product, output_base=output_base or ROOT_DIR)
        agent = AppExplorerAgent(context=ctx)
        self._alog.append(
            event_type="agent_run", agent="app_explorer",
            domain=domain, product=product, status="pending",
            summary=f"AppExplorer started — {len(pages)} page(s)",
        )
        try:
            result = agent.run(
                base_url=base_url,
                pages=pages,
                login_url=login_url,
                credentials=credentials or {},
            )
            if result.get("success"):
                _log.info(
                    "Exploration complete — %d page(s) explored",
                    result.get("pages_explored", 0),
                )
                self._alog.append(
                    event_type="agent_run", agent="app_explorer",
                    domain=domain, product=product, status="success",
                    summary=f"AppExplorer complete — {result.get('pages_explored', 0)} page(s) explored",
                )
                return result.get("exploration_context", "")
            self._alog.append(
                event_type="agent_run", agent="app_explorer",
                domain=domain, product=product, status="error",
                summary="AppExplorer returned no result",
            )
        except Exception as exc:
            _log.warning("Exploration failed (non-fatal) — continuing without it: %s", exc)
            self._alog.append(
                event_type="agent_run", agent="app_explorer",
                domain=domain, product=product, status="error",
                summary=f"AppExplorer failed: {exc}",
            )
        return ""

    def _generate_doc(
        self,
        feature_name: str,
        domain: str,
        out_path: Path = None,
        output_base: Path = None,
        tc_prefix: str = "",
        tc_start: int = 1,
        source: str = "",
    ) -> Path:
        from ai.agents import AgentContext, DocGenAgent

        product = str(output_base).split("products/")[-1].split("/")[0] if output_base and "products/" in str(output_base) else None
        self._alog.append(
            event_type="agent_run", agent="doc_gen",
            domain=domain, product=product, status="pending",
            summary=f"DocGen started — {feature_name}",
        )
        try:
            base = output_base if output_base else ROOT_DIR
            ctx = AgentContext(domain=domain, output_base=base).extend(
                tc_prefix=tc_prefix, tc_start=tc_start, source=source,
            )
            agent = DocGenAgent(ai_client=self.ai_client, kb_loader=self.kb_loader, context=ctx)
            result = agent.run(feature_name=feature_name, output_path=out_path)
            doc_path = result["doc_path"]
            self._clean_doc(doc_path)
            if tc_prefix:
                self._normalize_tc_ids(doc_path, tc_prefix, tc_start)
            self._alog.append(
                event_type="agent_run", agent="doc_gen",
                domain=domain, product=product, status="success",
                summary=f"DocGen complete — {doc_path.name}",
            )
            return doc_path
        except Exception as exc:
            self._alog.append(
                event_type="agent_run", agent="doc_gen",
                domain=domain, product=product, status="error",
                summary=f"DocGen failed: {exc}",
            )
            raise

    @staticmethod
    def _clean_doc(doc_path: Path) -> None:
        """Strip code-fence wrappers and normalize blank lines around TC section headers."""
        import re
        text = doc_path.read_text(encoding="utf-8")
        stripped = text.strip()

        # Remove leading/trailing markdown code fences
        if stripped.startswith("```"):
            lines = stripped.splitlines()
            if lines[0].startswith("```"):
                lines = lines[1:]
            if lines and lines[-1].strip() == "```":
                lines = lines[:-1]
            stripped = "\n".join(lines)

        # Ensure a blank line before every bold section header inside TC detail blocks.
        # Headers use the form **Pre-conditions:** where the colon is inside the bold markers.
        _TC_HEADERS = re.compile(
            r"(?<!\n\n)"
            r"(\*\*(?:Pre-conditions|Test Data|Request|Steps|Expected Result|Validation|Category|Status|Note)[^*]*\*\*)",
        )
        normalized = _TC_HEADERS.sub(r"\n\1", stripped)

        # Collapse any triple+ blank lines introduced by the above pass
        normalized = re.sub(r"\n{3,}", "\n\n", normalized)

        doc_path.write_text(normalized.strip() + "\n", encoding="utf-8")

    def _normalize_tc_ids(self, doc_path: Path, tc_prefix: str, tc_start: int) -> None:
        """Renumber any wrong TC IDs the LLM generated, preserving relative order.

        Also replaces bare 'TC_ID' placeholder tokens (models that copied the format
        template literally) with the correct sequential IDs starting at tc_start.
        """
        import re
        text = doc_path.read_text(encoding="utf-8")

        # Replace literal TC_ID placeholders first
        placeholder_count = text.count("TC_ID")
        if placeholder_count:
            counter = tc_start
            def _replace_placeholder(m: re.Match) -> str:  # noqa: E306
                nonlocal counter
                result = f"{tc_prefix}-{counter:03d}"
                counter += 1
                return result
            text = re.sub(r"\bTC_ID\b", _replace_placeholder, text)
            doc_path.write_text(text, encoding="utf-8")
            _log.info("Replaced %d TC_ID placeholder(s) in %s starting at %s-%03d",
                      placeholder_count, doc_path.name, tc_prefix, tc_start)

        # Renumber any PREFIX-NNN IDs that don't start at tc_start
        pattern = re.compile(rf"\b{re.escape(tc_prefix)}-(\d+)\b")
        found = sorted({int(m.group(1)) for m in pattern.finditer(text)})
        if not found:
            return
        correct_seq = list(range(tc_start, tc_start + len(found)))
        if list(found) == correct_seq:
            return
        mapping = {old: new for old, new in zip(found, correct_seq)}

        def _renumber(m: re.Match) -> str:
            return f"{tc_prefix}-{mapping[int(m.group(1))]:03d}"

        fixed = pattern.sub(_renumber, text)
        doc_path.write_text(fixed, encoding="utf-8")
        _log.info("Normalized TC IDs in %s: %s → %s..%s",
                  doc_path.name, found[0], correct_seq[0], correct_seq[-1])

    def _normalize_script_fn_ids(self, script_path: Path, doc_path: Path, tc_prefix: str) -> None:
        """Rename test function names so they match the TC IDs in the doc, in order.

        After ScriptGenAgent runs, models often ignore the doc IDs and number functions
        from 001.  This step reads TC IDs (non-not_automatable) from the doc index table,
        reads function names from the script in declaration order, and renames any that
        carry the wrong ID.  Skips silently if counts don't match (mismatch = model
        added or dropped tests, needs manual review).
        """
        import re

        if not tc_prefix or not doc_path or not doc_path.exists() or not script_path.exists():
            return

        doc_text = doc_path.read_text(encoding="utf-8")

        # Extract TC IDs from the index table rows where status != not_automatable.
        # Table format: | OH-API-014 | description | type | automated | script.py |
        row_re = re.compile(
            rf"^\|\s*({re.escape(tc_prefix)}-(\d{{3}}))\s*\|"
            r"[^|]*\|[^|]*\|\s*(?!not_automat)(\w+)\s*\|",
            re.MULTILINE | re.IGNORECASE,
        )
        doc_ids = [m.group(1) for m in row_re.finditer(doc_text)]

        source = script_path.read_text(encoding="utf-8")
        fn_re = re.compile(r"^def (test_\w+)\s*\(", re.MULTILINE)
        fn_names = fn_re.findall(source)

        if not doc_ids or not fn_names:
            return

        if len(doc_ids) != len(fn_names):
            _log.warning(
                "_normalize_script_fn_ids: %d doc IDs vs %d test functions in %s — skipping",
                len(doc_ids), len(fn_names), script_path.name,
            )
            return

        prefix_in_fn = tc_prefix.replace("-", "_")
        # Matches test_OH_API_001_ prefix in function name (case-insensitive)
        id_in_fn_re = re.compile(rf"^test_{re.escape(prefix_in_fn)}_(\d{{3}})_", re.IGNORECASE)

        new_source = source
        renamed: list[tuple[str, str]] = []

        for doc_id, fn_name in zip(doc_ids, fn_names):
            expected_num = doc_id.split("-")[-1]  # "014"
            m = id_in_fn_re.match(fn_name)
            if m and m.group(1) == expected_num:
                continue  # already correct

            if m:
                # Has the prefix but wrong number — replace the number part only
                correct_fn = f"test_{prefix_in_fn}_{expected_num}_{fn_name[m.end():]}"
            else:
                # No TC ID prefix at all — prepend it
                rest = fn_name[5:] if fn_name.startswith("test_") else fn_name
                correct_fn = f"test_{prefix_in_fn}_{expected_num}_{rest}"

            new_source = re.sub(rf"\b{re.escape(fn_name)}\b", correct_fn, new_source)
            renamed.append((fn_name, correct_fn))

        if renamed:
            script_path.write_text(new_source, encoding="utf-8")
            _log.info(
                "_normalize_script_fn_ids: renamed %d function(s) in %s (e.g. %s → %s)",
                len(renamed), script_path.name, renamed[0][0], renamed[0][1],
            )

    def _review_doc(self, doc_path: Path, domain: str) -> None:
        """Run DocReviewAgent on a freshly generated doc — best-effort, never raises."""
        self._alog.append(
            event_type="agent_run", agent="doc_review",
            domain=domain, status="pending",
            summary=f"DocReview started — {doc_path.name}",
        )
        try:
            from ai.agents.base_agent import AgentContext
            from ai.agents.doc_review_agent import DocReviewAgent
            ctx = AgentContext(domain=domain)
            agent = DocReviewAgent(ai_client=self.ai_client, kb_loader=self.kb_loader, context=ctx)
            kb_context = self.kb_loader.get_all_context() if self.kb_loader else ""
            result = agent.run(doc_path=doc_path, fix=True, kb_context=kb_context)
            issues = result.get("issues", [])
            fixed = result.get("fixed", [])
            if issues:
                _log.info(
                    "DocReview: %d issue(s) found in %s — %d fixed",
                    len(issues), doc_path.name, len(fixed),
                )
            self._alog.append(
                event_type="agent_run", agent="doc_review",
                domain=domain, status="success",
                summary=f"DocReview complete — {len(issues)} issue(s), {len(fixed)} fixed in {doc_path.name}",
            )
        except Exception as exc:
            _log.warning("DocReview skipped (non-fatal): %s", exc)
            self._alog.append(
                event_type="agent_run", agent="doc_review",
                domain=domain, status="error",
                summary=f"DocReview failed: {exc}",
            )

    def _validate_script_paths(self, script_path: Path, domain: str) -> list[str]:
        """Return URL path strings in the generated script not found in the KB.
        Logged as warnings so the developer can spot hallucinated endpoints.
        """
        if domain != "api" or not self.kb_loader:
            return []
        try:
            import re
            text = script_path.read_text(encoding="utf-8")
            found = re.findall(r"""['"](/[\w/{}.\-]+)['"]""", text)
            specs = self.kb_loader.load_api_specs()
            allowed = [e["path"] for e in specs.get("rest_api", {}).get("endpoints", [])]

            def _matches(path: str) -> bool:
                for allowed_path in allowed:
                    pattern = re.sub(r"\{[^}]+\}", "[^/]+", re.escape(allowed_path))
                    if re.fullmatch(pattern, path):
                        return True
                return False

            return [p for p in set(found) if not _matches(p)]
        except Exception:
            return []

    def _review_script(self, script_path: Path, domain: str) -> None:
        """Run ScriptReviewAgent on a freshly generated script — best-effort, never raises."""
        self._alog.append(
            event_type="agent_run", agent="script_review",
            domain=domain, status="pending",
            summary=f"ScriptReview started — {script_path.name}",
        )
        try:
            from ai.agents.base_agent import AgentContext
            from ai.agents.script_review_agent import ScriptReviewAgent
            ctx = AgentContext(domain=domain)
            agent = ScriptReviewAgent(ai_client=self.ai_client, kb_loader=self.kb_loader, context=ctx)
            kb_context = self.kb_loader.get_all_context() if self.kb_loader else ""
            result = agent.run(script_path=script_path, fix=True, kb_context=kb_context, domain=domain)
            issues = result.get("issues", [])
            fixed = result.get("fixed", [])
            if issues:
                _log.info(
                    "ScriptReview: %d issue(s) in %s — %d fixed",
                    len(issues), script_path.name, len(fixed),
                )
            self._alog.append(
                event_type="agent_run", agent="script_review",
                domain=domain, status="success",
                summary=f"ScriptReview complete — {len(issues)} issue(s), {len(fixed)} fixed in {script_path.name}",
            )
        except Exception as exc:
            _log.warning("ScriptReview skipped (non-fatal): %s", exc)
            self._alog.append(
                event_type="agent_run", agent="script_review",
                domain=domain, status="error",
                summary=f"ScriptReview failed: {exc}",
            )

    def _generate_script(
        self,
        test_case_doc: str,
        feature_name: str,
        domain: str,
        output_base: Path = None,
        tc_prefix: str = "",
        exploration_context: str = "",
    ) -> Path:
        from ai.agents import AgentContext, ScriptGenAgent

        product = str(output_base).split("products/")[-1].split("/")[0] if output_base and "products/" in str(output_base) else None
        self._alog.append(
            event_type="agent_run", agent="script_gen",
            domain=domain, product=product, status="pending",
            summary=f"ScriptGen started — {feature_name}",
        )
        try:
            base = output_base if output_base else ROOT_DIR
            ctx = AgentContext(domain=domain, output_base=base).extend(
                tc_prefix=tc_prefix,
                exploration_context=exploration_context,
            )
            agent = ScriptGenAgent(ai_client=self._script_client, kb_loader=self.kb_loader, context=ctx)
            result = agent.run(test_case_doc=test_case_doc, feature_name=feature_name)
            script_path = result["script_path"]
            self._alog.append(
                event_type="agent_run", agent="script_gen",
                domain=domain, product=product, status="success",
                summary=f"ScriptGen complete — {script_path.name}",
            )
            return script_path
        except Exception as exc:
            self._alog.append(
                event_type="agent_run", agent="script_gen",
                domain=domain, product=product, status="error",
                summary=f"ScriptGen failed: {exc}",
            )
            raise

    def _load_increment(self, increment_file: str):
        path = ROOT_DIR / "ai" / "knowledge_base" / "increments" / increment_file
        if not path.exists():
            _log.warning("Increment file not found: %s — skipping", path)
            return
        # invalidate flushes the cache; load_increments re-reads all files including the new one
        self.kb_loader.invalidate()
        self.kb_loader.load_increments()
        _log.info("Loaded increment: %s", increment_file)

    def _log_increment(
        self,
        increment_file: str,
        feature_name: str,
        domain: str,
        doc_path: Path,
        script_path: Path,
    ):
        log_path = ROOT_DIR / "data" / "kb_increments_log.yaml"
        try:
            with log_path.open("r", encoding="utf-8") as f:
                log_data = yaml.safe_load(f) or {}
        except FileNotFoundError:
            log_data = {}

        processed = log_data.get("processed") or []
        processed.append({
            "increment": increment_file,
            "processed_date": str(date.today()),
            "feature": feature_name,
            "domain": domain,
            "generated_doc": str(doc_path.relative_to(ROOT_DIR)),
            "generated_script": str(script_path.relative_to(ROOT_DIR)),
            "status": "generated_pending_review",
        })
        log_data["processed"] = processed

        with log_path.open("w", encoding="utf-8") as f:
            yaml.dump(log_data, f, default_flow_style=False, sort_keys=False)
        _log.info("Increment log updated: %s", log_path)


def _build_client(model: str, args) -> object:
    """Build AI client from CLI args or env vars."""
    import os

    from core.ai_factory import create_ai_client

    ai_config = {
        "enabled": True,
        "mode": "mistral",
        "local": args.local,
        "model": model,
    }
    if args.local:
        ai_config["local_url"] = args.local_url
    else:
        api_key = args.api_key or os.environ.get("MISTRAL_API_KEY")
        if not api_key:
            _log.error("Cloud mode requires --api-key or MISTRAL_API_KEY env var")
            sys.exit(1)
        ai_config["api_key"] = api_key

    return create_ai_client(ai_config)


def _parse_args(argv=None):
    parser = argparse.ArgumentParser(
        description="SentinelFlux AI pipeline: KB → test doc → pytest script"
    )
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--feature", help="Feature name (used for file naming and KB lookup)")
    group.add_argument("--increment", help="Increment YAML filename in ai/knowledge_base/increments/")
    group.add_argument("--doc", help="Path to existing test case doc (skip doc generation)")

    parser.add_argument("--domain", required=True, choices=["api", "web", "mobile", "security", "a11y"])
    parser.add_argument("--skip-script", action="store_true",
                        help="Generate doc only — do not overwrite existing test script")
    parser.add_argument("--project", default=None,
                        help="Product name (e.g. orangehrm). Loads KB from products/<name>/ai/knowledge_base/.")
    parser.add_argument("--local", action="store_true", default=True, help="Use local Ollama (default)")
    parser.add_argument("--local-url", default="http://localhost:11434")
    parser.add_argument("--doc-model", default="qwen2.5-coder:14b-instruct-q4_K_M",
                        help="Ollama model for test case doc generation")
    parser.add_argument("--script-model", default="qwen2.5-coder:14b-instruct-q4_K_M",
                        help="Ollama model for pytest script generation")
    parser.add_argument("--model", default=None,
                        help="Use same model for both doc and script (overrides --doc-model and --script-model)")
    parser.add_argument("--api-key", help="Mistral cloud API key (or set MISTRAL_API_KEY)")
    parser.add_argument("--cloud", action="store_true", help="Use Mistral cloud API instead of local")
    parser.add_argument("--output-base", default=None,
                        help="Root directory for generated docs and scripts "
                             "(e.g. products/orangehrm). Defaults to framework root.")
    parser.add_argument("--tc-prefix", default="",
                        help="Test case ID prefix (e.g. OH-WEB). Injected into doc and script.")
    parser.add_argument("--tc-start", type=int, default=1,
                        help="Starting TC number for ID sequence (default: 1).")
    parser.add_argument("--source", default="",
                        help="API source for richer test generation: path to OpenAPI spec, "
                             "service code file, or a URL. Auto-detected by extension/content.")
    parser.add_argument("--explore", action="store_true",
                        help="Explore the running app before generating — discovers real UI elements and flows. "
                             "Requires --base-url and --explore-pages.")
    parser.add_argument("--base-url", default="",
                        help="App root URL for exploration, e.g. http://localhost:8080")
    parser.add_argument("--login-url", default="",
                        help="Login page path for authentication before exploring, e.g. /auth/login")
    parser.add_argument("--explore-pages", default="",
                        help="Comma-separated list of page paths to explore, e.g. /pim/addEmployee,/leave/apply")
    parser.add_argument("--credentials", default="",
                        help="Credentials for login as username:password (avoid shell history — prefer env vars "
                             "SF_EXPLORE_USER and SF_EXPLORE_PASS)")

    return parser.parse_args(argv)


def main(argv=None):
    args = _parse_args(argv)
    if args.cloud:
        args.local = False

    doc_model = args.model or args.doc_model
    script_model = args.model or args.script_model

    doc_client = _build_client(doc_model, args)

    # Use a separate client for script gen if different model requested
    if script_model != doc_model:
        script_client = _build_client(script_model, args)
    else:
        script_client = doc_client

    # Resolve KB directory
    kb_dir = None
    if args.project:
        kb_dir = ROOT_DIR / "products" / args.project / "ai" / "knowledge_base"
        if not kb_dir.exists():
            _log.error("KB project directory not found: %s", kb_dir)
            sys.exit(1)

    from ai.knowledge_base.kb_loader import KnowledgeBaseLoader
    kb_loader = KnowledgeBaseLoader(kb_dir=kb_dir)

    orchestrator = TestPipelineOrchestrator(doc_client, kb_loader)
    # Inject separate script client if using two models
    orchestrator._script_client = script_client

    skip_script = args.skip_script
    output_base = Path(args.output_base).resolve() if args.output_base else None
    tc_prefix = args.tc_prefix or ""
    source = args.source or ""

    # Exploration args
    explore = args.explore
    base_url = args.base_url or ""
    login_url = args.login_url or ""
    explore_pages = [p.strip() for p in args.explore_pages.split(",") if p.strip()] if args.explore_pages else []
    credentials: dict = {}
    if args.credentials and ":" in args.credentials:
        u, p = args.credentials.split(":", 1)
        credentials = {"username": u, "password": p}
    else:
        import os
        sf_user = os.environ.get("SF_EXPLORE_USER", "")
        sf_pass = os.environ.get("SF_EXPLORE_PASS", "")
        if sf_user and sf_pass:
            credentials = {"username": sf_user, "password": sf_pass}

    # Auto-detect tc_start from existing docs when prefix is known and user did not
    # explicitly override the default (1).  This prevents ID collisions across modules.
    tc_start = args.tc_start
    if tc_prefix and tc_start == 1 and output_base:
        docs_dir = output_base / "docs" / "test_cases" / args.domain
        detected = _find_highest_tc_id(docs_dir, tc_prefix)
        if detected > 0:
            tc_start = detected + 1
            _log.info("Auto-detected tc_start=%d for prefix %s (highest existing: %d)",
                      tc_start, tc_prefix, detected)

    _explore_kwargs = dict(
        explore=explore,
        base_url=base_url,
        login_url=login_url,
        credentials=credentials,
        explore_pages=explore_pages,
    )

    if args.doc:
        doc_path = Path(args.doc).resolve()
        feature_name = doc_path.stem.removeprefix("test_")
        orchestrator.run(
            feature_name=feature_name,
            domain=args.domain,
            skip_doc=True,
            skip_script=skip_script,
            doc_path=doc_path,
            output_base=output_base,
            tc_prefix=tc_prefix,
            tc_start=tc_start,
            source=source,
            **_explore_kwargs,
        )
    elif args.increment:
        stem = Path(args.increment).stem
        # Strip trailing "_<product>" so each YAML gets a unique output filename.
        # e.g. "ess_requirements_orangehrm" + project=orangehrm → "ess_requirements"
        if args.project and stem.endswith(f"_{args.project}"):
            feature_name = stem[: -(len(args.project) + 1)]
        else:
            feature_name = stem
        orchestrator.run(
            feature_name=feature_name,
            domain=args.domain,
            increment_file=args.increment,
            skip_script=skip_script,
            output_base=output_base,
            tc_prefix=tc_prefix,
            tc_start=tc_start,
            source=source,
            **_explore_kwargs,
        )
    else:
        orchestrator.run(
            feature_name=args.feature,
            domain=args.domain,
            skip_script=skip_script,
            output_base=output_base,
            tc_prefix=tc_prefix,
            tc_start=tc_start,
            source=source,
            **_explore_kwargs,
        )


if __name__ == "__main__":
    main()
