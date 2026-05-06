# Test Case Document — Leave API

## Endpoint Details
- Base: `https://opensource-demo.orangehrmlive.com/web/index.php/api/v2`
- Auth: Session cookie (cookie-based, obtained via POST `/auth/validateCredentials`)

## Endpoints Covered
- `GET /leave/leave-types` — List all leave types
- `POST /leave/leave-requests` — Submit a leave request

## Test Scenarios

### Positive Tests
1. **[positive]** GET /leave/leave-types returns 200 with a data array
2. **[positive]** Each leave type item contains `id` and `name` fields

### Negative Tests
3. **[negative]** GET /leave/leave-types without authentication returns 401
4. **[negative]** POST /leave/leave-requests with non-existent leaveTypeId returns 400
5. **[negative]** POST /leave/leave-requests with toDate before fromDate returns 400

## Field Validation Rules
- `leaveTypeId`: integer, must reference an existing leave type
- `fromDate`: string YYYY-MM-DD, required
- `toDate`: string YYYY-MM-DD, required, must be >= fromDate
- `comment`: string, optional

## Test Case — Create Leave Request with Invalid Date Range

### Pre-conditions
- Authenticated session exists
- At least one leave type exists (verify via GET /leave/leave-types first)

### Steps
1. GET /leave/leave-types — extract first valid `id`
2. POST /leave/leave-requests with `fromDate = "2024-06-30"`, `toDate = "2024-01-01"`

### Expected
- Status 400 — date validation error
