# Test Case Document — Leave List Page

**Product:** OrangeHRM  
**Layer:** Web  
**Module:** Leave — Leave List (`/web/index.php/leave/viewLeaveList`)

---

## Test Case Index

| ID | Scenario | Type | Status | Script |
|---|---|---|---|---|
| OH-WEB-026 | Leave list loads with record count on navigation | positive | automated | test_leave.py |
| OH-WEB-027 | Leave list shows record count after search | positive | automated | test_leave.py |
| OH-WEB-028 | Filter by "Pending Approval" status shows results | positive | automated | test_leave.py |
| OH-WEB-029 | Searching a future date range (2099) shows No Records Found | negative | automated | test_leave.py |
| OH-WEB-030 | Date To before Date From returns empty results or zero records | negative | automated | test_leave.py |
| OH-WEB-070 | Filter by leave type narrows results | positive | not_automated | — |
| OH-WEB-071 | Export leave list results to CSV | positive | not_automatable | — |

> **Status values:** `automated` = script exists · `not_automated` = not yet scripted · `not_automatable` = human must mark; skipped by script generator

---

## Page Details
- **URL:** `/web/index.php/leave/viewLeaveList`
- **Fields:** Date From (optional), Date To (optional), Show/Status (dropdown), Search button, Leave request table, Record count

---

## Business Rules
- Date range filter: both dates are optional
- Date To must be >= Date From (enforced by server; demo may not enforce)
- Status filter: Pending Approval, Approved, Rejected, Cancelled

---

## Detailed Test Cases

```
### OH-WEB-026 — Leave List Loads
**Pre-conditions:**
- User Role: Admin
- Starting URL: /web/index.php/dashboard/index
- Required Data State: Authenticated as Admin
**Test Data:**
| Field | Value |
|---|---|
| None | N/A |
**Steps:**
1. Navigate to Leave - Leave List from the Dashboard
**Expected Result:** Page loads; record count element present
**Validation:** Verify that the Leave List page loads successfully and a record count is displayed
**Category:** positive
**Status:** not_automated
```### OH-WEB-027 — Record Count After Search
**Pre-conditions:**
- User Role: Admin/Supervisor/ESS
- Starting URL: /web/index.php/dashboard/index
- Required Data State: User logged in

**Test Data:**
| Field | Value |
|---|---|
| FieldName | Not applicable |

**Steps:**
1. Navigate to Leave List: Click on "Leave" from the main menu, then select "Leave List".
2. Click Search: In the search bar, click on the search icon or press Enter key.

**Expected Result:** Text containing "Record X of Y" is visible in the leave list where X is the current record number and Y is the total count of records matching the search criteria.

**Validation:** Verify that the displayed record count corresponds to the actual count of records matching the search criteria.

**Category:** positive
**Status:** not_automated### OH-WEB-028 — Filter By Pending Status
**Pre-conditions:**
- User Role: Admin
- Starting URL: /web/index.php/admin/viewSystemUsers
- Required Data State: System Users list is displayed

**Test Data:**
| Field | Value |
|---|---|
| Status | Pending Approval |

**Steps:**
1. Navigate to Admin - System Users page
2. Filter the system users by selecting "Pending Approval" from the Status dropdown
3. Check the displayed list of users

**Expected Result:** The displayed list contains system users with pending approval status

**Validation:** Verify that the number of displayed users matches the filtered state

**Category:** positive
**Status:** not_automated### OH-WEB-029 — Future Date Range Shows No Records
**Pre-conditions:**
- Role: Admin
- Starting URL: /web/index.php/api/v2/admin/users (Login and navigate to Admin dashboard if needed)
- Required data state: Current system user is an admin

**Test Data:**
| Field | Value |
|---|---|
| From Date | 2099-01-01 |
| To Date | 2099-12-31 |

**Steps:**
1. Send GET request to /leave/leave-requests with query parameters `from=${From Date}&to=${To Date}`
2. Check response for any leave records within the specified date range

**Expected Result:** No leave records found

**Validation:** Check that the API response contains no records matching the specified date range

**Category:** positive
**Status:** not_automated### OH-WEB-030 — Date To Before Date From
**Pre-conditions:**
- Role: Admin/Supervisor, URL: /web/index.php/leave/viewLeaveList
- Leave Request with Date From and Date To values present in database
**Test Data:**
| Field | Value |
|---|---|
| Date From | 2024-01-01 |
| Date To | 2024-06-30 |
**Steps:**
1. Navigate to Leave List page
2. Filter leave requests with the specified date range
3. Check for records in the filtered list
**Expected Result:** No Records Found or zero count
**Validation:** Verify that no leave request with the specified date range is found
**Category:** positive
**Status:** not_automated### OH-WEB-070 — Filter By Leave Type (not_automated)
**Pre-conditions:**
- User Role: Admin or HR Manager
- Starting URL: /web/index.php/leave/viewLeaveList
- Required Data State: No specific leave type selected in the filter dropdown

**Test Data:**
| Field | Value |
|---|---|
| Leave Type | Recreational Leave (from Knowledge Base) |

**Steps:**
1. Navigate to the Leave List page at /web/index.php/leave/viewLeaveList
2. Select the "Recreational Leave" option from the leave type filter dropdown
3. Click the "Search" button

**Expected Result:** Only records for the "Recreational Leave" type are displayed on the Leave List page

**Validation:** Verify that all displayed records have "Recreational Leave" as their leave type
**Category:** positive
**Status:** not_automated### OH-WEB-071 — Export To CSV (not_automatable)
**Pre-conditions:**
- Admin role, URL: /web/index.php/dashboard/index
- Employees present in the system
**Test Data:**
| Field | Value |
|---|---|
| EmpNumber | Any existing employee's empNumber from the KB |
**Steps:**
1. Navigate to PIM - Employee List: /web/index.php/pim/viewEmployeeList
2. Click on the "Export To CSV" button for the selected employee (EmpNumber)
3. Download and save the CSV file
**Expected Result:**
- The downloaded CSV file contains correct information about the selected employee
**Validation:**
- Verify the contents of the CSV file against the expected data for the specific employee
**Category:** positive
**Status:** not_automated