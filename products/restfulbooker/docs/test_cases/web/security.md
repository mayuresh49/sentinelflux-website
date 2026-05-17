# Test Case Document — Web Security

**Product:** Restful Booker  
**Layer:** Web  
**Module:** Security — Home Page & Admin Panel

---

## Test Case Index

| ID | Scenario | Type | Status | Script |
|---|---|---|---|---|
| RB-SEC-006 | XSS payload in contact form does not execute | negative | automated | test_security_web.py |
| RB-SEC-007 | Admin panel requires login credentials to access | negative | automated | test_security_web.py |
| RB-SEC-008 | XSS payload in booking firstname field does not execute | negative | automated | test_security_web.py |
| RB-SEC-009 | Home page does not expose web server version in headers | negative | automated | test_security_web.py |

> **Status values:** `automated` = script exists · `not_automated` = not yet scripted · `not_automatable` = human must mark; skipped by script generator

---

## Scope

Client-side security checks on the Restful Booker web layer: XSS prevention in user-input forms, access control on the admin panel, and response header hygiene.

---

## Detailed Test Cases

### RB-SEC-006 — XSS In Contact Form Does Not Execute
**Marks:** `web`, `security`, `regression`  
**Pre-conditions:** Home page is accessible  
**Test Data:** XSS payload = `<script>window.__xss_fired=true</script>`  
**Steps:**
1. Navigate to home page
2. Fill `#name` and `#message` (or equivalent contact fields) with XSS payload
3. Fill `#email` with a valid-format email
4. Check for JS dialog events and `window.__xss_fired`  
**Expected:** No dialog fires; `window.__xss_fired` is not `true`

### RB-SEC-007 — Admin Panel Requires Login
**Marks:** `web`, `security`, `sanity`  
**Pre-conditions:** No active admin session  
**Steps:** Navigate directly to `/admin`  
**Expected:** A login form (`#username`, `#password`, or `input[name='username']`) is present; admin panel content is not shown without credentials

### RB-SEC-008 — XSS In Booking Firstname Does Not Execute
**Marks:** `web`, `security`, `regression`  
**Test Data:** XSS payload = `<script>window.__xss_fired=true</script>`  
**Steps:**
1. Navigate to home page
2. Click first available Book button to open booking form
3. Fill `input[name='firstname']` or `#firstname` with XSS payload
4. Check for JS dialog events and `window.__xss_fired`  
**Expected:** No dialog fires; `window.__xss_fired` is not `true`

### RB-SEC-009 — Home Page Does Not Expose Server Version
**Marks:** `web`, `security`, `regression`  
**Steps:**
1. Navigate to home page
2. Intercept all responses via Playwright `page.on("response", ...)`
3. Reload page and collect `Server` response headers  
**Expected:** No `Server` header contains a version string for `apache/`, `nginx/`, or `iis/`
