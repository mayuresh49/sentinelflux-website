class PromptTemplate:
    def __init__(self, template: str):
        self.template = template

    def format(self, **kwargs) -> str:
        return self.template.format(**kwargs)


# Example prompts
LOCATOR_HEALING_PROMPT = PromptTemplate("""
Given the following HTML snippet and a broken locator, suggest a new locator.

HTML: {html}
Broken Locator: {broken_locator}
Page URL: {url}

Suggest a valid CSS or XPath selector.
""")

TEST_GENERATION_PROMPT = PromptTemplate("""
Generate a pytest test for the following scenario.

Scenario: {scenario}
Type: {test_type}
Target: {target}
Expected outcome: {expected_outcome}

Include positive, edge-case, and negative-path coverage.
Return valid pytest test code only.
""")

API_TEST_GENERATION_PROMPT = PromptTemplate("""
Generate a pytest API test suite for the following endpoint.

API Name: {api_name}
Endpoint: {endpoint}
Method: {method}
Description: {description}
Payload: {payload_description}
Expected status codes: {expected_status}

{kb_context}

The suite should include:
- standard success case
- edge cases for boundary values and optional inputs
- negative scenarios for invalid payloads, missing fields, and non-existing resource IDs
- response schema and status validation
- error-handling assertions

Return valid pytest test functions only.
""")

TEST_CASE_DOC_PROMPT = PromptTemplate("""
Generate a detailed test case document for the form located at {page_url}.

Knowledge Base Context:
{kb_context}

The document should include:
- Test case title
- Pre-conditions
- Test data
- Step-by-step actions
- Expected results
- Validation rules and constraints
- Negative scenarios for mandatory fields
- Input restriction checks (character limits, invalid characters)
- Notes on optional fields and edge cases

Form Description:
{form_description}

Output full markdown documentation suitable for version control.
""")

API_TEST_CASE_DOC_PROMPT = PromptTemplate("""
Generate a detailed API test case document for the endpoint {endpoint}.

Knowledge Base Context:
{kb_context}

The document should include:
- Test case title
- Endpoint description
- Request method and payload
- Expected response codes
- Positive test cases
- Edge cases
- Negative test cases
- Validation rules
- Notes on authentication and error handling

Output full markdown documentation suitable for version control.
""")