# Test Case Document — PIM Employee List Page

**Product:** OrangeHRM  
**Layer:** Web  
**Module:** PIM — Employee List (`/web/index.php/pim/viewEmployeeList`)

---

## Test Case Index

| ID | Scenario | Type | Status | Script |
|---|---|---|---|---|
| OH-WEB-009 | Employee list loads with record count on navigation | positive | automated | test_pim_employee.py |
| OH-WEB-010 | Add employee with required fields only (first + last name) | positive | automated | test_pim_employee.py |
| OH-WEB-011 | Add employee with all four fields (including middle name and ID) | positive | automated | test_pim_employee.py |
| OH-WEB-012 | Save add employee form without firstname shows validation error | negative | automated | test_pim_employee.py |
| OH-WEB-013 | Save add employee form without lastname shows validation error | negative | automated | test_pim_employee.py |
| OH-WEB-014 | Firstname exceeding 30 chars shows validation error | negative | automated | test_pim_employee.py |
| OH-WEB-015 | Cancel on add employee form returns to list without saving | positive | automated | test_pim_employee.py |
| OH-WEB-016 | Search by name "Admin" filters results | positive | automated | test_pim_employee.py |
| OH-WEB-017 | Search with non-existent name shows No Records Found | negative | automated | test_pim_employee.py |
| OH-WEB-018 | Add employee with parametrized names (Alice/Smith, Bob/Jones) | positive | automated | test_pim_employee.py |
| OH-WEB-062 | Search by Employee ID filters to exact match | positive | not_automated | — |
| OH-WEB-063 | Record count updates after search | positive | not_automated | — |
| OH-WEB-064 | Search is case-insensitive | edge | not_automated | — |
| OH-WEB-065 | Partial name search returns all matching employees | edge | not_automated | — |
| OH-WEB-066 | Duplicate Employee ID shows validation error | negative | not_automatable | — |

> **Status values:** `automated` = script exists · `not_automated` = not yet scripted · `not_automatable` = human must mark; skipped by script generator

---

## Page Details

### List Page
- **URL:** `/web/index.php/pim/viewEmployeeList`
- **Fields:** Employee Name (filter), Employee Id (filter), Search button, Add button, Employee table, Record count, Row checkbox

### Add Employee Form
- **URL:** `/web/index.php/pim/addEmployee`
- **Fields:**
  - First Name (required, max 30 chars)
  - Middle Name (optional)
  - Last Name (required)
  - Employee ID (optional, auto-generated if blank)

---

## Business Rules
- First Name and Last Name are required
- First Name max 30 characters
- Employee ID must be unique if specified
- All four Add Employee fields are the ONLY fields on that form

---

## Detailed Test Cases

### OH-WEB-009 — Employee List Loads
**Pre-conditions:**
- User Role: Admin
- Starting URL: /web/index.php/dashboard/index
- Required Data State: Authenticated as Admin

**Test Data:**
| Field | Value |
|---|---|
| None | - |

**Steps:**
1. Navigate to PIM - Employee List: /web/index.php/pim/viewEmployeeList
2. Click on "Employee List" link from the Dashboard

**Expected Result:**
- Page loads
- "Records Found" text visible on UI

**Validation:**
- Verify that the page loads without any errors
- Verify that the "Records Found" text is displayed on the UI### OH-WEB-010 — Add Employee Required Fields Only
**Pre-conditions:**
- User Role: Admin/Supervisor, Starting URL: /web/index.php/pim/addEmployee, Required Data State: None

**Test Data:**
| Field | Value |
|---|---|
| First Name | Test |
| Last Name | User |

**Steps:**
1. Navigate to PIM - Add Employee page
2. Fill in the required fields with the provided test data
3. Save the employee record

**Expected Result:** Success toast or profile page shown

**Validation:** Verify that the employee record is saved with the provided First Name and Last Name

**Category:** positive
**Status:** not_automated### OH-WEB-011 — Add Employee All Fields
**Pre-conditions:**
- User Role: Admin, Starting URL: /web/index.php/pim/addEmployee, Required Data State: No data required
**Test Data:**
| Field | Value |
|---|---|
| First Name | John |
| Middle Name | Robert |
| Last Name | Doe |
**Steps:**
1. Navigate to PIM - Add Employee page
2. Fill in the First Name, Middle Name, and Last Name fields with the provided values
3. Click the Save button
**Expected Result:** Success toast or profile page shown
**Validation:** Verify that the employee record is saved correctly with the provided values
**Category:** positive
**Status:** not_automated### OH-WEB-012 — Save Without Firstname
**Pre-conditions:**
- User Role: Admin/ESS
- Starting URL: /web/index.php/pim/addEmployee
- Required Data State: Last Name filled

**Test Data:**
| Field | Value |
|---|---|
| First Name | (empty) |

**Steps:**
1. Navigate to the Add Employee page
2. Fill in Last Name and save without entering a First Name
3. Verify validation error for First Name field

**Expected Result:** Validation error message displayed for the First Name field

**Validation:** First Name field is not empty after saving

**Category:** positive
**Status:** not_automated### OH-WEB-013 — Save Without Lastname
**Pre-conditions:**
- User Role: Admin/ESS
- Starting URL: /web/index.php/pim/addEmployee
- Required Data State: First Name is provided

**Test Data:**
| Field | Value |
|---|---|
| First Name | value from KB (as per Add Employee form) |
| Last Name | empty |

**Steps:**
1. Navigate to PIM - Add Employee page
2. Fill in the First Name and leave the Last Name field empty
3. Click on the Save button

**Expected Result:** Validation error for Last Name field

**Validation:** Check that an error message appears for the Last Name field

**Category:** positive
**Status:** not_automated### OH-WEB-014 — Firstname Exceeding 30 Characters
**Pre-conditions:**
- Role: Admin/ESS, URL: /web/index.php/pim/addEmployee, Required Data State: None

**Test Data:**
| Field | Value |
|---|---|
| First Name | 31 × "A"   |
| Last Name | Any valid value (1-30 chars) |

**Steps:**
1. Navigate to PIM - Add Employee: /web/index.php/pim/addEmployee
2. Fill in First Name and Last Name
3. Click Save

**Expected Result:** Validation error shown for First Name exceeding 30 characters

**Validation:** Verify that the validation error message is displayed

**Category:** positive
**Status:** not_automated### OH-WEB-015 — Cancel Returns To List
**Pre-conditions:**
- User Role: Admin/ESS
- Starting URL: /web/index.php/recruitment/addJobVacancy
- Required Data State: Empty form

**Test Data:**
| Field | Value |
|---|---|
| Vacancy Name | N/A (not applicable since the test case is for cancelation) |

**Steps:**
1. Navigate to Recruitment - Add Vacancy
2. Fill in any required fields and click 'Cancel'
3. Verify that the user is returned to the Employee List

**Expected Result:** The user is returned to the Employee List; no new vacancy was created

**Validation:** Check that the Recruitment - Add Vacancy page is not displayed anymore and the employee list is visible, indicating that the cancel action worked as intended.### OH-WEB-016 — Search By Name
**Pre-conditions:**
- User Role: Admin
- Starting URL: /web/index.php/dashboard/index
- Required Data State: Login successful

**Test Data:**
| Field | Value |
|---|---|
| Search Query | "Admin" |

**Steps:**
1. Navigate to Recruitment - Job Vacancies page: /web/index.php/recruitment/viewJobVacancy
2. Enter the search query "Admin" in the search bar and click 'Search'
3. Verify the number of job vacancies listed

**Expected Result:** The search should return a list of job vacancies associated with Admins

**Validation:** Check if the list contains at least one job vacancy where the hiring manager is an Admin user

**Category:** positive
**Status:** not_automated```
### OH-WEB-017 — Search Non-Existent Name
**Pre-conditions:**
- User Role: Admin
- Starting URL: /web/index.php/recruitment/viewCandidates
- Required Data State: No specific candidate exists with name "ZZZnonexistentXXX"

**Test Data:**
| Field | Value |
|---|---|
| Search Input | ZZZnonexistentXXX |

**Steps:**
1. Navigate to the Recruitment - Candidates page.
2. Enter "ZZZnonexistentXXX" in the search bar and click 'Search'.
3. Verify that no candidate records are displayed.

**Expected Result:** No Records Found message is displayed.

**Validation:** Check that the search results do not contain any candidates with name "ZZZnonexistentXXX".

**Category:** positive
**Status:** not_automated
```### OH-WEB-018 — Add Employee Parametrized
**Pre-conditions:**
- (ESS or Admin role, /web/index.php/auth/login, authenticated session)
- (Admin role, /web/index.php/pim/addEmployee, empty employee list)

**Test Data:**
| Field | Value |
|---|---|
| First Name | Alice |
| Last Name | Smith |

**Steps:**
1. Navigate to Login Page (/web/index.php/auth/login) and authenticate using valid credentials.
2. Navigate to PIM - Add Employee (/web/index.php/pim/addEmployee).
3. Enter First Name as Alice, Last Name as Smith, and click Save.
4. Verify that the employee is added successfully with the provided details.

**Expected Result:** Success message appears for adding employee.

**Validation:** Check that the employee record exists with correct data in the PIM - Employee List (/web/index.php/pim/viewEmployeeList).

**Category:** positive
**Status:** not_automated### OH-WEB-066 — Duplicate Employee ID (not_automatable)
**Pre-conditions:**
- User Role: Admin
- Starting URL: /web/index.php/pim/addEmployee
- Required Data State: Existing Employee ID from Knowledge Base

**Test Data:**
| Field | Value |
|---|---|
| Employee ID | Existing Employee ID from Knowledge Base |

**Steps:**
1. Navigate to /web/index.php/pim/addEmployee
2. Enter the existing Employee ID in the 'Employee ID' field and complete the form with valid data
3. Click 'Save'

**Expected Result:** An error message is displayed indicating that the entered Employee ID already exists

**Validation:** Verify that the error message appears and the employee record remains unchanged

**Category:** positive
**Status:** not_automated