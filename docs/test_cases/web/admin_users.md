# Test Case Document — Admin System Users Page

## Page Details
- Page: Admin — System Users (`/web/index.php/admin/viewSystemUsers`)
- Description: Manage system user accounts — list, search, create, and delete

## Fields (List page)
- Username (optional filter)
- User Role (optional dropdown filter: Admin / ESS)
- Employee Name (optional filter)
- Status (optional dropdown filter)
- Search (optional)
- Add (optional)
- System Users table (optional)
- Record count (optional)

## Fields (Add User form)
- User Role (required)
- Employee Name (required, autocomplete)
- Status (required)
- Username (required)
- Password (required, min 8 chars, uppercase + number + special)
- Confirm Password (required)

## Test Scenarios

### Positive Tests
1. **[positive]** System users list loads with record count
2. **[positive]** Search by username "Admin" returns at least one result
3. **[positive]** Cancel on add-user form returns to users list without saving

### Negative Tests
4. **[negative]** Search with non-existent username shows No Records Found
5. **[negative]** Save add-user form without username shows required field error
6. **[negative]** Save add-user form without password shows required field error

## Business Rules
- Username must be unique across all system users
- Password: min 8 chars, at least one uppercase, one number, one special character
- User Role: Admin (full access) or ESS (employee self-service)
- Employee Name must be an existing employee in the PIM module
- Admin cannot delete their own account

## Test Case — Add User — Missing Required Fields

### Pre-conditions
- User is authenticated as Admin
- At least one employee exists in PIM

### Steps
1. Navigate to add user form
2. Select User Role = ESS
3. Fill Employee Name, Status, Password, Confirm Password — leave Username blank
4. Click Save

### Expected
- Validation error shown for Username field; user is not created
