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
    parser.add_argument("--local", action="store_true", help="Use local Mistral via Ollama (http://localhost:11434)")
    parser.add_argument("--local-url", default="http://localhost:11434", help="Local Mistral URL")
    args = parser.parse_args()

    config = load_config(Path(args.config))
    ai_config = config.get("sentinelflux", {}).get("ai", {})
    if not ai_config.get("enabled", False):
        raise SystemExit("AI integration is disabled in the configuration.")

    # Support local Mistral via command line or config
    use_local = args.local or ai_config.get("local", False)
    local_url = args.local_url or ai_config.get("local_url", "http://localhost:11434")
    
    if use_local:
        print(f"Using local Mistral at {local_url}")
        client = MistralClient(api_key=None, model=ai_config.get("model", "mistral"), local=True, local_url=local_url)
    else:
        api_key = ai_config.get("api_key")
        if not api_key:
            raise SystemExit("AI api_key is not set in configuration and --local flag not provided.")
        client = MistralClient(api_key=api_key, model=ai_config.get("model", "mistral-medium"), local=False)

    kb_loader = KnowledgeBaseLoader()
    skill = TestCaseDocumentationSkill(client, kb_loader)
    document = skill.generate_document(args.page_url, args.description)

    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(document, encoding="utf-8")
    print(f"✓ Generated test case document: {output_path}")


if __name__ == "__main__":
    main()
