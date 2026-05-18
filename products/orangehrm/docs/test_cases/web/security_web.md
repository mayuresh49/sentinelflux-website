### TC Index

| ID       | Scenario                                  | Type    | Status        | Script   |
|----------|-------------------------------------------|---------|---------------|----------|
| OH-WEB-083 | Validate Username Case Sensitivity         | security| not_automated |          |
| OH-WEB-084 | Account Lock After 5 Failed Login Attempts | security| not_automated |          |
| OH-WEB-085 | Session Expiry After Inactivity Timeout    | security| not_automated |          |
| OH-WEB-086 | Password Complexity for Authentication    | security| not_automated |          |
| OH-WEB-087 | Admin Cannot Delete Own Account           | business| not_automated |          |
| OH-WEB-088 | Add Employee with Valid Data              | positive| not_automated |          |
| OH-WEB-089 | Add Employee with Missing First Name      | negative| not_automated |          |
| OH-WEB-090 | Add Employee with Duplicate Employee ID   | negative| not_automated |          |
| OH-WEB-091 | ESS User Views Own Profile                | positive| not_automated |          |
| OH-WEB-092 | Admin Views All Employee Records          | positive| not_automated |          |
| OH-WEB-093 | Supervisor Views Direct Reports           | positive| not_automated |          |
| OH-WEB-094 | Terminated Employees Hidden from Active Lists | positive| not_automated |          |
| OH-WEB-095 | Leave Request Dates Not in the Past       | negative| not_automated |          |
| OH-WEB-096 | To Date Must Be On or After From Date    | negative| not_automated |          |
| OH-WEB-097 | Leave Cannot be Taken on Non-Working Days | negative| not_automated |          |
| OH-WEB-098 | Sufficient Leave Balance for Request      | negative| not_automated |          |
| OH-WEB-099 | Valid Leave Type Required               | negative| not_automated |          |
| OH-WEB-100 | Approved Leave Can be Cancelled Before Start Date | positive| not_automated |          |
| OH-WEB-101 | Admin/Supervisor Approves Leave           | positive| not_automated |          |
| OH-WEB-102 | Half-Day Leave Allowed for Configured Types | positive| not_automated |          |
| OH-WEB-103 | Leave Entitlement Resets at Start        | positive| not_automated |          |
| OH-WEB-104 | Only Admin Can Create/Edit/Delete Users   | security| not_automated |          |
| OH-WEB-105 | Username Must Be Unique                 | negative| not_automated |          |
| OH-WEB-106 | User Password Complexity                | security| not_automated |          |
| OH-WEB-107 | Each System User Linked to Employee Record | business| not_automated |          |
| OH-WEB-108 | Admin Cannot Change Own Role to ESS       | business| not_automated |          |
| OH-WEB-109 | Disabled Users Cannot Log In             | security| not_automated |          |
| OH-WEB-110 | User Roles Assignment                   | positive| not_automated |          |
| OH-WEB-111 | Only Admin Can Create/Edit/Delete Job Vacancies | security| not_automated |          |
| OH-WEB-112 | Vacancy Name Must Be Unique             | negative| not_automated |          |
| OH-WEB-113 | Job Title References Existing Job Title   | business| not_automated |          |
| OH-WEB-114 | Hiring Manager Must Be Active Employee  | business| not_automated |          |
| OH-WEB-115 | No. of Positions Must Be Positive       | negative| not_automated |          |
| OH-WEB-116 | Candidate First and Last Name Required   | positive| not_automated |          |
| OH-WEB-117 | Candidate Email Valid Format            | positive| not_automated |          |
| OH-WEB-118 | Candidate Resume Upload Type and Size    | negative| not_automated |          |
| OH-WEB-119 | Date of Application Defaults to Today   | positive| not_automated |          |
| OH-WEB-120 | Interview Title Required                | positive| not_automated |          |
| OH-WEB-121 | At Least One Interviewer Assigned       | negative| not_automated |          |
| OH-WEB-122 | Interview Date Required                 | positive| not_automated |          |
| OH-WEB-123 | Candidate Status Transitions            | business| not_automated |          |

### Fields in Scope

| Field               | Type        | Required | Validation Rule                                                                                   |
|---------------------|-------------|----------|-----------------------------------------------------------------------------------------------------|
| employee_firstname  | string      | True     | alphanumeric and spaces, hyphens, apostrophes, min_length: 1, max_length: 30                        |
| employee_lastname   | string      | True     | min_length: 1, max_length: 30                                                                      |
| employee_id         | string      | False    | unique, auto_generated, max_length: 10                                                             |
| username            | string      | True     | alphanumeric and underscores only, min_length: 5, max_length: 40, unique                             |
| password            | string      | True     | min_length: 8, rules: [At least one uppercase letter, At least one lowercase letter, At least one number, At least one special character] |

### OH-WEB-083 — Validate Username Case Sensitivity

**Pre-conditions:**
- User role: Admin
- Starting URL: /security_web/login
- No required data state

**Test Data:**
| Field  | Value          |
|--------|----------------|
| username | Admin          |
| password | admin123       |

**Steps:**
1. Navigate to the exact URL /security_web/login
2. Enter the username "Admin" and password "admin123"
3. Click on the login button

**Expected Result:** The user should be logged in successfully.

**Validation:**
- Check if the homepage or dashboard is loaded.
- Verify that the session cookie contains the HttpOnly flag.

**Category:** security

**Status:** not_automated

### OH-WEB-084 — Account Lock After 5 Failed Login Attempts

**Pre-conditions:**
- User role: Admin
- Starting URL: /security_web/login
- No required data state

**Test Data:**
| Field  | Value          |
|--------|----------------|
| username | admin        |
| password | incorrect123 |

**Steps:**
1. Navigate to the exact URL /security_web/login
2. Enter an incorrect username "admin" and password "incorrect123"
3. Click on the login button five times

**Expected Result:** The account should be locked, and a lockout message should appear.

**Validation:**
- Check if the lockout message is displayed.
- Verify that further login attempts result in failure or different error messages.

**Category:** security

**Status:** not_automated
