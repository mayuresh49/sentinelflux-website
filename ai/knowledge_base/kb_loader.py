"""Knowledge Base Loader - loads and caches application and feature information for AI context"""

from pathlib import Path
from typing import Dict, Any
import yaml
from functools import lru_cache


class KnowledgeBaseLoader:
    """Load and cache knowledge base files for AI-powered test generation."""
    
    def __init__(self, kb_dir: Path = None):
        if kb_dir is None:
            kb_dir = Path(__file__).resolve().parent  # Current directory is the KB
        self.kb_dir = kb_dir
        self._cache = {}
    
    @lru_cache(maxsize=10)
    def load_application_metadata(self) -> Dict[str, Any]:
        """Load application configuration and metadata."""
        path = self.kb_dir / "application.yaml"
        return self._load_yaml(path)
    
    @lru_cache(maxsize=10)
    def load_api_specs(self) -> Dict[str, Any]:
        """Load API specifications and endpoints."""
        path = self.kb_dir / "api_specs.yaml"
        return self._load_yaml(path)
    
    @lru_cache(maxsize=10)
    def load_ui_pages(self) -> Dict[str, Any]:
        """Load UI pages and web application specifications."""
        path = self.kb_dir / "ui_pages.yaml"
        return self._load_yaml(path)
    
    @lru_cache(maxsize=10)
    def load_feature_changelog(self) -> str:
        """Load feature changelog as text."""
        path = self.kb_dir / "feature_changelog.md"
        return path.read_text(encoding="utf-8")
    
    def get_rest_api_context(self) -> str:
        """Get REST API context for prompt injection."""
        specs = self.load_api_specs()
        rest = specs.get("rest_api", {})
        
        endpoints_info = []
        for endpoint in rest.get("endpoints", []):
            endpoints_info.append(
                f"- {endpoint['method']} {endpoint['path']}: {endpoint['description']}"
            )
        
        return f"""REST API Context:
Base URL: {rest.get('base_url', 'N/A')}
Version: {rest.get('version', '1.0')}

Endpoints:
{chr(10).join(endpoints_info)}
"""
    
    def get_graphql_api_context(self) -> str:
        """Get GraphQL API context for prompt injection."""
        specs = self.load_api_specs()
        graphql = specs.get("graphql_api", {})
        
        queries_info = []
        for query in graphql.get("queries", []):
            queries_info.append(f"- {query['name']}: {query['description']}")
        
        return f"""GraphQL API Context:
Endpoint: {graphql.get('endpoint', '/graphql')}

Available Queries:
{chr(10).join(queries_info)}
"""
    
    def get_ui_context(self) -> str:
        """Get UI pages context for prompt injection."""
        ui = self.load_ui_pages()
        
        pages_info = []
        for page in ui.get("pages", []):
            pages_info.append(f"- {page['name']}: {page['url']}")
        
        return f"""UI Pages Context:
{chr(10).join(pages_info)}
"""
    
    def get_feature_context(self, feature_name: str = None) -> str:
        """Get feature information from changelog."""
        changelog = self.load_feature_changelog()
        
        if feature_name:
            # Extract specific feature section
            lines = changelog.split('\n')
            feature_section = []
            in_section = False
            for line in lines:
                if feature_name.lower() in line.lower():
                    in_section = True
                if in_section:
                    feature_section.append(line)
                    if line.startswith('---'):
                        break
            return '\n'.join(feature_section[:50]) if feature_section else "Feature not found"
        
        # Return recent changes
        return changelog[:1000]
    
    def _load_yaml(self, path: Path) -> Dict[str, Any]:
        """Load and parse YAML file."""
        if not path.exists():
            raise FileNotFoundError(f"Knowledge base file not found: {path}")
        
        with path.open("r", encoding="utf-8") as f:
            return yaml.safe_load(f) or {}
    
    def get_all_context(self) -> str:
        """Get comprehensive context combining all KB sources."""
        context = []
        context.append("=== KNOWLEDGE BASE CONTEXT ===\n")
        context.append(self.get_ui_context())
        context.append(self.get_rest_api_context())
        context.append(self.get_graphql_api_context())
        context.append("\n=== RECENT FEATURES ===\n")
        context.append(self.get_feature_context())
        
        return '\n'.join(context)
