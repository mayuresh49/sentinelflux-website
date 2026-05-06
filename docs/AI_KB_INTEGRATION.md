# AI & Knowledge Base Integration Guide

## Overview

This guide demonstrates how the Knowledge Base integrates with the SentinelFlux framework's AI capabilities to enable context-aware test generation, documentation, and end-to-end testing with real applications.

## Architecture

```
┌─────────────────────────────────────┐
│   Application Specifications        │
├─────────────────────────────────────┤
│  - API Endpoints (REST, GraphQL)    │
│  - UI Pages & Forms                 │
│  - Features & Changelog             │
│  - Test Data & Validation Rules     │
└──────────────┬──────────────────────┘
               │
               ▼
┌─────────────────────────────────────┐
│   Knowledge Base Loader             │
├─────────────────────────────────────┤
│  - Load YAML specs                  │
│  - Format context for AI            │
│  - Cache loaded data                │
└──────────────┬──────────────────────┘
               │
               ▼
┌─────────────────────────────────────┐
│   AI Skills & Prompts               │
├─────────────────────────────────────┤
│  - Test Generation                  │
│  - Documentation Generation         │
│  - Locator Healing                  │
│  - Feature-based Test Creation      │
└──────────────┬──────────────────────┘
               │
               ▼
┌─────────────────────────────────────┐
│   Generated Artifacts               │
├─────────────────────────────────────┤
│  - Test Case Documentation (MD)     │
│  - Pytest Test Code                 │
│  - Validation Scripts               │
│  - Coverage Reports                 │
└─────────────────────────────────────┘
```

## Workflow: From Requirements to Executable Tests

### Step 1: Document Application in Knowledge Base

**Input**: Application specifications, API documentation, UI mockups

**Action**: Update KB files
```bash
# Update feature specification
vim ai/knowledge_base/application.yaml
# Add feature to changelog
vim ai/knowledge_base/feature_changelog.md
# Document API endpoints
vim ai/knowledge_base/api_specs.yaml
# Document UI pages
vim ai/knowledge_base/ui_pages.yaml
```

**Example - Adding Booking API**:
```yaml
# In api_specs.yaml
rest_api:
  endpoints:
    - name: "Create Booking"
      path: "/booking"
      method: POST
      negative_cases:
        - "Missing firstname"
        - "Invalid totalPrice format"
```

### Step 2: Generate Test Documentation with AI

**Input**: KB specifications

**Action**: Run the API and web generation scripts

#### API documentation
```bash
python ai/generate_api_test_doc.py \
  --endpoint /booking \
  --method POST \
  --output docs/test_cases/api/booking_create_tests.md
```

```bash
python ai/generate_api_test_doc.py \
  --endpoint countries_list \
  --method QUERY \
  --output docs/test_cases/api/countries_query_tests.md
```

#### Web UI documentation
```bash
python ai/generate_test_case_doc.py \
  --page-url "https://app.com/booking" \
  --description "Booking form with validation" \
  --output docs/test_cases/web/booking_form_tests.md
```

**Output**: Markdown documentation with:
- Test case descriptions
- Positive scenarios
- Negative scenarios
- Edge cases
- Expected validations

For a detailed guide, see:
- [API Test Generation Guide](api_test_generation.md)
- [Web Test Generation Guide](web_test_generation.md)

### Step 3: Implement Tests from Documentation

**Input**: Generated documentation

**Action**: Create pytest test files
```bash
# Example: tests/api/test_booking_create.py
import pytest
from api.rest_client import RestClient

@pytest.mark.smoke
def test_create_booking_success(rest_client, booking_data):
    """Test successful booking creation with valid data"""
    response = rest_client.post("/booking", json=booking_data)
    assert response.status_code == 201
    assert response.json()["bookingid"] is not None

@pytest.mark.negative
def test_create_booking_missing_firstname(rest_client):
    """Test booking creation fails without firstname"""
    booking_data = {
        "lastname": "Doe",
        "totalprice": 100,
        "depositpaid": True,
        "bookingdates": {"checkin": "2026-06-01", "checkout": "2026-06-10"}
    }
    response = rest_client.post("/booking", json=booking_data)
    assert response.status_code == 400
    assert "firstname" in response.json()["error"]
```

### Step 4: Execute Tests with Framework

```bash
# Run all tests with ReportPortal integration
pytest tests/ -v --tb=short

# Run tests in parallel
pytest tests/api/ -n auto -v

# Run with specific browser for UI tests
pytest tests/web/ -v --headed --browser firefox

# Run tests and generate report
pytest tests/ --reportportal -v
```

### Step 5: Update Knowledge Base with Learnings

**Input**: Test execution results, discoveries

**Action**: Update KB with findings
```yaml
# In api_specs.yaml, document discovered behavior
endpoints:
  - name: "Create Booking"
    path: "/booking"
    known_issues:
      - "API accepts historical dates without validation"
      - "additionalneeds field not sanitized for XSS"
    validation:
      date_format: "YYYY-MM-DD"
      price_range:
        min: 0
        max: 10000
```

## Usage Patterns

### Pattern 1: Test Generation for New API Endpoint

**Scenario**: New REST endpoint added to application

```python
# In test_generation/api_booking.py
from ai.clients.mistral_client import MistralClient
from ai.skills.test_case_doc_kb import TestCaseDocumentationSkill
from ai.knowledge_base import KnowledgeBaseLoader

def generate_booking_tests():
    kb_loader = KnowledgeBaseLoader()
    client = MistralClient(api_key="sk-...")
    skill = TestCaseDocumentationSkill(client, kb_loader)
    
    # KB provides context about endpoint
    doc = skill.generate_api_test_document(
        endpoint="/booking",
        method="POST",
        description="Create new booking",
        api_type="rest"
    )
    
    # Save documentation
    Path("docs/test_cases/api/booking_create.md").write_text(doc)
    
    # AI-generated tests based on KB specs
    return doc
```

### Pattern 2: Update Knowledge Base for Feature Release

```python
# In utils/kb_updater.py
import yaml
from pathlib import Path

def add_feature_to_kb(feature_name, version, endpoints=None, ui_pages=None):
    """Add feature to knowledge base"""
    
    # Update application.yaml
    app_path = Path("ai/knowledge_base/application.yaml")
    with app_path.open() as f:
        app_data = yaml.safe_load(f)
    
    app_data["features"].append({
        "name": feature_name,
        "version": version,
        "added_date": "2026-05-03",
        "endpoints": endpoints or []
    })
    
    with app_path.open("w") as f:
        yaml.dump(app_data, f)
    
    # Update feature_changelog.md
    changelog_path = Path("ai/knowledge_base/feature_changelog.md")
    changelog = changelog_path.read_text()
    changelog += f"\n\n#### {feature_name}\n- Release Date: 2026-05-03\n- Version: {version}\n"
    changelog_path.write_text(changelog)
```

### Pattern 3: Self-Healing with Knowledge Base Context

```python
# In ai/skills/self_healing.py (extended)
def heal_locator(broken_locator, page_html, page_url):
    """Heal broken locator using KB context"""
    from ai.knowledge_base import KnowledgeBaseLoader
    
    kb_loader = KnowledgeBaseLoader()
    ui_context = kb_loader.get_ui_context()
    
    prompt = f"""
Given the following KB context and HTML, find the correct locator:

Knowledge Base UI Context:
{ui_context}

Current Page HTML:
{page_html}

Broken Locator: {broken_locator}
Page URL: {page_url}

Suggest a working locator.
"""
    
    response = ai_client.generate(prompt)
    return response.strip()
```

## Best Practices

### 1. Keep KB Updated During Development

✅ **DO**:
```python
# When adding feature, update KB first
# ai/knowledge_base/api_specs.yaml
endpoints:
  - name: "New Feature Endpoint"
    path: "/api/feature"
    negative_cases: [...]
```

❌ **DON'T**:
```python
# Don't hardcode specs in tests
def test_feature():
    response = client.post("/api/feature", json={...})
    # Specs should come from KB, not hardcoded
```

### 2. Use KB Data in Tests

✅ **DO**:
```python
from ai.knowledge_base import KnowledgeBaseLoader

def test_with_kb():
    kb = KnowledgeBaseLoader()
    specs = kb.load_api_specs()
    endpoint = specs["rest_api"]["endpoints"][0]
    test_with_endpoint(endpoint)
```

❌ **DON'T**:
```python
def test_without_kb():
    endpoint = {
        "path": "/booking",
        "method": "POST"
    }  # Hardcoded instead of from KB
```

### 3. Document Test Discoveries in KB

✅ **DO**:
```python
# When test reveals behavior not in KB
# Update feature_changelog.md
known_issues:
  - "API doesn't validate historical dates"
  - "Response includes internal field 'debug_mode'"
```

❌ **DON'T**:
```python
# Don't leave discoveries only in test code
# This information should be in KB for AI and other tests
def test_booking_historical_date():
    # Discovery: API accepts past dates without validation
    pass
```

### 4. Leverage KB in AI-Powered Test Generation

✅ **DO**:
```bash
# AI uses KB context to generate comprehensive tests
python ai/generate_api_test_doc.py \
  --endpoint /booking \
  --method POST
# AI generates tests for all documented negative cases
```

❌ **DON'T**:
```bash
# Don't provide minimal context
python ai/generate_api_test_doc.py --endpoint /booking --method POST --description "Some endpoint"
# AI has no context for negative scenarios
```

## Transitioning from Dummy to Production

### Phase 1: KB Preparation

```yaml
# Update application.yaml with production URLs
application:
  environment:
    qa: "https://api.qa.sentinelflux.local"
    staging: "https://api.staging.sentinelflux.local"
    production: "https://api.sentinelflux.local"  # NEW
```

### Phase 2: Verify API Specifications

```bash
# Test actual endpoints against KB specs
pytest tests/api/ -v --environment production

# Document any differences
# Update api_specs.yaml with actual behavior
```

### Phase 3: Update UI Locators

```yaml
# In ui_pages.yaml, verify all locators work on production UI
pages:
  - name: "Booking Form"
    forms:
      - fields:
        - name: "firstname"
          locators:
            primary: "input#firstname"  # Verify on production
            alternative: "input[name='firstname']"
```

### Phase 4: Regenerate Test Documentation

```bash
# Use production URLs in KB
python ai/generate_test_case_doc.py \
  --page-url "https://app.sentinelflux.local/booking" \
  --output docs/test_cases/web/booking_form_prod.md

python ai/generate_api_test_doc.py \
  --endpoint /booking \
  --method POST \
  --output docs/test_cases/api/booking_create_prod.md
```

### Phase 5: Execute Full Test Suite

```bash
# Run complete test suite on production
pytest tests/ -v --environment production --tb=short

# Generate ReportPortal report
pytest tests/ --reportportal -v
```

## Files Structure Summary

```
ai/
├── knowledge_base/              ← Knowledge base package
│   ├── __init__.py
│   ├── kb_loader.py            ← Loader utility
│   ├── application.yaml        ← App metadata & features
│   ├── api_specs.yaml          ← REST & GraphQL specs
│   ├── ui_pages.yaml           ← UI & form specs
│   └── feature_changelog.md    ← Feature history
├── generate_test_case_doc.py   ← UI test doc generator (updated)
├── generate_api_test_doc.py    ← API test doc generator (new)
├── skills/
│   ├── test_case_doc.py        ← Original UI skill
│   └── test_case_doc_kb.py     ← KB-aware skill (new)
└── prompts/
    └── prompt_templates.py      ← Updated with KB context

docs/
├── KNOWLEDGE_BASE_GUIDE.md     ← KB documentation
└── test_cases/
    ├── form_test_cases.md
    ├── api_test_cases.md
    └── api/                    ← Generated API tests
```

## Integration Checklist

- [ ] Knowledge base files created and validated
- [ ] KnowledgeBaseLoader imported and working
- [ ] KB-aware skills created (test_case_doc_kb.py)
- [ ] Prompt templates updated with KB context
- [ ] API test doc generator script created
- [ ] UI test doc generator updated to use KB
- [ ] Knowledge base guide documentation complete
- [ ] Integration guide created
- [ ] Example workflows tested
- [ ] Framework conventions verified
- [ ] All code compiles and imports work

## Next Steps

1. **Populate Knowledge Base**: Add your actual application specs to KB YAML files
2. **Generate Test Documentation**: Run generation scripts for your APIs and UI
3. **Implement Tests**: Create pytest files from generated documentation
4. **Execute Tests**: Run tests with framework and verify coverage
5. **Update KB**: Document any discoveries in KB
6. **Iterate**: Continue adding features to KB and regenerating tests

## References

- [Knowledge Base Guide](KNOWLEDGE_BASE_GUIDE.md)
- [Prompt Templates](../ai/prompts/prompt_templates.py)
- [Test Case Documentation](test_cases/api_test_cases.md)
- [AI Skills](../ai/skills/)
