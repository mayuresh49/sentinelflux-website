# Test Case Document — Web Timesheets

**Product:** OrangeHRM
**Layer:** Web
**Module:** Timesheets

---

## Test Case Index

| ID | Scenario | Type | Status | Script |
|---|---|---|---|---|
| OH-WEB-072 | Authenticated user can access Timesheets form | positive | automated | test_Timesheets.py |
| OH-WEB-073 | Valid timesheet submission with all required fields | positive | automated | test_Timesheets.py |
| OH-WEB-074 | Missing Employee ID and Hours Worked shows validation errors | negative | automated | test_Timesheets.py |
| OH-WEB-075 | Excessive hours worked value shows validation error | negative | automated | test_Timesheets.py |
| OH-WEB-076 | Empty From Date shows validation error | negative | automated | test_Timesheets.py |
| OH-WEB-077 | Duplicate Employee ID submission shows error | negative | automated | test_Timesheets.py |
| OH-WEB-078 | Session expires after inactivity timeout | edge | automated | test_Timesheets.py |
| OH-WEB-079 | Password complexity rules enforced | security | automated | test_Timesheets.py |
| OH-WEB-080 | Admin cannot delete their own account | security | automated | test_Timesheets.py |
| OH-WEB-081 | ESS user can only edit their own profile | edge | automated | test_Timesheets.py |
| OH-WEB-082 | Supervisor can view direct reports' timesheets | positive | automated | test_Timesheets.py |

> **Status values:** `automated` = script exists · `not_automated` = not yet scripted · `not_automatable` = human must mark; skipped by script generator

---

## Fields in Scope

| Field | Type | Required | Validation |
|---|---|---|---|
| employee_id | String | Yes | Must reference an existing employee; unique per timesheet period |
| timesheet_from_date | Date | Yes | YYYY-MM-DD format; cannot be empty |
| timesheet_to_date | Date | Yes | YYYY-MM-DD format; must be ≥ from_date |
| hours_worked | Numeric | Yes | Positive integer; excessive values (e.g. 999) rejected |

---

## Detailed Test Cases

### OH-WEB-072 — Authenticated User Can Access Timesheets Form
**Pre-conditions:**
- User role: Admin (credentials: Admin / admin123)
- User is logged in and on the dashboard
- Starting URL: /web/index.php/time/viewEmployeeTimesheet
**Steps:**
1. Log in as Admin using valid credentials
2. Navigate to the Timesheets form URL
3. Assert that the Timesheets form is displayed
**Expected Result:** The Timesheets form page loads successfully and is visible to the authenticated user.
**Category:** positive
**Status:** automated

---

### OH-WEB-073 — Valid Timesheet Submission With All Required Fields
**Pre-conditions:**
- User role: Admin (credentials: Admin / admin123)
- Employee with ID 12345 exists in the system
- Starting URL: /web/index.php/time/viewEmployeeTimesheet
**Test Data:**
| Field | Value |
|---|---|
| employee_id | 12345 |
| timesheet_from_date | 2023-01-01 |
| timesheet_to_date | 2023-01-07 |
| hours_worked | 40 |
**Steps:**
1. Navigate to the Timesheets form
2. Fill in employee_id=12345, from_date=2023-01-01, to_date=2023-01-07, hours_worked=40
3. Click Submit and assert submission success
**Expected Result:** Timesheet is submitted successfully; success confirmation is displayed.
**Category:** positive
**Status:** automated

---

### OH-WEB-074 — Missing Employee ID And Hours Worked Shows Validation Errors
**Pre-conditions:**
- User role: Admin (credentials: Admin / admin123)
- Starting URL: /web/index.php/time/viewEmployeeTimesheet
**Test Data:**
| Field | Value |
|---|---|
| timesheet_from_date | 2023-01-01 |
| timesheet_to_date | 2023-01-07 |
| employee_id | (empty) |
| hours_worked | (empty) |
**Steps:**
1. Navigate to the Timesheets form
2. Fill only from_date and to_date; leave employee_id and hours_worked blank
3. Click Submit and assert validation errors
**Expected Result:** Validation errors appear for both employee_id (required) and hours_worked (required). Form is not submitted.
**Category:** negative
**Status:** automated

---

### OH-WEB-075 — Excessive Hours Worked Value Shows Validation Error
**Pre-conditions:**
- User role: Admin (credentials: Admin / admin123)
- Employee with ID 12345 exists
- Starting URL: /web/index.php/time/viewEmployeeTimesheet
**Test Data:**
| Field | Value |
|---|---|
| employee_id | 12345 |
| timesheet_from_date | 2023-01-01 |
| timesheet_to_date | 2023-01-07 |
| hours_worked | 999 |
**Steps:**
1. Navigate to the Timesheets form
2. Fill all fields with hours_worked=999 (excessively large value)
3. Click Submit and assert validation error for hours_worked
**Expected Result:** An error message is displayed indicating the hours worked value is invalid. Form is not submitted.
**Category:** negative
**Status:** automated

---

### OH-WEB-076 — Empty From Date Shows Validation Error
**Pre-conditions:**
- User role: Admin (credentials: Admin / admin123)
- Employee with ID 12345 exists
- Starting URL: /web/index.php/time/viewEmployeeTimesheet
**Test Data:**
| Field | Value |
|---|---|
| employee_id | 12345 |
| timesheet_from_date | (empty) |
| timesheet_to_date | 2023-01-07 |
**Steps:**
1. Navigate to the Timesheets form
2. Fill employee_id and to_date; leave from_date empty
3. Click Submit and assert validation error for from_date
**Expected Result:** A validation error for the from_date field is displayed. Form is not submitted.
**Category:** negative
**Status:** automated

---

### OH-WEB-077 — Duplicate Employee ID Submission Shows Error
**Pre-conditions:**
- User role: Admin (credentials: Admin / admin123)
- Employee with ID 12345 already has a timesheet for the specified period
- Starting URL: /web/index.php/time/viewEmployeeTimesheet
**Test Data:**
| Field | Value |
|---|---|
| employee_id | 12345 |
| timesheet_from_date | 2023-01-01 |
| timesheet_to_date | 2023-01-07 |
| hours_worked | 40 |
**Steps:**
1. Navigate to the Timesheets form
2. Fill all fields with the same employee_id and period as an existing timesheet
3. Click Submit and assert duplicate entry error
**Expected Result:** An error message is displayed indicating a duplicate timesheet entry exists. Submission is rejected.
**Category:** negative
**Status:** automated

---

### OH-WEB-078 — Session Expires After Inactivity Timeout
**Pre-conditions:**
- User role: Admin (credentials: Admin / admin123)
- Session timeout is configured (system setting)
**Steps:**
1. Log in as Admin
2. Leave the browser idle past the configured session timeout period
3. Attempt to perform an action and assert session expiry redirect
**Expected Result:** User is redirected to the login page; session expired or timed out message is shown.
**Category:** edge
**Status:** automated
**Note:** Stub test — requires session timeout simulation setup.

---

### OH-WEB-079 — Password Complexity Rules Enforced
**Pre-conditions:**
- Starting URL: /web/index.php/auth/login (or admin change-password page)
**Steps:**
1. Navigate to the password change or account creation page
2. Enter a password that does not meet complexity rules
3. Submit and assert validation error
**Expected Result:** An error is displayed listing password complexity requirements. Password is not saved.
**Category:** security
**Status:** automated
**Note:** Stub test — requires password-change page navigation setup.

---

### OH-WEB-080 — Admin Cannot Delete Their Own Account
**Pre-conditions:**
- User role: Admin (credentials: Admin / admin123)
- Admin is logged in
**Steps:**
1. Log in as Admin
2. Navigate to the admin account management page
3. Attempt to delete the currently logged-in admin account
**Expected Result:** Delete action is blocked; an error or disabled UI element prevents self-deletion.
**Category:** security
**Status:** automated
**Note:** Stub test — requires admin account management page navigation setup.

---

### OH-WEB-081 — ESS User Can Only Edit Their Own Profile
**Pre-conditions:**
- User role: ESS (credentials: Kris.Chapman / Admin123)
- ESS user is logged in
**Steps:**
1. Log in as ESS user
2. Attempt to navigate to another employee's profile edit page
3. Assert access is denied or redirected
**Expected Result:** ESS user cannot view or edit profiles belonging to other employees. Access is denied or redirected.
**Category:** edge
**Status:** automated
**Note:** Stub test — requires ESS permission and cross-profile access setup.

---

### OH-WEB-082 — Supervisor Can View Direct Reports' Timesheets
**Pre-conditions:**
- User role: Supervisor (user assigned as supervisor for at least one direct report)
- Direct report has submitted at least one timesheet
**Steps:**
1. Log in as Supervisor
2. Navigate to the Timesheets view for direct reports
3. Assert that the direct report's timesheets are visible
**Expected Result:** Supervisor can see timesheets of their direct reports; timesheets from other employees' chains are not visible.
**Category:** positive
**Status:** automated
**Note:** Stub test — requires supervisor role and direct report data setup.
