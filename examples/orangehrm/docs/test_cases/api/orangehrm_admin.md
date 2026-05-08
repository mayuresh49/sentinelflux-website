# Test Case Document — Admin Users API

## Endpoint Details
- Base: `https://opensource-demo.orangehrmlive.com/web/index.php/api/v2`
- Auth: Session cookie (Admin role required for most operations)

## Endpoints Covered
- `GET /admin/users` — List system users
- `POST /admin/users` — Create a new system user

## Test Scenarios

### Positive Tests
1. **[positive]** GET /admin/users returns 200 with data array
2. **[positive]** Response includes the default "Admin" user

### Negative Tests
3. **[negative]** GET /admin/users without authentication returns 401
4. **[negative]** POST /admin/users with weak password returns 400
5. **[negative]** POST /admin/users with duplicate username "Admin" returns 400

## Field Validation Rules
- `userRoleId`: integer, 1=Admin 2=ESS, required
- `userName`: string, unique, required
- `password`: min 8 chars, uppercase + number + special char, required
- `status`: "Enabled" or "Disabled", required
- `empNumber`: integer, must reference an existing employee, required

## Test Case — Create User with Duplicate Username

### Pre-conditions
- Authenticated session as Admin
- Username "Admin" already exists

### Steps
1. POST /admin/users with `userName = "Admin"` and otherwise valid fields

### Expected
- Status 400 — duplicate username error
