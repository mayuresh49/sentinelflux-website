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

> 
**Status values:** `automated` = script exists · `not_automated` = not yet scripted · `not_automatable` = human must mark; skipped by script generator

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

**Pre-conditions:**
- User Role: Admin
- Starting URL: /web/index.php/auth/login
- Required Data State: username=Admin, password=admin123

**Test Data:**
| Field | Value |
|---|---|
| Username | Admin |
| Password | admin123 |

**Steps:**
1. Navigate to the Login Page.
2. Input the credentials and click "Login".

**Expected Result:** Dashboard is visible; navigation elements present.

**Validation:** The displayed page is the Dashboard.

**Category:** positive

**Status:** not_automated

### OH-MOB-002 — ESS User Sees Limited Menu

**Pre-conditions:**
- Role: ESS
- Starting URL: /web/index.php/auth/login
- Required data state: Authenticated with valid ESS credentials (username=Kris.Chapman, password=Admin123)

**Test Data:**
| Field | Value |
|---|---|
| Username | Kris.Chapman |
| Password | Admin123 |

**Steps:**
1. Navigate to the login page and enter the provided credentials.
2. Click on the 'Login' button.
3. Verify that the navigation menu shows only ESS-relevant links.

**Expected Result:** The navigation menu displays limited links compared to Admin.

**Validation:** The displayed links match those specified for an ESS user in the UI Pages Context of the Knowledge Base.

**Category:** positive

**Status:** not_automated

### OH-MOB-003 — Wrong Password Shows Error

**Pre-conditions:**
- User Role: Admin
- Starting URL: https://opensource-demo.orangehrmlive.com/web/index.php/api/v2 (for REST API tests) or /web/index.php/auth/login (for UI tests)
- Required Data State: Session is logged out

**Test Data:**
| Field | Value |
|---|---|
| Username | Admin |
| Password | wrongpassword |

**Steps:**
1. Navigate to login page or authenticate user and create session (for UI tests) or POST request to /auth/login endpoint with provided credentials (for REST API tests)
2. Fill in the username and password fields with the test data values and submit the form
3. Check for error message display (for UI tests) or examine the response status code and body (for REST API tests)

**Expected Result:** Error message displayed (for UI tests) or HTTP 401 Unauthorized status code and appropriate error message in response body (for REST API tests)

**Validation:** Verify that the error message is correctly displayed (for UI tests) or verify that the response status code and error message match expectations (for REST API tests)

**Category:** positive

**Status:** not_automated

### OH-MOB-004 — Empty Username Shows Validation Error

**Pre-conditions:**
- Role: Admin
- Starting URL: https://opensource-demo.orangehrmlive.com/web/index.php/api/v2
- Version: v2
- Base URL: https://opensource-demo.orangehrmlive.com/web/index.php/auth/login

**Test Data:**
| Field | Value |
|---|---|
| Username | (empty) |
| Password | any valid password meeting complexity requirements |

**Steps:**
1. Navigate to the authentication endpoint: POST /auth/login
2. Send a request with empty username and valid password
3. Check for response status code
4. Verify if validation error appears for the username field

**Expected Result:** HTTP response with status 400 Bad Request and validation error message for the username field

**Validation:** Response status code is 400, and error message contains "Username is required"

**Category:** positive

**Status:** not_automated

### OH-MOB-005 — Empty Password Shows Validation Error

**Pre-conditions:**
- Role: Admin/ESS
- Starting URL: /web/index.php/auth/login
- Required data state: Username filled

**Test Data:**
| Field | Value |
|---|---|
| Password | (empty) |

**Steps:**
1. Navigate to Login Page
2. Fill username and leave password blank
3. Tap on Login button

**Expected Result:** Validation error for password field appears

**Validation:** Error message "Password must meet complexity: min 8 chars, uppercase, lowercase, number, special char" is displayed

**Category:** positive

**Status:** not_automated

### OH-MOB-006 — Both Fields Empty Shows Validation Error

**Pre-conditions:**
- Role: Admin/User
- Starting URL: https://opensource-demo.orangehrmlive.com/web/index.php/api/v2/auth/login
- Username and Password are blank

**Test Data:**
| Field | Value |
|---|---|
| Username |  |
| Password |  |

**Steps:**
1. Send a POST request to the provided starting URL with empty username and password
2. Check if the response contains an error message related to the empty fields
3. Check if the session is not created

**Expected Result:** The server responds with an error message for both empty fields

**Validation:** Check the error message displayed on the response and verify that the session remains inactive

**Category:** positive

**Status:** not_automated

### OH-MOB-007 — SQL Injection In Username Shows Error Not 500

**Pre-conditions:**
- Admin role, Login Page: /web/index.php/auth/login
- Required data state: Invalid username with SQL injection

**Test Data:**
| Field | Value |
|---|---|
| Username | `' OR '1'='1`  |
| Password | any value |

**Steps:**
1. Navigate to the Login Page.
2. Input the injection string in the username field and any password.
3. Tap on "Login".

**Expected Result:** Error message shown; no server crash or unhandled exception.

**Validation:** Verify that an error message is displayed, and there is no indication of a server crash or unhandled exception.

**Category:** positive

**Status:** not_automated

### OH-MOB-008 — Username Is Case-Sensitive

**Pre-conditions:**
- User Role: Admin, Starting URL: /web/index.php/auth/login, Required Data State: Valid Password

**Test Data:**
| Field | Value |
|---|---|
| Username | admin (lowercase) |

**Steps:**
1. Navigate to the login page at /web/index.php/auth/login
2. Enter "admin" as the username and valid password
3. Attempt to log in

**Expected Result:** Login fails; error shown

**Validation:** Error message displays: "Invalid username or password."

**Category:** positive

**Status:** not_automated

### OH-MOB-009 — Back Button Does Not Expose Session

**Pre-conditions:**
- User Role: Admin
- Starting URL: /web/index.php/auth/login (Login Page)
- Required Data State: Successfully logged in

**Test Data:**
| Field | Value |
|---|---|
| Username | exact value from KB |
| Password | exact value from KB |

**Steps:**
1. Navigate to the Login Page and log in with the provided credentials.
2. Press the device back button after successful login.
3. Verify that the login page is shown or the app returns to a safe state.

**Expected Result:** The session is not exposed; either the login page is shown or the app returns to a safe state.

**Validation:** Verify that the user is not automatically logged in when navigating back.

**Category:** positive

**Status:** not_automated

### OH-MOB-010 — Session Expires After Inactivity

**Pre-conditions:**
- User Role: Admin/ESS
- Starting URL: /web/index.php/auth/login
- Required Data State: Authenticated user

**Test Data:**
| Field | Value |
|---|---|
| username | exact_admin_username |
| password | exact_password |

**Steps:**
1. Navigate to starting URL and log in with test data.
2. Leave app idle past the configured timeout.
3. Attempt to perform any user action.

**Expected Result:** User is automatically logged out; session expired state shown.

**Validation:** Check if the user is redirected to login page.

**Category:** positive

**Status:** not_automated

### OH-MOB-011 — Valid Login Navigates To Dashboard

**Pre-conditions:**
- User Role: Admin/ESS, Starting URL: /web/index.php/auth/login, Required Data State: orangehrm_credentials present

**Test Data:**
| Field | Value |
|---|---|
| username | exact value from KB |
| password | exact value from KB |

**Steps:**
1. Navigate to /web/index.php/auth/login
2. Enter the provided credentials and click 'Login'
3. Check for successful login message

**Expected Result:** Dashboard/home screen is visible

**Validation:** Verify that the user is navigated to the dashboard after a successful login

**Category:** positive

**Status:** not_automated

### OH-MOB-012 — Invalid Password Shows Error

**Pre-conditions:**
- Role: Admin/ESS, Starting URL: /web/index.php/auth/login, Required Data State: Authenticated user

**Test Data:**
| Field | Value |
|---|---|
| Username | exact value from KB |
| Password | incorrect password (must meet complexity: min 8 chars, uppercase, lowercase, number, special char) |

**Steps:**
1. Navigate to the login page
2. Enter incorrect credentials and submit the form
3. Check for error message visibility

**Expected Result:** Error message visible

**Validation:** Verify that the error message is displayed correctly

**Category:** positive

**Status:** not_automated

### OH-MOB-013 — Invalid Username Shows Error

**Pre-conditions:**
- Role: Admin or ESS
- Starting URL: /web/index.php/auth/login
- Required Data State: Authenticated user logged out

**Test Data:**
| Field | Value |
|---|---|
| Username | nonexistentuser |
| Password | anypassword |

**Steps:**
1. Navigate to the login page
2. Enter invalid username and valid password
3. Click on the "Login" button
4. Verify error message visible

**Expected Result:** Error message displayed

**Validation:** Error message correctly displays for invalid username

**Category:** positive

**Status:** not_automated

### OH-MOB-014 — Empty Username Shows Validation Error

**Pre-conditions:**
- Role: Admin or ESS, Starting URL: /web/index.php/auth/login, Required Data State: Valid Password

**Test Data:**
| Field | Value |
|---|---|
| Username | (empty) |
| Password | (valid password from KB) |

**Steps:**
1. Navigate to the login page
2. Enter empty username and valid password
3. Click on the "Log In" button
4. Observe the error message for the username field

**Expected Result:** Error message displayed for the username field

**Validation:** The error message should indicate that the username is required

**Category:** positive

**Status:** not_automated

### OH-MOB-015 — Empty Password Shows Validation Error

**Pre-conditions:**
- User Role: Admin/ESS, Starting URL: /web/index.php/auth/login, Required Data State: orangehrm_credentials with valid username and empty password

**Test Data:**
| Field | Value |
|---|---|
| Username | exact value from KB |
| Password | Empty |

**Steps:**
1. Navigate to the login page.
2. Enter the valid username and empty password in the respective fields.
3. Click on the "Login" button.

**Expected Result:** A validation error message appears for the password field.

**Validation:** Verify that a validation error message is displayed for the password field.

**Category:** positive

**Status:** not_automated

### OH-MOB-016 — Both Credentials Empty Shows Validation Error

**Pre-conditions:**
- User Role: Admin/ESS
- Starting URL: /web/index.php/auth/login
- Required Data State: Login form fields empty

**Test Data:**
| Field | Value |
|---|---|
| username |  |
| password |  |

**Steps:**
1. Navigate to the login page
2. Enter empty values for username and password fields
3. Click on the 'Login' button

**Expected Result:** A validation error message is displayed

**Validation:** The error message should indicate that both username and password are required fields

**Category:** positive

**Status:** not_automated
