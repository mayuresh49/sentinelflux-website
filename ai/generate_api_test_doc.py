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
import yaml

from ai.clients.mistral_client import MistralClient
from ai.skills.test_case_doc_kb import TestCaseDocumentationSkill
from ai.knowledge_base.kb_loader import KnowledgeBaseLoader


ROOT_DIR = Path(__file__).resolve().parent.parent


def load_config(config_path: Path):
    """Load configuration from YAML file."""
    with config_path.open("r", encoding="utf-8") as stream:
        return yaml.safe_load(stream)


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
        "--config",
        default=str(ROOT_DIR / "config" / "env_qa.yaml"),
        help="Path to environment YAML config"
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
    
    args = parser.parse_args()
    
    # Load configuration
    config = load_config(Path(args.config))
    ai_config = config.get("sentinelflux", {}).get("ai", {})
    
    if not ai_config.get("enabled", False):
        raise SystemExit("AI integration is disabled in the configuration.")
    
    api_key = ai_config.get("api_key")
    if not api_key:
        raise SystemExit("AI api_key is not set in configuration.")
    
    # Initialize AI client and knowledge base
    client = MistralClient(api_key=api_key, model=ai_config.get("mode", "mistral-medium"))
    kb_loader = KnowledgeBaseLoader()
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
