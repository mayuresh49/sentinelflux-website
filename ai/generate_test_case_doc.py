import argparse
from pathlib import Path

from ai.knowledge_base.kb_loader import KnowledgeBaseLoader
from ai.skills.test_case_doc_kb import TestCaseDocumentationSkill
from core.ai_factory import create_ai_client_from_dashboard

ROOT_DIR = Path(__file__).resolve().parent.parent


def main():
    parser = argparse.ArgumentParser(description="Generate a test case document for a web form using AI.")
    parser.add_argument("--page-url", default="https://automationintesting.com/selenium/testpage/", help="URL of the page to document")
    parser.add_argument("--output", default=str(ROOT_DIR / "docs" / "test_cases" / "generated_test_case_doc.md"), help="Output markdown file path")
    parser.add_argument("--description", default="A web form with first name, surname, gender, favorite color, contact preferences, message, and continent selection.", help="Description of the form for AI prompt")
    parser.add_argument("--kb-dir", default=None, help="Path to product KB directory (default: ai/knowledge_base/)")
    args = parser.parse_args()

    client = create_ai_client_from_dashboard()
    if client is None:
        raise SystemExit("AI provider not configured — set up a provider in the dashboard AI Assistant settings.")

    kb_dir = Path(args.kb_dir) if args.kb_dir else None
    kb_loader = KnowledgeBaseLoader(kb_dir=kb_dir)
    skill = TestCaseDocumentationSkill(client, kb_loader)
    document = skill.generate_document(args.page_url, args.description)

    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(document, encoding="utf-8")
    print(f"✓ Generated test case document: {output_path}")


if __name__ == "__main__":
    main()
