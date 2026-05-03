import argparse
from pathlib import Path
import yaml

from ai.clients.mistral_client import MistralClient
from ai.skills.test_case_doc_kb import TestCaseDocumentationSkill
from ai.knowledge_base.kb_loader import KnowledgeBaseLoader


ROOT_DIR = Path(__file__).resolve().parent.parent


def load_config(config_path: Path):
    with config_path.open("r", encoding="utf-8") as stream:
        return yaml.safe_load(stream)


def main():
    parser = argparse.ArgumentParser(description="Generate a test case document for a web form using AI.")
    parser.add_argument("--config", default=str(ROOT_DIR / "config" / "env_qa.yaml"), help="Path to environment YAML config")
    parser.add_argument("--page-url", default="https://automationintesting.com/selenium/testpage/", help="URL of the page to document")
    parser.add_argument("--output", default=str(ROOT_DIR / "docs" / "test_cases" / "generated_test_case_doc.md"), help="Output markdown file path")
    parser.add_argument("--description", default="A web form with first name, surname, gender, favorite color, contact preferences, message, and continent selection.", help="Description of the form for AI prompt")
    args = parser.parse_args()

    config = load_config(Path(args.config))
    ai_config = config.get("sentinelflux", {}).get("ai", {})
    if not ai_config.get("enabled", False):
        raise SystemExit("AI integration is disabled in the configuration.")

    api_key = ai_config.get("api_key")
    if not api_key:
        raise SystemExit("AI api_key is not set in configuration.")

    client = MistralClient(api_key=api_key, model=ai_config.get("mode", "mistral-medium"))
    kb_loader = KnowledgeBaseLoader()
    skill = TestCaseDocumentationSkill(client, kb_loader)
    document = skill.generate_document(args.page_url, args.description)

    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(document, encoding="utf-8")
    print(f"✓ Generated test case document: {output_path}")


if __name__ == "__main__":
    main()
