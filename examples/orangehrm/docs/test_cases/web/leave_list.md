# Test Case Document — Leave List Page

## Page Details
- Page: Leave — Leave List (`/web/index.php/leave/viewLeaveList`)
- Description: Admin view of all leave requests with date range and status filters

## Fields
- Date From (optional)
- Date To (optional)
- Show / Status (optional dropdown)
- Search (optional)
- Leave request table (optional)
- Record count (optional)

## Test Scenarios

### Positive Tests
1. **[positive]** Leave list loads with record count on navigation
2. **[positive]** Filter by "Pending Approval" status shows only pending items
3. **[positive]** Record count text is present after page load

### Negative Tests
4. **[negative]** Searching a future date range (2099) shows No Records Found
5. **[negative]** Date To before Date From returns empty results or zero records

## Test Case — Leave List Loads

### Pre-conditions
- User is authenticated as Admin

### Steps
1. Navigate to `/web/index.php/leave/viewLeaveList`

### Expected
- Page loads; record count text is visible

## Test Case — Filter by Status

### Pre-conditions
- User is authenticated as Admin
- Leave requests with "Pending Approval" status exist on demo site

### Steps
1. Navigate to leave list
2. Select "Pending Approval" from the Show dropdown
3. Click Search

### Expected
- Results table updates; record count reflects filtered set
