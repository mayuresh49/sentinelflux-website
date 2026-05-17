# Test Case Document — Web Security

**Product:** OrangeHRM  
**Layer:** Web  
**Module:** Security (`/web/index.php/auth/login`, dashboard, admin, PIM)

---

## Test Case Index

| ID | Scenario | Type | Status | Script |
|---|---|---|---|---|
| OH-SEC-008 | XSS payload in login username field does not execute | negative | automated | test_security_web.py |
| OH-SEC-009 | Dashboard URL without auth redirects to login | negative | automated | test_security_web.py |
| OH-SEC-010 | Admin URL without auth redirects to login | negative | automated | test_security_web.py |
| OH-SEC-011 | Session cookie has HttpOnly flag after login | negative | automated | test_security_web.py |
| OH-SEC-012 | PIM URL without auth redirects to login | negative | automated | test_security_web.py |

> **Status values:** `automated` = script exists · `not_automated` = not yet scripted · `not_automatable` = human must mark; skipped by script generator

---

## Scope

These tests verify client-side security controls on the OrangeHRM web layer: XSS prevention, unauthenticated access protection, and session cookie security attributes.

---

## Detailed Test Cases

### OH-SEC-008 — XSS Payload In Username Does Not Execute
**Marks:** `web`, `security`  
**Pre-conditions:** OrangeHRM login page is accessible  
**Test Data:** Username = `<script>window.__xss_fired=true</script>`, Password = `anypassword`  
**Steps:**
1. Navigate to login page
2. Fill username with XSS script tag
3. Fill any password
4. Click Login
5. Check for JS dialog events and `window.__xss_fired`  
**Expected:** No dialog fires; `window.__xss_fired` is not `true`; script tag is sanitised

### OH-SEC-009 — Dashboard Without Auth Redirects To Login
**Marks:** `web`, `security`  
**Pre-conditions:** No active session  
**Steps:** Navigate directly to `/web/index.php/dashboard/index`  
**Expected:** URL contains `/auth/login`; user is not shown dashboard content

### OH-SEC-010 — Admin URL Without Auth Redirects To Login
**Marks:** `web`, `security`  
**Pre-conditions:** No active session  
**Steps:** Navigate directly to `/web/index.php/admin/viewSystemUsers`  
**Expected:** URL contains `/auth/login`

### OH-SEC-011 — Session Cookie Has HttpOnly Flag
**Marks:** `web`, `security`  
**Pre-conditions:** Valid admin credentials  
**Steps:**
1. Navigate to login page
2. Log in with Admin / admin123
3. Inspect all cookies after redirect to dashboard  
**Expected:** Every session/auth cookie (`session`, `orangehrm`, `csrf`) has `httpOnly: true`

### OH-SEC-012 — PIM URL Without Auth Redirects To Login
**Marks:** `web`, `security`  
**Pre-conditions:** No active session  
**Steps:** Navigate directly to `/web/index.php/pim/viewEmployeeList`  
**Expected:** URL contains `/auth/login`
