# Test Case Document — Admin System Users Page

**Product:** OrangeHRM  
**Layer:** Web  
**Module:** Admin — System Users (`/web/index.php/admin/viewSystemUsers`)

---

## Test Case Index

| ID | Scenario | Type | Status | Script |
|---|---|---|---|---|
| OH-WEB-019 | System users list loads with record count | positive | automated | test_admin_users.py |
| OH-WEB-020 | User list shows record count text | positive | automated | test_admin_users.py |
| OH-WEB-021 | Search by username "Admin" returns at least one result | positive | automated | test_admin_users.py |
| OH-WEB-022 | Search with non-existent username shows No Records Found | negative | automated | test_admin_users.py |
| OH-WEB-023 | Cancel on add-user form returns to users list without saving | positive | automated | test_admin_users.py |
| OH-WEB-024 | Save add-user form without username shows required field error | negative | automated | test_admin_users.py |
| OH-WEB-025 | Save add-user form without password shows required field error | negative | automated | test_admin_users.py |
| OH-WEB-067 | Create user with weak password shows password policy error | negative | not_automated | — |
| OH-WEB-068 | Create user with duplicate username shows conflict error | negative | not_automatable | — |
| OH-WEB-069 | Delete user removes them from list | positive | not_automatable | — |

> 
**Status values:** `automated` = script exists · `not_automated` = not yet scripted · `not_automatable` = human must mark; skipped by script generator

---

## Page Details

### List Page
- **URL:** `/web/index.php/admin/viewSystemUsers`
- **Fields:** Username (filter), User Role (dropdown), Employee Name (filter), Status (dropdown), Search, Add, System Users table, Record count

### Add User Form
- **Fields:**
  - User Role (required, Admin/ESS)
  - Employee Name (required, autocomplete)
  - Status (required, Enabled/Disabled)
  - Username (required, unique)
  - Password (required, min 8 chars, uppercase + number + special)
  - Confirm Password (required)

---

## Business Rules
- Username must be unique across all system users
- Password: min 8 chars, at least one uppercase, one number, one special character
- User Role: Admin (full access) or ESS (employee self-service)
- Employee Name must be an existing employee in the PIM module
- Admin cannot delete their own account

---

## Detailed Test Cases

### OH-WEB-019 — User List Loads

**Pre-conditions:**
- Role: Admin
- Starting URL: /web/index.php/admin/viewSystemUsers
- Required data state: Authenticated user

**Test Data:**
| Field | Value |
|---|---|
| User Role | Admin |

**Steps:**
1. Navigate to Admin > System Users
2. Verify that the user is authenticated and can access the page

**Expected Result:** The User List is visible on the page

**Validation:** Assert that the User List is displayed without any errors

**Category:** positive

**Status:** not_automated

### OH-WEB-020 — Record Count Shown

**Pre-conditions:**
- User Role: Admin
- Starting URL: /web/index.php/admin/viewSystemUsers
- Required Data State: System users are present in the system

**Test Data:**
| Field | Value |
|---|---|
| - | - |

**Steps:**
1. Navigate to Admin > System Users
2. Verify that the page displays a count of the number of system users
3. Check if the count matches the actual number of system users in the system

**Expected Result:** The text containing "Record" is visible and corresponds to the actual number of system users

**Validation:** Verify that the displayed count matches the actual number of system users in the system

**Category:** positive

**Status:** not_automated

### OH-WEB-021 — Search By Username

**Pre-conditions:**
- Role: Admin
- Starting URL: /web/index.php/auth/login (Login Page)
- Session created and logged in as an Admin

**Test Data:**
| Field | Value |
|---|---|
| Filter | "Admin" |

**Steps:**
1. Navigate to Recruitment - Job Vacancies: /web/index.php/recruitment/viewJobVacancy
2. Click on the Search Bar and enter "Admin"
3. Click on the Search Button

**Expected Result:** Record count text visible; at least one result displayed

**Validation:** Verify that the search results contain at least one record with username equal to "Admin"

**Category:** positive

**Status:** not_automated

### OH-WEB-022 — Search Non-Existent Username

**Pre-conditions:**
- User Role: Admin or ESS user with appropriate privileges
- Starting URL: /web/index.php/auth/login (assuming the user is not already logged in)
- Required Data State: Authenticated Admin or ESS user

**Test Data:**
| Field | Value |
|---|---|
| Username | ZZZnonexistentXXX999 |

**Steps:**
1. Login with valid credentials
2. Navigate to /web/index.php/admin/viewSystemUsers or /web/index.php/pim/viewEmployeeList (depending on user role)
3. Enter ZZZnonexistentXXX999 in the search field and click Search

**Expected Result:** No Records Found message displayed

**Validation:** Verify that no records are shown with the entered username

**Category:** positive

**Status:** not_automated

### OH-WEB-023 — Cancel Returns To List

**Pre-conditions:**
- User Role: Admin
- Starting URL: /web/index.php/admin/viewSystemUsers
- Required Data State: No specific data state required

**Test Data:**
| Field | Value |
|---|---|
| User Role | Admin |

**Steps:**
1. Navigate to the System Users page at "/web/index.php/admin/viewSystemUsers"
2. Click on "Cancel" while viewing the Add User form

**Expected Result:** The user is redirected to the System Users list ("/web/index.php/admin/viewSystemUsers")

**Validation:** Verify that the System Users list is displayed, and the cancelled user is not present in the list

**Category:** positive

**Status:** not_automated

### OH-WEB-024 — Save Without Username

**Pre-conditions:**
- Role: Admin, Starting URL: /web/index.php/admin/viewSystemUsers, Required Data State: Username not provided

**Test Data:**
| Field | Value |
|---|---|
| First Name | any valid value (1-30 chars) |
| Last Name | any valid value (1-30 chars) |
| Middle Name | optional value (max 30 chars) |
| Employee ID | optional value |
| Password | any complex password (min 8 chars, uppercase, lowercase, number, special char) |

**Steps:**
1. Navigate to /web/index.php/admin/viewSystemUsers
2. Click "Add New User"
3. Fill all fields except Username and click "Save"

**Expected Result:** Validation error for the Username field

**Validation:** Check that an error message appears for the Username field

**Category:** positive

**Status:** not_automated

### OH-WEB-025 — Save Without Password

**Pre-conditions:**
- Role: Admin, Starting URL: /web/index.php/admin/viewSystemUsers, Required data state: First Name, Last Name, Middle Name, Employee ID (optional), Username, Email

**Test Data:**
| Field | Value |
|---|---|
| Password | left blank |

**Steps:**
1. Navigate to Admin - System Users page
2. Click Add New User
3. Fill in all required fields except for Password
4. Click Save

**Expected Result:** Validation error for Password field appears

**Validation:** Error message displayed for Password field

**Category:** positive

**Status:** not_automated

### OH-WEB-067 — Weak Password (not_automated)

**Pre-conditions:**
- Role: Admin/ESS
- Starting URL: https://opensource-demo.orangehrmlive.com/web/index.php/api/v2
- Account created with password complexity met

**Test Data:**
| Field | Value |
|---|---|
| Password | weak |

**Steps:**
1. Navigate to POST /auth/login endpoint and authenticate user
2. Call PUT /pim/employees/{empNumber}/personal-details endpoint with new password field set to "weak"
3. Check response for password policy error

**Expected Result:** Password policy error shown

**Validation:** Check response status code (4xx) and error message contains "Weak Password"

**Category:** positive

**Status:** not_automated

### OH-WEB-068 — Duplicate Username (not_automatable)

**Pre-conditions:**
- Role: Admin, Starting URL: /web/index.php/admin/viewSystemUsers, Required Data State: Existing unique username

**Test Data:**
| Field | Value |
|---|---|
| Username | Existing unique username |

**Steps:**
1. Navigate to Admin - System Users page
2. Click on "Add New User" button
3. Enter the existing unique username in the "Username" field
4. Fill out other required fields with valid values
5. Click on "Save" button

**Expected Result:** An error message is displayed indicating that the username already exists.

**Validation:** Verify that the error message appears and the new user is not created.

**Category:** positive

**Status:** not_automated

### OH-WEB-069 — Delete User (not_automatable)

**Pre-conditions:**
- Role: Admin
- Starting URL: /web/index.php/admin/viewSystemUsers
- Required Data State: Known Test User with valid credentials

**Test Data:**
| Field | Value |
|---|---|
| Username | exact value from KB |
| Password | exact value from KB |

**Steps:**
1. Navigate to the Admin - System Users page.
2. Enter the known test user's credentials and click 'Login'.
3. Locate the test user in the list of system users.
4. Click on the 'Delete' button next to the test user.
5. Confirm the deletion by clicking 'OK' on the confirmation dialog.

**Expected Result:** The test user is deleted from the system and the list updates accordingly. A success message appears indicating that the user has been successfully deleted.

**Validation:** Verify that the test user no longer exists in the system and the list does not contain the deleted user.

**Category:** positive

**Status:** not_automated
