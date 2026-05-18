"""Generate API test case documentation using AI with knowledge base context

This script generates comprehensive test case documentation for API endpoints,
leveraging the application knowledge base for context-aware test generation.

Usage:
    python ai/generate_api_test_doc.py --endpoint /booking --method POST
    python ai/generate_api_test_doc.py --endpoint /booking/{id} --method GET
    python ai/generate_api_test_doc.py --endpoint countries_list --method QUERY
"""

import argparse
from pathlib import Path

from ai.knowledge_base.kb_loader import KnowledgeBaseLoader
from ai.skills.test_case_doc_kb import TestCaseDocumentationSkill
from core.ai_factory import create_ai_client_from_dashboard

ROOT_DIR = Path(__file__).resolve().parent.parent



def get_endpoint_info(endpoint: str, method: str, kb_loader: KnowledgeBaseLoader):
    """Retrieve endpoint information from knowledge base."""
    api_specs = kb_loader.load_api_specs()
    
    if method.upper() in ["GET", "POST", "PUT", "DELETE"]:
        endpoints = api_specs.get("rest_api", {}).get("endpoints", [])
    else:
        endpoints = api_specs.get("graphql_api", {}).get("queries", [])
    
    for ep in endpoints:
        if ep.get("path") == endpoint or ep.get("name").lower() == endpoint.lower():
            return ep
    
    return None


def main():
    parser = argparse.ArgumentParser(
        description="Generate API test case documentation using AI and knowledge base."
    )
    parser.add_argument(
        "--endpoint",
        required=True,
        help="API endpoint path or name (e.g., /booking, countries_list)"
    )
    parser.add_argument(
        "--method",
        required=True,
        choices=["GET", "POST", "PUT", "DELETE", "QUERY", "MUTATION"],
        help="HTTP method or GraphQL operation type"
    )
    parser.add_argument(
        "--output",
        default=str(ROOT_DIR / "docs" / "test_cases" / "api" / "generated_test_doc.md"),
        help="Output markdown file path"
    )
    parser.add_argument(
        "--description",
        help="Optional custom description for the endpoint"
    )
    parser.add_argument(
        "--kb-dir",
        default=None,
        help="Path to product KB directory (default: ai/knowledge_base/)"
    )

    args = parser.parse_args()

    client = create_ai_client_from_dashboard()
    if client is None:
        raise SystemExit("AI provider not configured — set up a provider in the dashboard AI Assistant settings.")
    kb_dir = Path(args.kb_dir) if args.kb_dir else None
    kb_loader = KnowledgeBaseLoader(kb_dir=kb_dir)
    skill = TestCaseDocumentationSkill(client, kb_loader)
    
    # Get endpoint information from knowledge base
    endpoint_info = get_endpoint_info(args.endpoint, args.method, kb_loader)
    
    if not endpoint_info:
        print(f"Warning: Endpoint '{args.endpoint}' not found in knowledge base.")
        print("Generating documentation with provided information...")
        description = args.description or f"API endpoint {args.method} {args.endpoint}"
    else:
        description = args.description or endpoint_info.get("description", "")
        print(f"Found endpoint in knowledge base: {endpoint_info.get('name')}")
    
    # Generate documentation
    print(f"Generating API test documentation for {args.method} {args.endpoint}...")
    document = skill.generate_api_test_document(
        endpoint=args.endpoint,
        method=args.method,
        description=description,
        api_type="graphql" if args.method in ["QUERY", "MUTATION"] else "rest"
    )
    
    # Save output
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(document, encoding="utf-8")
    
    print(f"✓ Generated API test documentation: {output_path}")
    print(f"  Endpoint: {args.method} {args.endpoint}")
    print(f"  Lines: {len(document.splitlines())}")


if __name__ == "__main__":
    main()
