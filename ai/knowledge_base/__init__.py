"""Knowledge Base Package - Application metadata, API specs, UI specs, and product knowledge

This package contains the application knowledge base used by AI systems for:
- Context-aware test generation
- API documentation and endpoint specifications
- UI page and form specifications
- Feature tracking and changelog
- PRODUCT KNOWLEDGE: modules, personas, features, business rules, use cases
- Test case generation with comprehensive product context

Modules:
- kb_loader: KnowledgeBaseLoader class for loading and caching KB files
- application.yaml: Application metadata, features, and test data
- api_specs.yaml: REST and GraphQL API specifications
- ui_pages.yaml: Web UI pages, forms, and workflows
- feature_changelog.md: Feature history and upcoming roadmap
- product_knowledge.yaml: Business logic, personas, modules, rules, and use cases

Product Knowledge Structure:
- Product modules and sub-modules (features)
- User personas and access control
- Business rules and validation constraints
- Feature flags and account settings
- Use cases and test scenarios
- Integration points
- Known issues and limitations
"""

from .kb_loader import KnowledgeBaseLoader

__all__ = ["KnowledgeBaseLoader"]
