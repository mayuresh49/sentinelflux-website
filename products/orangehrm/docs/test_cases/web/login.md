# Test Case Document — Login Page

**Product:** OrangeHRM  
**Layer:** Web  
**Module:** Login (`/web/index.php/auth/login`)

---

## Test Case Index

| ID | Scenario | Type | Status | Script |
|---|---|---|---|---|
| OH-WEB-001 | Admin user logs in with valid credentials and lands on dashboard | positive | automated | test_login.py |
| OH-WEB-002 | Wrong password shows Invalid credentials error | negative | automated | test_login.py |
| OH-WEB-003 | Wrong username shows Invalid credentials error | negative | automated | test_login.py |
| OH-WEB-004 | Empty username shows validation error | negative | automated | test_login.py |
| OH-WEB-005 | Empty password shows validation error | negative | automated | test_login.py |
| OH-WEB-006 | Both fields empty shows validation error | negative | automated | test_login.py |
| OH-WEB-007 | Username is case-sensitive (Admin != admin) | edge | automated | test_login.py |
| OH-WEB-008 | SQL injection in username shows error, not 500 | negative | automated | test_login.py |
| OH-WEB-058 | ESS user logs in and sees limited navigation menu | positive | not_automated | — |
| OH-WEB-059 | Browser back button after login does not expose session | edge | not_automatable | — |
| OH-WEB-060 | Session expires after inactivity timeout | edge | not_automatable | — |
| OH-WEB-061 | Account locks after 5 consecutive failed login attempts | edge | not_automatable | — |

> **Status values:** `automated` = script exists · `not_automated` = not yet scripted · `not_automatable` = human must mark; skipped by script generator

---

## Page Details
- **URL:** `/web/index.php/auth/login`
- **Fields:**
  - Username (required)
  - Password (required)
  - Login button
  - Error message (optional)
- **Credentials (demo):** Admin / admin123

---

## Business Rules and Validations

- Username is case-sensitive
- Account locks after 5 consecutive failed login attempts (if configured)
- Session expires after configured inactivity timeout
- Password: min 8 chars, uppercase, lowercase, number, special char
- Admin cannot delete their own account

## Field Validation Rules

- `username`: required, string, min 5 / max 40 chars, alphanumeric + underscores, unique
- `password`: required, min 8 chars, must include uppercase, lowercase, number, special character

---

## Detailed Test Cases

### OH-WEB-001 — Valid Admin Login
**Pre-conditions:** OrangeHRM demo is accessible  
**Test Data:** Username=Admin, Password=admin123  
**Steps:**
1. Navigate to login page
2. Enter valid credentials
3. Click Login  
**Expected:** Redirected to dashboard; dashboard elements visible

### OH-WEB-002 — Wrong Password
**Test Data:** Username=Admin, Password=wrongpassword  
**Steps:** Enter wrong password, click Login  
**Expected:** Error message displayed; stays on login page

### OH-WEB-003 — Wrong Username
**Test Data:** Username=nonexistentuser, Password=admin123  
**Steps:** Enter non-existent username, click Login  
**Expected:** Error message displayed; stays on login page

### OH-WEB-004 — Empty Username
**Steps:** Leave username blank, fill password, click Login  
**Expected:** Validation error shown for username field

### OH-WEB-005 — Empty Password
**Steps:** Fill username, leave password blank, click Login  
**Expected:** Validation error shown for password field

### OH-WEB-006 — Both Fields Empty
**Steps:** Click Login without entering anything  
**Expected:** Validation error displayed

### OH-WEB-007 — Case-Sensitive Username
**Steps:** Enter "admin" (lowercase) with valid password  
**Expected:** Error displayed; login fails  
**Note:** xfail on public demo — demo has separate lowercase "admin" account

### OH-WEB-008 — SQL Injection in Username
**Test Data:** Username=`' OR '1'='1`, Password=admin123  
**Steps:** Enter injection string, click Login  
**Expected:** Error displayed; no 500 or unhandled exception

### OH-WEB-058 — ESS User Limited Menu (not_automated)
**Pre-conditions:** ESS user account exists  
**Expected:** After login, navigation shows only ESS-relevant links

### OH-WEB-059 — Back Button Does Not Expose Session (not_automatable)
**Note:** Requires browser-level session verification. Complex to automate reliably across all browsers; recommended as manual exploratory test.

### OH-WEB-060 — Session Expiry (not_automatable)
**Note:** Requires waiting for the configured inactivity timeout (typically 30+ minutes). Not suitable for automated regression runs; verify manually or with time-mocking.

### OH-WEB-061 — Account Lock After 5 Failures (not_automatable)
**Note:** Demo site may not have account lockout configured; this destructive test can lock out the shared demo account. Run only on isolated environments.
