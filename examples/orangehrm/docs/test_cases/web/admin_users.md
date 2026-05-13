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
| OH-WEB-026 | Create user with weak password shows password policy error | negative | not_automated | — |
| OH-WEB-027 | Create user with duplicate username shows conflict error | negative | not_automatable | — |
| OH-WEB-028 | Delete user removes them from list | positive | not_automatable | — |

> **Status values:** `automated` = script exists · `not_automated` = not yet scripted · `not_automatable` = human must mark; skipped by script generator

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
**Pre-conditions:** Authenticated as Admin  
**Steps:** Navigate to Admin > System Users  
**Expected:** Page loads; user list visible

### OH-WEB-020 — Record Count Shown
**Steps:** Navigate to System Users  
**Expected:** Text containing "Record" is visible

### OH-WEB-021 — Search By Username
**Test Data:** Username filter = "Admin"  
**Steps:** Enter "Admin" in username filter, search  
**Expected:** Record count text visible; at least one result

### OH-WEB-022 — Search Non-Existent Username
**Test Data:** Username = "ZZZnonexistentXXX999"  
**Steps:** Search for non-existent username  
**Expected:** No Records Found shown

### OH-WEB-023 — Cancel Returns To List
**Steps:** Navigate to Add User form, click Cancel  
**Expected:** Returns to System Users list

### OH-WEB-024 — Save Without Username
**Steps:** Fill all add-user fields except Username, click Save  
**Expected:** Validation error for Username field  
**Note:** xfail on demo — employee lookup may time out

### OH-WEB-025 — Save Without Password
**Steps:** Fill all add-user fields except Password, click Save  
**Expected:** Validation error for Password field

### OH-WEB-026 — Weak Password (not_automated)
**Steps:** Fill all fields with password = "weak", click Save  
**Expected:** Password policy error shown

### OH-WEB-027 — Duplicate Username (not_automatable)
**Note:** Creates a real user on the demo system. Risk of polluting shared state. Run only on isolated environments with cleanup.

### OH-WEB-028 — Delete User (not_automatable)
**Note:** Destructive; deleting the Admin user on demo would break all tests. Run only on isolated environments with a known test user.
