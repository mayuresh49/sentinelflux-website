# Selenium Test Page Form - Test Case Documentation

This document contains test cases for the form on https://automationintesting.com/selenium/testpage/.

## Overview
The form includes:
- First name
- Surname
- Gender selection
- Favorite color radio buttons
- Contact preferences (Email/SMS)
- Free-text message
- Continent selection
- Submit button

## Validation Rules and Constraints
- **First name**: Required. Accepts alphabetic characters and spaces. Should reject empty input.
- **Surname**: Required. Accepts alphabetic characters and spaces. Should reject empty input.
- **Gender**: Required. One option must be selected.
- **Favorite color**: Required. One radio option must be selected.
- **Contact preferences**: Optional. Any combination of Email and SMS may be selected.
- **Message**: Optional. Accepts text input; should handle long entries up to expected browser/form limits.
- **Continent selection**: Optional. One or more continents may be selected.
- **Submit button**: Should be clickable once required fields are completed; form should not throw an error.

## Test Cases

### TC-001: Fill and verify form values
- Pre-conditions: Page is loaded.
- Test data:
  - First name: John
  - Surname: Doe
  - Gender: male
  - Favorite color: red
  - Contact preferences: Email, SMS
  - Message: "This is a test message."
  - Continents: Asia, Europe
- Steps:
  1. Enter first name.
  2. Enter surname.
  3. Select gender.
  4. Choose favorite color.
  5. Select both contact preferences.
  6. Enter the message.
  7. Select multiple continents.
- Expected result:
  - Each field retains the entered value.
  - Selected radio and checkboxes remain checked.
  - Multi-select contains chosen continents.

### TC-002: Required fields validation
- Pre-conditions: Page is loaded.
- Steps:
  1. Leave first name empty.
  2. Leave surname empty.
  3. Do not select gender.
  4. Do not select a favorite color.
  5. Click Submit.
- Expected result:
  - The form should prevent submission or show validation feedback.
  - Required fields remain highlighted or marked as invalid.

### TC-003: Invalid input validation
- Pre-conditions: Page is loaded.
- Steps:
  1. Enter numeric or special characters in first name.
  2. Enter numeric or special characters in surname.
  3. Complete the rest of the required fields.
  4. Click Submit.
- Expected result:
  - The form should reject invalid characters if validation exists.
  - The system should provide clear feedback for invalid input.

### TC-004: Message field limits and long text handling
- Pre-conditions: Page is loaded.
- Steps:
  1. Enter a very long message string into the message field.
  2. Complete the required fields.
  3. Click Submit.
- Expected result:
  - The message field should accept text up to the allowed limit.
  - The form should not crash or display an error unrelated to the message length.

### TC-005: Optional fields behavior
- Pre-conditions: Page is loaded.
- Steps:
  1. Fill only the required fields.
  2. Leave contact preferences and message blank.
  3. Click Submit.
- Expected result:
  - Form submission should still be possible if only required fields are populated.
  - Optional fields may remain empty without preventing submission.

## Notes
- AI-based self-healing can be used to recover failed locators and adjust selectors.
- This document is version controlled under `docs/test_cases/form_test_cases.md`.
