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
| OH-WEB-019 | Search by Employee ID filters to exact match | positive | not_automated | — |
| OH-WEB-020 | Record count updates after search | positive | not_automated | — |
| OH-WEB-021 | Search is case-insensitive | edge | not_automated | — |
| OH-WEB-022 | Partial name search returns all matching employees | edge | not_automated | — |
| OH-WEB-023 | Duplicate Employee ID shows validation error | negative | not_automatable | — |

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
**Pre-conditions:** Authenticated as Admin  
**Steps:** Navigate to Employee List  
**Expected:** Page loads; "Records Found" text visible on ui

### OH-WEB-010 — Add Employee Required Fields Only
**Steps:** Navigate to Add, fill First Name="Test", Last Name="User", save  
**Expected:** Success toast or profile page shown

### OH-WEB-011 — Add Employee All Fields
**Test Data:** First="John", Middle="Robert", Last="Doe", ID=EMP-{random}  
**Steps:** Fill all four fields, save  
**Expected:** Success toast or profile page shown

### OH-WEB-012 — Save Without Firstname
**Steps:** Fill Last Name only, click Save  
**Expected:** Validation error for First Name field

### OH-WEB-013 — Save Without Lastname
**Steps:** Fill First Name only, click Save  
**Expected:** Validation error for Last Name field

### OH-WEB-014 — Firstname Exceeding 30 Characters
**Test Data:** First Name = 31 × "A"  
**Steps:** Fill oversized name, fill Last Name, click Save  
**Expected:** Validation error shown

### OH-WEB-015 — Cancel Returns To List
**Steps:** Navigate to Add, fill name, click Cancel  
**Expected:** Returned to Employee List; employee was not saved

### OH-WEB-016 — Search By Name
**Steps:** Navigate to list, search "Admin"  
**Expected:** "Records Found" text visible (filtered results)

### OH-WEB-017 — Search Non-Existent Name
**Steps:** Search "ZZZnonexistentXXX"  
**Expected:** No Records Found  
**Note:** xfail on demo — shared data may produce false hits

### OH-WEB-018 — Add Employee Parametrized
**Test Data:** [("Alice", "Smith"), ("Bob", "Jones")]  
**Steps:** Add each employee, save  
**Expected:** Success for each data set

### OH-WEB-023 — Duplicate Employee ID (not_automatable)
**Note:** Requires knowing a pre-existing Employee ID on the demo system, which changes between test runs. Recommend manual verification.
