# Test Case Document — Admin Users API

**Product:** OrangeHRM  
**Layer:** API  
**Module:** Admin — System Users (`/api/v2/admin/users`)

---

## Test Case Index

| ID | Scenario | Type | Status | Script |
|---|---|---|---|---|
| OH-API-001 | GET /admin/users returns 200 with data array | positive | automated | test_orangehrm_admin.py |
| OH-API-002 | Response includes the default "Admin" user | positive | automated | test_orangehrm_admin.py |
| OH-API-003 | GET /admin/users without authentication returns 401 | negative | automated | test_orangehrm_admin.py |
| OH-API-004 | POST /admin/users with weak password returns 400 | negative | automated | test_orangehrm_admin.py |
| OH-API-005 | POST /admin/users with duplicate username "Admin" returns 400 | negative | automated | test_orangehrm_admin.py |
| OH-API-006 | POST /admin/users with missing required field returns 400 | negative | not_automated | — |
| OH-API-007 | GET /admin/users with pagination parameters returns correct page | positive | not_automated | — |
| OH-API-008 | DELETE /admin/users/{id} removes user from list | positive | not_automatable | — |

> 
**Status values:** `automated` = script exists · `not_automated` = not yet scripted · `not_automatable` = human must mark; skipped by script generator

---

## Endpoint Details
- **Base:** `https://opensource-demo.orangehrmlive.com/web/index.php/api/v2`
- **Auth:** Session cookie (Admin role required)

## Endpoints Covered
- `GET /admin/users` — List system users
- `POST /admin/users` — Create a new system user

## Field Validation Rules
- `userRoleId`: integer, 1=Admin 2=ESS, required
- `userName`: string, unique, required
- `password`: min 8 chars, uppercase + number + special char, required
- `status`: "Enabled" or "Disabled", required
- `empNumber`: integer, must reference an existing employee, required

---

## Detailed Test Cases

### OH-API-001 — List System Users Returns 200

**Steps:** GET /admin/users with valid session cookie  
**Expected:** 200, body has `data` array

### OH-API-002 — Response Includes Admin User

**Steps:** GET /admin/users  
**Expected:** At least one user in `data` has `userName == "Admin"`

### OH-API-003 — List Without Auth Returns 401

**Steps:** GET /admin/users without any auth cookie  
**Expected:** 401 Unauthorized

### OH-API-004 — Create User With Weak Password
**Payload:** `{"username": "testuser_weakpwd", "password": "weak", "status": 1, "userRoleId": 2, "empNumber": 1}`  
**Expected:** 400 or 422

### OH-API-005 — Create With Duplicate Username

**Pre-conditions:** Username "Admin" exists  
**Payload:** `{"username": "Admin", "password": "Admin1234!", "status": 1, "userRoleId": 2, "empNumber": 1}`  
**Expected:** 400 or 422

### OH-API-006 — Create With Missing Required Field (not_automated)
**Payload:** Omit `userName` or `empNumber`  
**Expected:** 400 or 422 with field-specific error

### OH-API-007 — Paginated List (not_automated)

**Steps:** GET /admin/users?limit=5&offset=0  
**Expected:** Response limited to 5 records; meta contains total count

### OH-API-008 — Delete User (not_automatable)

**Note:** Destructive on shared demo environment. Deleting the Admin user would break all subsequent tests. Run only on isolated environments with explicit teardown.
