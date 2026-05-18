# Test Case Document — Web Accessibility

**Product:** Restful Booker  
**Layer:** Web  
**Module:** Accessibility — Home Page

---

## Test Case Index

| ID | Scenario | Type | Status | Script |
|---|---|---|---|---|
| RB-A11Y-001 | Home page has at least one heading element | positive | automated | test_accessibility.py |
| RB-A11Y-002 | Room images have alt text attributes | positive | automated | test_accessibility.py |
| RB-A11Y-003 | Contact form fields have labels or placeholders | positive | automated | test_accessibility.py |
| RB-A11Y-004 | Page is keyboard navigable via Tab key | positive | automated | test_accessibility.py |

> 
**Status values:** `automated` = script exists · `not_automated` = not yet scripted · `not_automatable` = human must mark; skipped by script generator

---

## Scope

Baseline accessibility checks for the Restful Booker home page: semantic heading structure, image alt text, form field discoverability, and keyboard navigation.

---

## Detailed Test Cases

### RB-A11Y-001 — Home Page Has Main Heading
**Marks:** `web`, `a11y`, `sanity`  

**Steps:** Navigate to home page; count all elements with role `heading`  
**Expected:** At least 1 heading element found

### RB-A11Y-002 — Room Images Have Alt Text
**Marks:** `web`, `a11y`, `regression`  

**Steps:** Navigate to home page; inspect every `<img>` element  
**Expected:**
- At least 1 image is present on the page
- Every image has a non-null `alt` attribute (empty string is acceptable, missing attribute is not)

### RB-A11Y-003 — Contact Form Fields Have Labels
**Marks:** `web`, `a11y`, `regression`  

**Steps:** Navigate to home page; for each contact field (`name`, `email`, `phone`, `subject`) check for a `<label>` or an input with matching `placeholder`; check that a `<textarea>` for the message exists  
**Expected:** Each field is discoverable via label or placeholder; at least one `<textarea>` is present

### RB-A11Y-004 — Page Is Keyboard Navigable
**Marks:** `web`, `a11y`, `regression`  

**Steps:** Navigate to home page; press Tab once  
**Expected:** `document.activeElement.tagName` is one of `A`, `BUTTON`, `INPUT`, `SELECT`, `TEXTAREA`
