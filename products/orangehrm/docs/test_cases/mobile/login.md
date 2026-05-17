# Test Case Document — Mobile Login

**Product:** OrangeHRM  
**Layer:** Mobile  
**Module:** Login

---

## Test Case Index

| ID | Scenario | Type | Status | Script |
|---|---|---|---|---|
| OH-MOB-001 | Admin user logs in with valid credentials and lands on dashboard | positive | automated | test_login.py |
| OH-MOB-002 | ESS user logs in and sees limited navigation menu | positive | automated | test_login.py |
| OH-MOB-003 | Wrong password shows invalid credentials error | negative | automated | test_login.py |
| OH-MOB-004 | Empty username shows validation error | negative | automated | test_login.py |
| OH-MOB-005 | Empty password shows validation error | negative | automated | test_login.py |
| OH-MOB-006 | Both fields empty shows validation error | negative | automated | test_login.py |
| OH-MOB-007 | SQL injection in username shows error, not 500 | negative | automated | test_login.py |
| OH-MOB-008 | Username is case-sensitive (Admin != admin) | edge | automated | test_login.py |
| OH-MOB-009 | Browser back button after login does not expose session | edge | automated | test_login.py |
| OH-MOB-010 | Session expires after inactivity | edge | automated | test_login.py |
| OH-MOB-011 | Valid login navigates to dashboard (test_login_mobile.py) | positive | automated | test_login_mobile.py |
| OH-MOB-012 | Invalid password shows error message | negative | automated | test_login_mobile.py |
| OH-MOB-013 | Invalid username shows error message | negative | automated | test_login_mobile.py |
| OH-MOB-014 | Empty username field shows validation error | negative | automated | test_login_mobile.py |
| OH-MOB-015 | Empty password field shows validation error | negative | automated | test_login_mobile.py |
| OH-MOB-016 | Both credentials empty shows validation error | negative | automated | test_login_mobile.py |

> **Status values:** `automated` = script exists · `not_automated` = not yet scripted · `not_automatable` = human must mark; skipped by script generator

---

## Screen Details
- **Screen:** Login screen
- **Fields:** Username, Password, Login button
- **Credentials (demo):** Admin / admin123, ESS: Kris.Chapman / Admin123

---

## Notes

- `test_login.py` uses the Appium page object model (`appium_driver` fixture)
- `test_login_mobile.py` uses a `login_screen` fixture with separate implementation; covers a subset of the same scenarios

---

## Detailed Test Cases

### OH-MOB-001 — Admin Valid Login Lands On Dashboard
**Test Data:** username=Admin, password=admin123  
**Steps:** Launch app; fill credentials; tap Login  
**Expected:** Dashboard is visible; navigation elements present

### OH-MOB-002 — ESS User Sees Limited Menu
**Test Data:** username=Kris.Chapman, password=Admin123  
**Steps:** Launch app; fill ESS credentials; tap Login  
**Expected:** Navigation menu shows only ESS-relevant links (limited compared to Admin)

### OH-MOB-003 — Wrong Password Shows Error
**Test Data:** username=Admin, password=wrongpassword  
**Steps:** Fill valid username and wrong password; tap Login  
**Expected:** Error message displayed; login fails

### OH-MOB-004 — Empty Username Shows Validation Error
**Steps:** Leave username blank; fill password; tap Login  
**Expected:** Validation error for username field

### OH-MOB-005 — Empty Password Shows Validation Error
**Steps:** Fill username; leave password blank; tap Login  
**Expected:** Validation error for password field

### OH-MOB-006 — Both Fields Empty Shows Validation Error
**Steps:** Tap Login without entering anything  
**Expected:** Validation error displayed

### OH-MOB-007 — SQL Injection In Username Shows Error Not 500
**Test Data:** username = `' OR '1'='1`  
**Steps:** Fill injection string in username; fill any password; tap Login  
**Expected:** Error message shown; no server crash or unhandled exception

### OH-MOB-008 — Username Is Case-Sensitive
**Test Data:** username=admin (lowercase)  
**Steps:** Enter lowercase "admin" with valid password  
**Expected:** Login fails; error shown  
**Note:** May xfail if demo has a separate lowercase admin account

### OH-MOB-009 — Back Button Does Not Expose Session
**Steps:** Log in as Admin; press device back button  
**Expected:** Session not exposed; login page shown or app returns to safe state

### OH-MOB-010 — Session Expires After Inactivity
**Steps:** Log in; leave app idle past the configured timeout  
**Expected:** User is automatically logged out; session expired state shown

### OH-MOB-011 — Valid Login Navigates To Dashboard
**Fixture:** `login_screen`, `orangehrm_credentials`  
**Steps:** `login_screen.login(username, password)`  
**Expected:** Dashboard/home screen is visible

### OH-MOB-012 — Invalid Password Shows Error
**Fixture:** `login_screen`, `orangehrm_credentials`  
**Steps:** `login_screen.login(username, wrong_password)`  
**Expected:** Error message visible

### OH-MOB-013 — Invalid Username Shows Error
**Fixture:** `login_screen`  
**Steps:** `login_screen.login("nonexistentuser", "anypassword")`  
**Expected:** Error message visible

### OH-MOB-014 — Empty Username Shows Validation Error
**Fixture:** `login_screen`, `orangehrm_credentials`  
**Steps:** Submit with empty username and valid password  
**Expected:** Validation error for username

### OH-MOB-015 — Empty Password Shows Validation Error
**Fixture:** `login_screen`, `orangehrm_credentials`  
**Steps:** Submit with valid username and empty password  
**Expected:** Validation error for password

### OH-MOB-016 — Both Credentials Empty Shows Validation Error
**Fixture:** `login_screen`  
**Steps:** Submit with both fields empty  
**Expected:** Validation error displayed
