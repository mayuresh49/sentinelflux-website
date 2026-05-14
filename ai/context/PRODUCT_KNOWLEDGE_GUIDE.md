# Product Knowledge Base Guide

## Overview

The **Product Knowledge Base** captures the business logic, features, personas, rules, and workflows of your application. This is different from technical framework specifications and is used by AI to generate meaningful test cases based on actual product behavior.

## Where Product Knowledge Lives

**File**: `ai/knowledge_base/product_knowledge.yaml`

This YAML file contains:
- Product modules and features
- User personas and access control
- Business rules and validation constraints
- Feature flags and account settings
- Use cases and test scenarios
- Integration points
- Known issues and limitations

## Structure and Sections

### 1. Product Metadata

```yaml
product:
  name: "Your Product Name"
  description: "What the product does"
  version: "1.0.0"
```

### 2. Modules and Features

Define the major features and sub-modules of your product:

```yaml
modules:
  - name: "Booking Management"
    description: "Core module for managing bookings"
    version: "1.0.0"
    enabled_by_default: true
    status: "production"  # or "beta", "deprecated"
    
    sub_modules:
      - name: "Create Booking"
        enabled_by_default: true
      - name: "Modify Booking"
        depends_on: ["View Booking"]
    
    business_rules:
      - "Rule 1"
      - "Rule 2"
    
    validation_rules:
      field_name:
        required: true
        type: "string"
        min_length: 1
        max_length: 100
```

**When to Add**: Each major feature or module should be documented here.

### 3. User Personas and Access Control

Define who uses the product and what they can do:

```yaml
personas:
  - name: "Guest"
    description: "Non-authenticated visitor"
    access_level: 1
    
    features_available:
      - "View public form"
      - "Submit form"
    
    restrictions:
      - "Cannot view other data"
    
    test_scenarios:
      - "Create without authentication"
      - "Cannot access admin panel"
```

**When to Add**: Each user type with different permissions should be a persona.

**Sections**:
- `features_available`: What this persona can do
- `restrictions`: What this persona cannot do
- `test_scenarios`: Test cases for this persona's workflows

### 4. Feature Flags and Settings

Document how features are controlled:

```yaml
feature_flags:
  - name: "feature_name"
    description: "What this flag does"
    default: true
    personas_can_toggle: ["Administrator"]
    impact: "affected_module"
    test_scenarios:
      - "Feature enabled test"
      - "Feature disabled test"

account_settings:
  - name: "Setting Name"
    type: "boolean"  # or "string", "number"
    default_value: true
    persona_can_change: ["Authenticated User"]
```

**When to Add**: Features that can be toggled or settings that users can configure.

### 5. Use Cases and Scenarios

Document the workflows and test scenarios:

```yaml
use_cases:
  - name: "Simple Booking"
    description: "User creates a basic booking"
    actors: ["Guest"]
    
    preconditions:
      - "User is on booking form"
    
    steps:
      - "Enter first name"
      - "Enter last name"
      - "Click submit"
    
    expected_result: "Booking is created"
    
    test_scenarios:
      - "Happy path with valid data"
      - "Missing required field"
      - "Invalid date"
```

**When to Add**: Each major workflow or feature that needs testing.

### 6. Integration Points

Document external systems:

```yaml
integrations:
  - name: "Payment Gateway"
    description: "Processes payments"
    trigger_events:
      - "booking_created"
    business_rules:
      - "Payment must succeed before booking confirmed"
    test_scenarios:
      - "Successful payment"
      - "Failed payment"
```

### 7. Edge Cases and Constraints

Document special cases and limitations:

```yaml
edge_cases:
  - scenario: "Leap year handling"
    description: "System handles Feb 29"
    test_data:
      checkin: "2024-02-28"
      checkout: "2024-02-29"
    expected_behavior: "Booking created"

known_issues:
  - issue: "API accepts historical dates"
    severity: "low"
    workaround: "Validate on client"
    planned_fix: "Q3 2026"
```

## How AI Uses Product Knowledge

The `KnowledgeBaseLoader` extracts product knowledge into formatted contexts:

```python
from ai.knowledge_base import KnowledgeBaseLoader

kb = KnowledgeBaseLoader()

# Get specific contexts
product_ctx = kb.get_product_context()      # Modules and features
personas_ctx = kb.get_personas_context()    # User types
rules_ctx = kb.get_business_rules_context() # Business rules
usecases_ctx = kb.get_use_cases_context()   # Workflows

# Get everything
all_context = kb.get_all_context()  # Complete KB context
```

When generating test documentation, AI receives:

```
=== PRODUCT KNOWLEDGE ===
Product: SentinelFlux

=== MODULES AND FEATURES ===
- Booking Management: Core module for managing bookings
  Business Rules:
    • Check-out date must be after check-in date
    • Booking price must be between 0 and 10000

=== USER PERSONAS AND ACCESS CONTROL ===
- Guest: Non-authenticated visitor
  Features:
    • View public booking form
    • Submit booking

=== USE CASES AND SCENARIOS ===
- Simple Booking: Guest creates a basic booking
  Actors: Guest
  Test Scenarios:
    • Happy path with valid data
    • Missing required field
```

## Adding Product Knowledge Step by Step

### Step 1: Define Your Product

```yaml
product:
  name: "My SaaS Platform"
  description: "Cloud-based project management tool"
  version: "2.0.0"
```

### Step 2: Document Modules

```yaml
modules:
  - name: "Project Management"
    description: "Create and manage projects"
    business_rules:
      - "Project name is required"
      - "Project owner cannot be changed"
      - "Only 10 concurrent projects per user"
```

### Step 3: Define Personas

```yaml
personas:
  - name: "Team Lead"
    description: "Manages team and projects"
    access_level: 2
    features_available:
      - "Create projects"
      - "Invite team members"
      - "Assign tasks"
```

### Step 4: Document Use Cases

```yaml
use_cases:
  - name: "Create Project"
    actors: ["Team Lead"]
    steps:
      - "Navigate to projects"
      - "Click create"
      - "Enter project name"
      - "Click save"
    test_scenarios:
      - "Create with valid name"
      - "Create with duplicate name"
      - "Name too long"
```

### Step 5: Add Business Rules

```yaml
modules:
  - name: "Project Management"
    validation_rules:
      project_name:
        required: true
        max_length: 100
      team_size:
        required: false
        min_value: 1
        max_value: 50
```

## Best Practices

### 1. Use Business Language
```yaml
# ✅ DO: Use business terminology
business_rules:
  - "Customer must verify email before purchase"
  - "Refunds available within 30 days"

# ❌ DON'T: Use technical jargon
business_rules:
  - "email_verified flag must be true in DB"
  - "check refund_window query"
```

### 2. Document All Personas
```yaml
# ✅ DO: Document every user type
personas:
  - name: "Guest"
  - name: "User"
  - name: "Admin"
  - name: "Moderator"

# ❌ DON'T: Leave some personas undocumented
```

### 3. Include Test Scenarios
```yaml
# ✅ DO: Add specific test scenarios
use_cases:
  - name: "Create"
    test_scenarios:
      - "Create with valid data"
      - "Create with missing required field"
      - "Create with invalid email"

# ❌ DON'T: Leave scenarios vague
use_cases:
  - name: "Create"
    test_scenarios:
      - "Test creation"
```

### 4. Keep URLs in Config
```yaml
# ✅ DO: Keep URLs separate
# In product_knowledge.yaml:
validation_rules:
  email:
    pattern: "valid_email_format"

# In config/env_qa.yaml:
application:
  web_url: "https://qa.myapp.local"

# ❌ DON'T: Put URLs in product knowledge
validation_rules:
  callback_url:
    example: "https://qa.myapp.local/callback"
```

### 5. Document Edge Cases
```yaml
# ✅ DO: Include edge cases
edge_cases:
  - scenario: "Timezone boundary crossing"
    test_data:
      start_time: "2025-12-31T23:00Z"
      end_time: "2026-01-01T01:00Z"
    expected_behavior: "Duration calculated correctly"

# ❌ DON'T: Skip edge cases
# Just test normal cases
```

## Keeping Product Knowledge Updated

### When to Update

1. **New Feature Released**
   - Add to `modules` section
   - Add personas who can access it
   - Document business rules

2. **Access Control Changed**
   - Update `personas` section
   - Update `restrictions` list
   - Add test scenarios

3. **Business Rules Changed**
   - Update `business_rules` in module
   - Update validation rules
   - Document impact

4. **New Integration**
   - Add to `integrations` section
   - Document trigger events
   - Add test scenarios

5. **Bug Found**
   - Add to `known_issues`
   - Document workaround
   - Plan fix in roadmap

### Update Checklist

```yaml
# When adding a new feature:
modules:
  - name: "New Feature"
    ✓ description
    ✓ version
    ✓ status (production/beta/deprecated)
    ✓ business_rules (minimum 3)
    ✓ validation_rules (for each input)

personas:
  # Update which personas can access it
  ✓ features_available (add feature)
  ✓ restrictions (any new ones?)
  ✓ test_scenarios (for this persona)

use_cases:
  - name: "Feature Use Case"
    ✓ description
    ✓ actors (which personas)
    ✓ preconditions
    ✓ steps
    ✓ expected_result
    ✓ test_scenarios (minimum 3)
```

## Example: Adding a Payment Feature

```yaml
# Step 1: Add to modules
modules:
  - name: "Payment Processing"
    description: "Handle customer payments"
    business_rules:
      - "Payment must be processed within 30 seconds"
      - "Failed payments are retried 3 times"
      - "PCI compliance is enforced"
      - "Refunds available within 30 days"
    
    validation_rules:
      card_number:
        required: true
        min_length: 13
        max_length: 19
      cvv:
        required: true
        type: "string"
        pattern: "3-4 digits"

# Step 2: Update personas
personas:
  - name: "Customer"
    features_available:
      - "Make payment"
      - "Request refund"
      - "View payment history"

# Step 3: Document use cases
use_cases:
  - name: "Make Payment"
    actors: ["Customer"]
    test_scenarios:
      - "Successful payment with valid card"
      - "Payment with expired card"
      - "Payment with invalid CVV"
      - "Payment amount exceeds limit"

# Step 4: Document integrations
integrations:
  - name: "Payment Gateway"
    trigger_events:
      - "payment_initiated"
    business_rules:
      - "Payment must succeed within 30 seconds"
      - "Failed payments trigger retry logic"

# Step 5: Document known issues
known_issues:
  - issue: "3D Secure sometimes times out"
    severity: "medium"
    workaround: "Retry payment"
    planned_fix: "Q2 2026"
```

## Structure Summary

```
ai/knowledge_base/
├── product_knowledge.yaml          ← Product business logic
│   ├── product metadata
│   ├── modules (features)
│   ├── personas (user types)
│   ├── feature_flags
│   ├── use_cases (workflows)
│   ├── integrations
│   ├── edge_cases
│   └── known_issues
│
├── application.yaml                 ← App config & metadata
├── api_specs.yaml                   ← API technical specs
├── ui_pages.yaml                    ← UI technical specs
└── feature_changelog.md             ← Release notes
```

## Accessing Product Knowledge

```python
from ai.knowledge_base import KnowledgeBaseLoader

kb = KnowledgeBaseLoader()

# Load raw data
product_data = kb.load_product_knowledge()
modules = product_data["modules"]
personas = product_data["personas"]

# Get formatted contexts for AI
product_context = kb.get_product_context()
personas_context = kb.get_personas_context()
rules_context = kb.get_business_rules_context()
usecases_context = kb.get_use_cases_context()

# Get everything for comprehensive AI context
full_context = kb.get_all_context()
```

## Troubleshooting

### Product Knowledge Not Loading
- Verify `product_knowledge.yaml` exists in `ai/knowledge_base/`
- Check YAML syntax (indentation, colons)
- Ensure `KnowledgeBaseLoader` is initialized correctly

### AI Not Using Product Knowledge
- Verify product context is injected in prompts
- Check that prompt templates include `{product_context}` or `{kb_context}`
- Update prompt templates if needed

### Missing Test Scenarios
- Check if `use_cases` section has `test_scenarios`
- Add scenarios for each persona
- Document positive, negative, and edge cases

## See Also

- [Knowledge Base Implementation](KNOWLEDGE_BASE_IMPLEMENTATION.md)
- [AI & KB Integration Guide](AI_KB_INTEGRATION.md)
- [Knowledge Base Overview](KNOWLEDGE_BASE_GUIDE.md)
