"""Knowledge Base Package - Application metadata, API specs, and feature documentation

This package contains the application knowledge base used by AI systems for:
- Context-aware test generation
- API documentation and endpoint specifications
- UI page and form specifications
- Feature tracking and changelog
- Test case generation with knowledge context

Modules:
- kb_loader: KnowledgeBaseLoader class for loading and caching KB files
- application.yaml: Application metadata, features, and test data
- api_specs.yaml: REST and GraphQL API specifications
- ui_pages.yaml: Web UI pages, forms, and workflows
- feature_changelog.md: Feature history and upcoming roadmap
"""

from .kb_loader import KnowledgeBaseLoader

__all__ = ["KnowledgeBaseLoader"]
