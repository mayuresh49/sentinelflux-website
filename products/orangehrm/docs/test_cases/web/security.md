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
**Pre-conditions:**
- Role: Standard User
- Starting URL: /web/index.php/auth/login
- Required Data State: Password set

**Test Data:**
| Field | Value |
|---|---|
| Username | `<script>window.__xss_fired=true</script>` |
| Password | `anypassword` |

**Steps:**
1. Navigate to login page
2. Fill username with XSS script tag
3. Fill password
4. Click Login
5. Check for JS dialog events and `window.__xss_fired`

**Expected Result:** No dialog fires; `window.__xss_fired` is not `true`; script tag is sanitised

**Validation:** Script execution does not occur, `window.__xss_fired` remains false.

**Category:** positive
**Status:** not_automated### OH-SEC-009 — Dashboard Without Auth Redirects To Login
**Pre-conditions:**
- User Role: Anonymous
- Starting URL: /web/index.php/dashboard/index
- Required Data State: No active session

**Test Data:**
| Field | Value |
|---|---|
| User Role | Anonymous |
| Active Session | None |

**Steps:**
1. Navigate directly to `/web/index.php/dashboard/index` as an anonymous user without an active session.
2. No specific user action is required, as the lack of an active session should trigger automatic navigation.
3. Verify that the URL contains `/auth/login`.
4. Verify that the user is not shown dashboard content.

**Expected Result:** The user is redirected to the login page (`/web/index.php/auth/login`). No dashboard content is displayed.

**Validation:** Verify that the URL contains `/auth/login`. Verify that no dashboard content is visible.### OH-SEC-010 — Admin URL Without Auth Redirects To Login
**Pre-conditions:**
- User Role: Admin
- Starting URL: <https://opensource-demo.orangehrmlive.com/web/index.php/api/v2>
- Required Data State: No active session

**Test Data:**
| Field | Value |
|---|---|
| None | N/A |

**Steps:**
1. Navigate to `/web/index.php/admin/viewSystemUsers`
2. Verify that the URL contains `/auth/login`
3. Attempt to access system users page without authentication

**Expected Result:** The user is redirected to the login page (`/auth/login`)

**Validation:** Check if the URL contains `/auth/login` after attempting to access the system users page without authentication

**Category:** positive
**Status:** not_automated### OH-SEC-011 — Session Cookie Has HttpOnly Flag
**Pre-conditions:**
- Role: Admin
- Starting URL: /web/index.php/auth/login
- Required data state: Valid admin credentials (Username: Admin, Password: admin123)

**Test Data:**
| Field | Value |
|---|---|
| Session Cookie | session, orangehrm, csrf |

**Steps:**
1. Navigate to login page
2. Log in with Admin / admin123
3. Inspect all cookies after redirect to dashboard

**Expected Result:** Every session/auth cookie has `httpOnly: true`

**Validation:** Verify that the session, orangehrm, and csrf cookies have the HttpOnly flag set to true.

**Category:** positive
**Status:** not_automated### OH-SEC-012 — PIM URL Without Auth Redirects To Login
**Pre-conditions:**
- User Role: Anonymous
- Starting URL: /web/index.php/pim/viewEmployeeList
- Required Data State: No active session

**Test Data:**
| Field | Value |
|---|---|
| N/A | N/A |

**Steps:**
1. Navigate directly to "/web/index.php/pim/viewEmployeeList" without an active session.
2. No specific user action required (since the system should automatically redirect to the login page).
3. Check if the URL contains "/auth/login".

**Expected Result:** The URL contains "/auth/login".

**Validation:** Verify that the system redirects to the login page when accessing a PIM-related URL without an active session.

**Category:** positive
**Status:** not_automated