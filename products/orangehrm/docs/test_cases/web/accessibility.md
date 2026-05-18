# Test Case Document — Web Accessibility

**Product:** OrangeHRM  
**Layer:** Web  
**Module:** Accessibility — Login Page & Dashboard

---

## Test Case Index

| ID | Scenario | Type | Status | Script |
|---|---|---|---|---|
| OH-A11Y-001 | Login inputs have placeholder text as visible labels | positive | automated | test_accessibility.py |
| OH-A11Y-002 | Login page has a brand logo or page title | positive | automated | test_accessibility.py |
| OH-A11Y-003 | Login form is reachable via keyboard Tab navigation | positive | automated | test_accessibility.py |
| OH-A11Y-004 | Login page images have alt text attributes | positive | automated | test_accessibility.py |
| OH-A11Y-005 | Login error message is visible when credentials are invalid | negative | automated | test_accessibility.py |
| OH-A11Y-006 | Dashboard navigation items have visible text | positive | automated | test_accessibility.py |

> 
**Status values:** `automated` = script exists · `not_automated` = not yet scripted · `not_automatable` = human must mark; skipped by script generator

---

## Scope

Checks that the OrangeHRM login page and dashboard meet baseline accessibility requirements: labelled inputs, keyboard reachability, alt-text on images, and visible feedback for errors.

> 
**Note:** OrangeHRM is a Vue SPA — inputs use `placeholder` text as visible labels rather than `<label for>` elements. These tests account for that implementation pattern.

---

## Detailed Test Cases

### OH-A11Y-001 — Login Inputs Have Placeholder Labels
**Marks:** `web`, `a11y`  

**Steps:** Navigate to login page, wait for networkidle  
**Expected:** Both `input[placeholder="Username"]` and `input[placeholder="Password"]` exist

### OH-A11Y-002 — Login Page Has Brand Or Title
**Marks:** `web`, `a11y`  

**Steps:** Navigate to login page  
**Expected:** `page.title()` is non-empty OR at least one `<img>` is present (logo)

### OH-A11Y-003 — Login Form Reachable By Keyboard
**Marks:** `web`, `a11y`  

**Steps:** Navigate to login page; click body to set document focus; press Tab  
**Expected:** `document.activeElement.tagName` is one of `INPUT`, `BUTTON`, `A`, `SELECT`, `TEXTAREA`

### OH-A11Y-004 — Login Page Images Have Alt Text
**Marks:** `web`, `a11y`  

**Steps:** Navigate to login page; inspect every `<img>` element  
**Expected:** Every image has a non-null `alt` attribute

### OH-A11Y-005 — Login Error Visible On Invalid Credentials
**Marks:** `web`, `a11y`  

**Steps:** Navigate to login page; submit `baduser` / `badpass`  
**Expected:** `is_error_displayed()` returns `True`; error element (`.oxd-alert` or `[class*="error"]`) is visible in the DOM

### OH-A11Y-006 — Dashboard Nav Items Have Text
**Marks:** `web`, `a11y`  

**Pre-conditions:** Authenticated as Admin  

**Steps:** Log in; wait for networkidle; read all `.oxd-main-menu-item` elements  
**Expected:** At least one nav item found; every item has non-empty `inner_text()`
