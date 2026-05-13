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

from utils.activity_log import ActivityLog

ROOT_DIR = Path(__file__).resolve().parent.parent.parent

_log = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")


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
    ) -> dict[str, Path]:
        """
        Full pipeline: generate doc then script for a feature + domain.

        skip_doc=True  — reuse existing doc, only regenerate script.
        skip_script=True — regenerate doc only, never touch existing test script.

        Returns dict with keys 'doc' and 'script' (script may be None when skipped).
        """
        _log.info("Pipeline start — feature=%s domain=%s", feature_name, domain)
        product = str(output_base).split("examples/")[-1].split("/")[0] if output_base and "examples/" in str(output_base) else None

        try:
            if increment_file:
                self._load_increment(increment_file)

            if skip_doc and doc_path and doc_path.exists():
                _log.info("Skipping doc generation — using existing: %s", doc_path)
                test_case_doc = doc_path.read_text(encoding="utf-8")
                out_doc = doc_path
            else:
                out_doc = self._generate_doc(
                    feature_name, domain, doc_path,
                    output_base=output_base, tc_prefix=tc_prefix, tc_start=tc_start,
                )
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
                    output={"feature": feature_name, "doc": str(out_doc), "script": None},
                )
                return {"doc": out_doc, "script": None}

            out_script = self._generate_script(
                test_case_doc, feature_name, domain, output_base=output_base, tc_prefix=tc_prefix,
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
                output={"feature": feature_name, "doc": str(out_doc), "script": str(out_script)},
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

    def _generate_doc(
        self,
        feature_name: str,
        domain: str,
        out_path: Path = None,
        output_base: Path = None,
        tc_prefix: str = "",
        tc_start: int = 1,
    ) -> Path:
        from ai.agents import DocGenAgent, AgentContext

        base = output_base if output_base else ROOT_DIR
        ctx = AgentContext(domain=domain, output_base=base).extend(
            tc_prefix=tc_prefix, tc_start=tc_start,
        )
        agent = DocGenAgent(ai_client=self.ai_client, kb_loader=self.kb_loader, context=ctx)
        result = agent.run(feature_name=feature_name, output_path=out_path)
        return result["doc_path"]

    def _generate_script(
        self,
        test_case_doc: str,
        feature_name: str,
        domain: str,
        output_base: Path = None,
        tc_prefix: str = "",
    ) -> Path:
        from ai.agents import ScriptGenAgent, AgentContext

        base = output_base if output_base else ROOT_DIR
        ctx = AgentContext(domain=domain, output_base=base).extend(tc_prefix=tc_prefix)
        agent = ScriptGenAgent(ai_client=self._script_client, kb_loader=self.kb_loader, context=ctx)
        result = agent.run(test_case_doc=test_case_doc, feature_name=feature_name)
        return result["script_path"]

    def _load_increment(self, increment_file: str):
        path = ROOT_DIR / "ai" / "knowledge_base" / "increments" / increment_file
        if not path.exists():
            _log.warning("Increment file not found: %s — skipping", path)
            return
        self.kb_loader.invalidate()
        _log.info("Loaded increment: %s", increment_file)

    def _log_increment(
        self,
        increment_file: str,
        feature_name: str,
        domain: str,
        doc_path: Path,
        script_path: Path,
    ):
        log_path = ROOT_DIR / "framework_knowledge" / "kb_increments_log.yaml"
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
    from utils.ai_factory import create_ai_client

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

    parser.add_argument("--domain", required=True, choices=["api", "web", "mobile", "security"])
    parser.add_argument("--skip-script", action="store_true",
                        help="Generate doc only — do not overwrite existing test script")
    parser.add_argument("--project", default=None,
                        help="KB project subdirectory under ai/knowledge_base/ (e.g. orangehrm). "
                             "Defaults to ai/knowledge_base/ root.")
    parser.add_argument("--local", action="store_true", default=True, help="Use local Ollama (default)")
    parser.add_argument("--local-url", default="http://localhost:11434")
    parser.add_argument("--doc-model", default="mistral:7b-instruct-v0.3-q4_K_M",
                        help="Ollama model for test case doc generation")
    parser.add_argument("--script-model", default="qwen2.5-coder:14b-instruct-q4_K_M",
                        help="Ollama model for pytest script generation")
    parser.add_argument("--model", default=None,
                        help="Use same model for both doc and script (overrides --doc-model and --script-model)")
    parser.add_argument("--api-key", help="Mistral cloud API key (or set MISTRAL_API_KEY)")
    parser.add_argument("--cloud", action="store_true", help="Use Mistral cloud API instead of local")
    parser.add_argument("--output-base", default=None,
                        help="Root directory for generated docs and scripts "
                             "(e.g. examples/orangehrm). Defaults to framework root.")
    parser.add_argument("--tc-prefix", default="",
                        help="Test case ID prefix (e.g. OH-WEB). Injected into doc and script.")
    parser.add_argument("--tc-start", type=int, default=1,
                        help="Starting TC number for ID sequence (default: 1).")

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
        kb_dir = ROOT_DIR / "ai" / "knowledge_base" / args.project
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
    tc_start = args.tc_start

    if args.doc:
        doc_path = Path(args.doc)
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
        )
    elif args.increment:
        stem = Path(args.increment).stem
        parts = stem.split("_", 2)
        feature_name = parts[2] if len(parts) > 2 else stem
        orchestrator.run(
            feature_name=feature_name,
            domain=args.domain,
            increment_file=args.increment,
            skip_script=skip_script,
            output_base=output_base,
            tc_prefix=tc_prefix,
            tc_start=tc_start,
        )
    else:
        orchestrator.run(
            feature_name=args.feature,
            domain=args.domain,
            skip_script=skip_script,
            output_base=output_base,
            tc_prefix=tc_prefix,
            tc_start=tc_start,
        )


if __name__ == "__main__":
    main()
