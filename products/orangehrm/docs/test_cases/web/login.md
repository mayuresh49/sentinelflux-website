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

> 
**Status values:** `automated` = script exists · `not_automated` = not yet scripted · `not_automatable` = human must mark; skipped by script generator

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

**Pre-conditions:**
- User Role: Admin
- Starting URL: /web/index.php/auth/login
- Required Data State: Authenticated Session

**Test Data:**
| Field | Value |
|---|---|
| Username | Admin |
| Password | admin123 |

**Steps:**
1. Navigate to login page
2. Enter valid credentials and click Login
3. Verify redirect to dashboard
4. Verify visibility of dashboard elements

**Expected Result:** Redirected to dashboard; dashboard elements visible

**Validation:** Dashboard is displayed, user role matches "Admin"

**Category:** positive

**Status:** not_automated

### OH-WEB-002 — Wrong Password

**Pre-conditions:**
- User Role: Admin, Starting URL: /web/index.php/auth/login, Required Data State: Correct Password stored in KB

**Test Data:**
| Field | Value |
|---|---|
| Username | Admin |
| Password | exact value from KB (without password) |

**Steps:**
1. Navigate to the Login Page
2. Enter the provided username and incorrect password
3. Click on the "Login" button

**Expected Result:** Error message displayed; stays on login page

**Validation:** Error message matches expected format

**Category:** Positive

**Status:** Not_Automated

### OH-WEB-003 — Wrong Username

**Pre-conditions:**
- Role: Admin, Starting URL: /web/index.php/auth/login, Required Data State: None

**Test Data:**
| Field | Value |
|---|---|
| Username | nonexistentuser |
| Password | admin123 |

**Steps:**
1. Navigate to Login Page
2. Enter incorrect username and password, click Login
3. Verify error message displayed

**Expected Result:** Error message displayed; stays on login page

**Validation:** Verifying the displayed error message is correct

**Category:** positive

**Status:** not_automated

### OH-WEB-004 — Empty Username

**Pre-conditions:**
- Role: Admin/ESS
- Starting URL: /web/index.php/auth/login
- Required Data State: Employee not logged in

**Test Data:**
| Field | Value |
|---|---|
| username |  (leave blank) |
| password | exact value from KB |

**Steps:**
1. Navigate to the Login Page
2. Enter the provided password in the Password field
3. Leave the Username field blank
4. Click the Login button

**Expected Result:** Validation error shown for the Username field

**Validation:** Error message appears for empty username and login is not successful

**Category:** positive

**Status:** not_automated

### OH-WEB-005 — Empty Password

**Pre-conditions:**
- User Role: Admin or ESS
- Starting URL: /web/index.php/auth/login
- Required Data State: Valid username

**Test Data:**
| Field | Value |
|---|---|
| Password | (empty) |

**Steps:**
1. Navigate to the Login Page
2. Enter valid username
3. Leave password field empty
4. Click on Login button

**Expected Result:** Validation error shown for password field

**Validation:** Error message "Password is required" appears

**Category:** positive

**Status:** not_automated

### OH-WEB-006 — Both Fields Empty

**Pre-conditions:**
- Role: Any, Starting URL: /web/index.php/auth/login, Required Data State: Username and Password fields empty

**Test Data:**
| Field | Value |
|---|---|
| Username |  |
| Password |  |

**Steps:**
1. Navigate to the login page
2. Enter empty values for username and password fields
3. Click on the 'Login' button

**Expected Result:** Validation error message displayed for either username or password field

**Validation:** Error message "Username cannot be empty" or "Password cannot be empty" is displayed

**Category:** positive

**Status:** not_automated

### OH-WEB-007 — Case-Sensitive Username

**Pre-conditions:**
- User Role: Admin, Starting URL: /web/index.php/auth/login, Required Data State: Valid Password

**Test Data:**
| Field | Value |
|---|---|
| Username | admin (lowercase) |

**Steps:**
1. Navigate to the Login Page at /web/index.php/auth/login
2. Enter "admin" (lowercase) in the username field and valid password
3. Click the "Log In" button

**Expected Result:** Error displayed; login fails

**Validation:** Verify that an error message is shown indicating case-sensitive username

**Category:** positive

**Status:** not_automated

### OH-WEB-008 — SQL Injection in Username

**Pre-conditions:**
- Role: Admin or ESS, Starting URL: /web/index.php/auth/login, Required Data State: Authenticated user with invalid password

**Test Data:**
| Field | Value |
|---|---|
| Username | ' OR '1'='1', |
| Password | admin123   |

**Steps:**
1. Navigate to the Login Page
2. Enter injection string in the username field and password as provided
3. Click on Login

**Expected Result:** Error displayed; no 500 or unhandled exception

**Validation:** Verify that an error message is displayed

**Category:** positive

**Status:** not_automated

### OH-WEB-058 — ESS User Limited Menu (not_automated)

**Pre-conditions:**
- User Role: ESS User
- Starting URL: /web/index.php/auth/login
- Required Data State: Successful Authentication

**Test Data:**
| Field | Value |
|---|---|
| Username | valid_ess_username |
| Password | valid_ess_password |

**Steps:**
1. Navigate to the login page and enter the required credentials.
2. Click on the 'Login' button.
3. Verify that the navigation shows only ESS-relevant links.

**Expected Result:** The ESS user is navigated to their dashboard with only ESS-relevant links visible.

**Validation:** Verify that the ESS user can access their profile, view/edit their own leave requests, and cannot access other system users or administrative features.

**Category:** positive

**Status:** not_automated

### OH-WEB-059 — Back Button Does Not Expose Session (not_automatable)

**Pre-conditions:**
- User Role: Admin/ESS/Supervisor
- Starting URL: Login Page
- Required Data State: Authenticated User

**Test Data:**
| Field | Value |
|---|---|
| Username | exact value from KB |
| Password | exact value from KB |

**Steps:**
1. Navigate to the Login Page and enter valid credentials.
2. Click on 'Login'.
3. Navigate to a different UI Page (e.g., Dashboard, PIM - Employee List).
4. Click the Back Button.

**Expected Result:** The user remains authenticated upon returning to the previous page.

**Validation:** Verify that the user is still logged in and can access sensitive pages.

**Category:** positive

**Status:** not_automated

### OH-WEB-060 — Session Expiry (not_automatable)

**Pre-conditions:**
- User Role: Admin
- Starting URL: https://opensource-demo.orangehrmlive.com/web/index.php/auth/login
- Logged in with valid credentials

**Test Data:**
| Field | Value |
|---|---|
| Username | admin |
| Password | complex_password (min 8 chars, uppercase, lowercase, number, special char) |

**Steps:**
1. Navigate to the login page.
2. Enter the username and password.
3. Click on the 'Login' button.
4. Perform actions requiring user authentication (e.g., navigate to PIM - Employee List).
5. Wait for the configured inactivity timeout (typically 30+ minutes) without performing any actions.

**Expected Result:** User is logged out and redirected to the login page.

**Validation:** Check that the login page is displayed.

**Category:** positive

**Status:** not_automated

### OH-WEB-061 — Account Lock After 5 Failures (not_automatable)

**Pre-conditions:**
- User Role: Admin/User with configured account lockout
- Starting URL: /web/index.php/auth/login
- Required Data State: Account unlocked

**Test Data:**
| Field | Value |
|---|---|
| Username | valid admin username |
| Password | incorrect password (used 5 times) |

**Steps:**
1. Navigate to the Login Page at /web/index.php/auth/login
2. Enter incorrect password for given username and submit login
3. Repeat step 2 four more times with same incorrect password
4. Attempt to log in again with the same incorrect password

**Expected Result:** Account is locked after five consecutive failed login attempts

**Validation:** Check if login fails with a message indicating account lockout

**Category:** positive

**Status:** not_automated
