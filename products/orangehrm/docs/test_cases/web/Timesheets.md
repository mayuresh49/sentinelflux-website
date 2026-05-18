# Test Case Document — Web Timesheets

**Product:** OrangeHRM
**Layer:** Web
**Module:** Timesheets

---

## Test Case Index

| ID | Scenario | Type | Status | Script |
|---|---|---|---|---|
| OH-WEB-072 | Authenticated user can access Timesheets form | positive | automated | test_Timesheets.py |
| OH-WEB-073 | Valid timesheet submitted with all required fields | positive | automated | test_Timesheets.py |
| OH-WEB-074 | Missing Employee ID and Hours Worked shows validation errors | negative | automated | test_Timesheets.py |
| OH-WEB-075 | Excessive hours worked value shows validation error | negative | automated | test_Timesheets.py |
| OH-WEB-076 | Empty From Date shows validation error | negative | automated | test_Timesheets.py |
| OH-WEB-077 | Duplicate Employee ID for same period shows conflict error | negative | automated | test_Timesheets.py |
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
| Employee ID | String | Yes | Must reference an existing employee; unique per timesheet period |
| From Date | Date | Yes | YYYY-MM-DD; cannot be empty |
| To Date | Date | Yes | YYYY-MM-DD; must be >= From Date |
| Hours Worked | Numeric | Yes | Positive integer; excessive values (e.g. 999) rejected |

---

## Detailed Test Cases

### OH-WEB-072 — Authenticated User Can Access Timesheets Form
**Pre-conditions:**
- User role: Admin (username=Admin, password=admin123)
- User is logged in and on the dashboard
- Starting URL: /web/index.php/time/viewEmployeeTimesheet
**Steps:**
1. Log in as Admin using credentials from KB
2. Navigate to the Timesheets form URL
3. Assert that the Timesheets form page is visible
**Expected Result:** The Timesheets form loads successfully and is visible to the authenticated user.
**Category:** positive
**Status:** automated

---

### OH-WEB-073 — Valid Timesheet Submitted With All Required Fields
**Pre-conditions:**
- User role: Admin (username=Admin, password=admin123)
- Employee with ID 12345 exists in the system
- Starting URL: /web/index.php/time/viewEmployeeTimesheet
**Test Data:**
| Field | Value |
|---|---|
| Employee ID | 12345 |
| From Date | 2023-01-01 |
| To Date | 2023-01-07 |
| Hours Worked | 40 |
**Steps:**
1. Navigate to the Timesheets form
2. Fill in employee_id=12345, from_date=2023-01-01, to_date=2023-01-07, hours_worked=40
3. Click Submit and assert submission success message is displayed
**Expected Result:** Timesheet is submitted successfully; success confirmation message is visible.
**Category:** positive
**Status:** automated

---

### OH-WEB-074 — Missing Employee ID And Hours Worked Shows Validation Errors
**Pre-conditions:**
- User role: Admin (username=Admin, password=admin123)
- Starting URL: /web/index.php/time/viewEmployeeTimesheet
**Test Data:**
| Field | Value |
|---|---|
| From Date | 2023-01-01 |
| To Date | 2023-01-07 |
| Employee ID | (empty) |
| Hours Worked | (empty) |
**Steps:**
1. Navigate to the Timesheets form
2. Fill only From Date and To Date; leave Employee ID and Hours Worked blank
3. Click Submit and assert that validation errors appear for both fields
**Expected Result:** Validation error messages appear for the Employee ID (required) and Hours Worked (required) fields. Form is not submitted.
**Category:** negative
**Status:** automated

---

### OH-WEB-075 — Excessive Hours Worked Value Shows Validation Error
**Pre-conditions:**
- User role: Admin (username=Admin, password=admin123)
- Employee with ID 12345 exists
- Starting URL: /web/index.php/time/viewEmployeeTimesheet
**Test Data:**
| Field | Value |
|---|---|
| Employee ID | 12345 |
| From Date | 2023-01-01 |
| To Date | 2023-01-07 |
| Hours Worked | 999 |
**Steps:**
1. Navigate to the Timesheets form
2. Fill all fields with hours_worked=999 (excessively large value)
3. Click Submit and assert a validation error for Hours Worked is shown
**Expected Result:** An error message indicates the hours worked value is invalid or exceeds the maximum. Form is not submitted.
**Category:** negative
**Status:** automated

---

### OH-WEB-076 — Empty From Date Shows Validation Error
**Pre-conditions:**
- User role: Admin (username=Admin, password=admin123)
- Employee with ID 12345 exists
- Starting URL: /web/index.php/time/viewEmployeeTimesheet
**Test Data:**
| Field | Value |
|---|---|
| Employee ID | 12345 |
| From Date | (empty) |
| To Date | 2023-01-07 |
**Steps:**
1. Navigate to the Timesheets form
2. Fill Employee ID and To Date; leave From Date blank
3. Click Submit and assert validation error for From Date field
**Expected Result:** A validation error for From Date is displayed. Form is not submitted.
**Category:** negative
**Status:** automated

---

### OH-WEB-077 — Duplicate Employee ID For Same Period Shows Conflict Error
**Pre-conditions:**
- User role: Admin (username=Admin, password=admin123)
- Employee with ID 12345 already has a timesheet record for 2023-01-01 to 2023-01-07
- Starting URL: /web/index.php/time/viewEmployeeTimesheet
**Test Data:**
| Field | Value |
|---|---|
| Employee ID | 12345 |
| From Date | 2023-01-01 |
| To Date | 2023-01-07 |
| Hours Worked | 40 |
**Steps:**
1. Navigate to the Timesheets form
2. Fill all fields matching an existing timesheet (same employee and period)
3. Click Submit and assert a duplicate entry error is shown
**Expected Result:** An error message indicates a duplicate timesheet entry already exists. Submission is rejected.
**Category:** negative
**Status:** automated

---

### OH-WEB-078 — Session Expires After Inactivity Timeout
**Pre-conditions:**
- User role: Admin (username=Admin, password=admin123)
- Session timeout is configured at the system level
**Steps:**
1. Log in as Admin
2. Leave the browser idle past the configured session timeout period
3. Attempt to perform any action and assert the user is redirected to login
**Expected Result:** User is redirected to the login page; session expired message is shown. No authenticated content is exposed.
**Category:** edge
**Status:** automated
**Note:** Stub — requires session timeout simulation setup.

---

### OH-WEB-079 — Password Complexity Rules Enforced
**Pre-conditions:**
- Starting URL: /web/index.php/auth/login or admin change-password page
**Steps:**
1. Navigate to the password change page
2. Enter a password that does not meet the system's complexity requirements
3. Submit and assert a validation error listing the requirements
**Expected Result:** Password change is rejected with an error message specifying the complexity rules. Password is not updated.
**Category:** security
**Status:** automated
**Note:** Stub — requires password-change page navigation setup.

---

### OH-WEB-080 — Admin Cannot Delete Their Own Account
**Pre-conditions:**
- User role: Admin (username=Admin, password=admin123)
- Admin is logged in and on the admin account management page
**Steps:**
1. Log in as Admin
2. Navigate to the admin account management section
3. Attempt to delete the currently logged-in admin account
**Expected Result:** Delete action is blocked. An error message or disabled UI element prevents the admin from deleting their own account.
**Category:** security
**Status:** automated
**Note:** Stub — requires admin account management page navigation setup.

---

### OH-WEB-081 — ESS User Can Only Edit Their Own Profile
**Pre-conditions:**
- User role: ESS (username=Kris.Chapman, password=Admin123)
- ESS user is logged in
**Steps:**
1. Log in as ESS user Kris.Chapman
2. Attempt to navigate to or edit another employee's profile
3. Assert access is denied or the user is redirected
**Expected Result:** ESS user cannot view or edit profiles of other employees. Access is denied or a redirect to their own profile occurs.
**Category:** edge
**Status:** automated
**Note:** Stub — requires ESS permission and cross-profile access test setup.

---

### OH-WEB-082 — Supervisor Can View Direct Reports' Timesheets
**Pre-conditions:**
- User role: Supervisor (assigned as supervisor for at least one direct report)
- Direct report has submitted at least one timesheet
**Steps:**
1. Log in as Supervisor
2. Navigate to the Timesheets view section for direct reports
3. Assert that the direct report's submitted timesheets are visible
**Expected Result:** Supervisor can see timesheets belonging to their direct reports. Timesheets from unrelated employees are not accessible.
**Category:** positive
**Status:** automated
**Note:** Stub — requires supervisor role assignment and direct report data setup.
