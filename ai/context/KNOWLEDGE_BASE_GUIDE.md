# Knowledge Base Guide

## Overview

The Knowledge Base (KB) is a centralized repository of application metadata, API specifications, UI page definitions, and feature documentation. It serves as the single source of truth for the framework and provides context for AI-powered test generation.

### Purpose
- **AI Context**: Provide comprehensive application context to AI systems for intelligent test generation
- **Documentation**: Maintain up-to-date application and API specifications
- **Feature Tracking**: Document feature releases, changes, and upcoming work
- **Test Generation**: Enable generation of test cases based on actual application specifications
- **End-to-End Testing**: Support transition from dummy APIs to production systems

## Knowledge Base Structure

```
ai/knowledge_base/
├── __init__.py                  # Package initialization
├── kb_loader.py                 # KnowledgeBaseLoader utility class
├── application.yaml             # Application metadata and features
├── api_specs.yaml              # REST and GraphQL API specifications
├── ui_pages.yaml               # UI pages, forms, and workflows
└── feature_changelog.md         # Feature history and roadmap
```

## Files and Their Purpose

### `application.yaml`
**Purpose**: Central application configuration and metadata

**Contains**:
- Application name, version, and description
- Environment configurations (QA, Staging, Production URLs)
- Web application URLs and supported browsers
- API base URLs and authentication type
- Features list with versions and dates
- Test data templates
- Validation rules and field constraints

**Example**:
```yaml
application:
  name: "SentinelFlux Booking System"
  version: "1.0.0"
  
features:
  - name: "Booking Management"
    version: "1.0"
    added_date: "2026-01-15"
    endpoints:
      - POST /booking
      - GET /booking/{id}
```

**When to Update**:
- Add a new feature
- Change application URLs
- Add/modify test data templates
- Update validation rules

### `api_specs.yaml`
**Purpose**: Comprehensive API endpoint specifications

**Contains**:
- REST API endpoints with:
  - Path, method, description
  - Request/response formats
  - Authentication requirements
  - Success and error codes
  - Negative test scenarios
- GraphQL queries with:
  - Variables and types
  - Return types
  - Test cases

**Example**:
```yaml
rest_api:
  endpoints:
    - name: "Create Booking"
      path: "/booking"
      method: POST
      negative_cases:
        - "Missing firstname field"
        - "Invalid date format"
```

**When to Update**:
- Add/modify API endpoints
- Change request/response structures
- Document new validation rules
- Add negative test scenarios

### `ui_pages.yaml`
**Purpose**: Web UI page and form specifications

**Contains**:
- Page names and URLs
- Form definitions with:
  - Field names, types, and validation
  - Primary and alternative locators
  - Required/optional indicators
  - Max lengths and constraints
- Buttons and their behaviors
- Test scenarios (positive, negative, edge cases)
- User workflows
- Accessibility notes

**Example**:
```yaml
pages:
  - name: "Test Form Page"
    forms:
      - fields:
        - name: "firstname"
          locators:
            primary: "input#firstname"
            alternative: "input[name='firstname']"
```

**When to Update**:
- Add/remove form fields
- Update locators for changed UI
- Add new test scenarios
- Document new workflows

### `feature_changelog.md`
**Purpose**: Track feature history and roadmap

**Contains**:
- Released features with:
  - Release date
  - Description
  - Test coverage percentage
  - Known limitations
  - Configuration examples
- Upcoming features (planned)
- Dependency versions
- Development notes

**Structure**:
```markdown
## [1.0.0] - 2026-03-15

### Features

#### Feature Name
- Release Date
- Status (Stable/Beta)
- Description
- Test Cases
```

**When to Update**:
- Release a new feature
- Make changes to existing features
- Update feature status
- Note limitations or breaking changes
- Update roadmap

## Using the Knowledge Base

### In AI Skills and Test Generation

```python
from ai.knowledge_base import KnowledgeBaseLoader

kb_loader = KnowledgeBaseLoader()

# Load specific information
app_metadata = kb_loader.load_application_metadata()
api_specs = kb_loader.load_api_specs()
ui_pages = kb_loader.load_ui_pages()
changelog = kb_loader.load_feature_changelog()

# Get formatted context for prompts
rest_context = kb_loader.get_rest_api_context()
graphql_context = kb_loader.get_graphql_api_context()
ui_context = kb_loader.get_ui_context()

# Get comprehensive context
all_context = kb_loader.get_all_context()
```

### In Test Documentation Generation

```bash
# Generate UI test documentation
python ai/generate_test_case_doc.py \
  --page-url "https://app.com/form" \
  --description "User registration form"

# Generate API test documentation
python ai/generate_api_test_doc.py \
  --endpoint /booking \
  --method POST

# Generate GraphQL test documentation
python ai/generate_api_test_doc.py \
  --endpoint countries_list \
  --method QUERY
```

## Adding New Content to Knowledge Base

### Adding a New Feature

1. **Update `application.yaml`**:
   ```yaml
   features:
     - name: "New Feature Name"
       version: "1.0"
       added_date: "2026-05-03"
       endpoints:
         - POST /api/endpoint
   ```

2. **Update `api_specs.yaml`** (if API-related):
   ```yaml
   endpoints:
     - name: "New Endpoint"
       path: "/api/endpoint"
       method: POST
       negative_cases:
         - "Missing required field"
   ```

3. **Update `ui_pages.yaml`** (if UI-related):
   ```yaml
   pages:
     - name: "New Page"
       forms:
         - fields:
           - name: "field"
             required: true
   ```

4. **Update `feature_changelog.md`**:
   ```markdown
   #### New Feature Name
   - Release Date: 2026-05-03
   - Description: Feature description
   - Test Cases: ...
   ```

### Adding New API Endpoints

1. Add to `api_specs.yaml` under appropriate API type
2. Document request/response structure
3. List all negative test scenarios
4. Update `application.yaml` features section
5. Add feature to `feature_changelog.md`

### Adding New UI Forms

1. Add page to `ui_pages.yaml`
2. Document all form fields with locators
3. Add test scenarios (positive, negative, edge cases)
4. Update `application.yaml` if needed
5. Document in `feature_changelog.md`

## Best Practices

### For Developers

1. **Keep KB in sync with code**:
   - Update KB immediately when code changes
   - Review KB changes in PRs

2. **Use specific locators**:
   - Always provide primary and alternative locators
   - Test locators before adding to KB

3. **Document edge cases**:
   - List all negative scenarios
   - Include boundary value tests

4. **Version features**:
   - Use semantic versioning
   - Track release dates

### For Test Automation

1. **Reference KB in tests**:
   - Use KB data for test data instead of hardcoding
   - Reference KB endpoint specs for assertions

2. **Use AI with KB context**:
   - Always load KB when generating tests
   - Include relevant KB sections in AI prompts

3. **Update KB with test results**:
   - Document discovered limitations
   - Add validation rules found during testing

### For Product/Feature Teams

1. **Update KB for new features**:
   - Document at feature design time (not after release)
   - Include acceptance criteria
   - List validation rules

2. **Include in API documentation**:
   - Error codes and scenarios
   - Request/response examples
   - Authentication requirements

3. **Track in changelog**:
   - Feature release date
   - Breaking changes
   - Migration paths

## Integration with AI Test Generation

### How AI Uses the Knowledge Base

1. **Context Injection**: KB content is injected into AI prompts
2. **Validation Rule Awareness**: AI learns field constraints from KB
3. **Test Scenario Guidance**: AI generates tests from documented scenarios
4. **Endpoint Awareness**: AI knows all endpoints and their specs
5. **Feature History**: AI understands feature evolution and limitations

### Example: Generating API Tests with KB Context

```python
from ai.clients.mistral_client import MistralClient
from ai.skills.test_case_doc_kb import TestCaseDocumentationSkill
from ai.knowledge_base import KnowledgeBaseLoader

kb_loader = KnowledgeBaseLoader()
client = MistralClient(api_key="...")
skill = TestCaseDocumentationSkill(client, kb_loader)

# Skill automatically includes KB context in prompts
doc = skill.generate_api_test_document(
    endpoint="/booking",
    method="POST",
    description="Create a new booking"
)
```

## Extending the Knowledge Base

### Adding Custom Knowledge Sections

Extend `KnowledgeBaseLoader` with new methods:

```python
def load_custom_specs(self) -> Dict[str, Any]:
    """Load custom specifications."""
    path = self.kb_dir / "custom_specs.yaml"
    return self._load_yaml(path)

def get_custom_context(self) -> str:
    """Get custom context for prompts."""
    specs = self.load_custom_specs()
    return yaml.dump(specs)
```

### Adding New YAML Files

1. Create `custom_file.yaml` in `ai/knowledge_base/`
2. Add load method to `KnowledgeBaseLoader`
3. Update `__init__.py` documentation
4. Use in skills and scripts

## Migration from Dummy to Production

### Steps

1. **Update `application.yaml`**:
   - Change API base URLs to production
   - Update web application URLs
   - Add production environment config

2. **Update `api_specs.yaml`**:
   - Verify endpoint paths
   - Document actual response structures
   - Update validation rules based on production API

3. **Update `ui_pages.yaml`**:
   - Verify locators on production UI
   - Update field definitions
   - Add new forms/pages if different

4. **Update `feature_changelog.md`**:
   - Document production readiness
   - Note any behavior differences
   - Update integration notes

5. **Regenerate test documentation**:
   ```bash
   python ai/generate_api_test_doc.py --endpoint /booking --method POST
   python ai/generate_test_case_doc.py --page-url "https://prod.app.com"
   ```

## Troubleshooting

### KB File Not Found
- Verify file exists in `ai/knowledge_base/`
- Check file permissions
- Ensure YAML syntax is valid

### AI Not Using KB Context
- Verify KB context is passed to prompt template
- Check for {kb_context} placeholder in template
- Ensure KnowledgeBaseLoader is initialized

### Outdated Test Generation
- Check KB files are up-to-date
- Verify endpoint specs match actual API
- Update locators in ui_pages.yaml if UI changed

## References

- [AI Skills Documentation](ai_skills.md)
- [API Test Generation Guide](api_test_generation.md)
- [Web Test Generation Guide](web_test_generation.md)
- [Framework Architecture](../README.md)
