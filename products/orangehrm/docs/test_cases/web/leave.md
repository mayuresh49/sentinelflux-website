### TC Index Table

| ID        | Scenario                                       | Type      | Status          | Script |
|-----------|------------------------------------------------|-----------|-----------------|--------|
| OH-WEB-124 | Leave list loads with current period leave requests | positive  | not_automated   |        |
| OH-WEB-125 | Filter by date range narrows results correctly     | positive  | not_automated   |        |
| OH-WEB-126 | Admin can approve a pending leave request         | positive  | not_automated   |        |
| OH-WEB-127 | Admin can reject a pending leave request          | positive  | not_automated   |        |
| OH-WEB-128 | Date To before Date From shows validation or empty results | negative | not_automated   |        |

### Fields in Scope

| Field       | Type     | Required | Validation Rule                                                                 |
|-------------|----------|----------|---------------------------------------------------------------------------------|
| Date From   | date     | optional | -                                                                               |
| Date To     | date     | optional | -                                                                               |
| Show        | text     | optional | -                                                                               |
| Search      | text     | optional | -                                                                               |

### OH-WEB-124 — Leave list loads with current period leave requests

**Pre-conditions:**
- User role: Admin
- Starting URL: /web/index.php/leave/viewLeaveList
- Any required data state: Ensure there are pending leave requests for the current period.

**Test Data:**
| Field | Value |
|-------|-------|
| Date From | -     |
| Date To   | -     |

**Steps:**
1. Navigate to /web/index.php/leave/viewLeaveList.
2. Observe the leave request table without entering any filters (Date From, Date To, Show, Search).
3. Verify that the list displays leave requests for the current period.

**Expected Result:** The leave request table should display leave requests for the current period without filtering applied.

**Validation:**
- Assert that the displayed requests are within the current period.
- Assert that all required fields (Date From, Date To) remain empty or unfiltered.

**Category:** positive

**Status:** not_automated

### OH-WEB-125 — Filter by date range narrows results correctly

**Pre-conditions:**
- User role: Admin
- Starting URL: /web/index.php/leave/viewLeaveList
- Any required data state: Ensure there are leave requests for the selected date range.

**Test Data:**
| Field | Value          |
|-------|----------------|
| Date From | 2023-01-01   |
| Date To   | 2023-01-31   |

**Steps:**
1. Navigate to /web/index.php/leave/viewLeaveList.
2. Enter the Date From as "2023-01-01" and Date To as "2023-01-31".
3. Apply the filter by clicking on the corresponding button or pressing enter.

**Expected Result:** The leave request table should display only the requests that fall within the date range of January 1, 2023 to January 31, 2023.

**Validation:**
- Assert that all displayed requests have dates between "2023-01-01" and "2023-01-31".
- Assert that no requests outside this date range are shown.

**Category:** positive

**Status:** not_automated

### OH-WEB-126 — Admin can approve a pending leave request

**Pre-conditions:**
- User role: Admin
- Starting URL: /web/index.php/leave/viewLeaveList
- Any required data state: Ensure there is at least one pending leave request.

**Test Data:**
| Field | Value          |
|-------|----------------|
| Leave Request ID | 12345      |

**Steps:**
1. Navigate to /web/index.php/leave/viewLeaveList.
2. Locate a pending leave request with ID "12345".
3. Click on the approve button for this request.

**Expected Result:** The status of the leave request should change from "Pending" to "Approved". A confirmation message should be displayed indicating successful approval.

**Validation:**
- Assert that the status of the request with ID "12345" changes to "Approved".
- Assert that a success message "Leave request approved successfully." is displayed.

**Category:** positive

**Status:** not_automated

### OH-WEB-127 — Admin can reject a pending leave request

**Pre-conditions:**
- User role: Admin
- Starting URL: /web/index.php/leave/viewLeaveList
- Any required data state: Ensure there is at least one pending leave request.

**Test Data:**
| Field | Value          |
|-------|----------------|
| Leave Request ID | 12345      |

**Steps:**
1. Navigate to /web/index.php/leave/viewLeaveList.
2. Locate a pending leave request with ID "12345".
3. Click on the reject button for this request.

**Expected Result:** The status of the leave request should change from "Pending" to "Rejected". A confirmation message should be displayed indicating successful rejection.

**Validation:**
- Assert that the status of the request with ID "12345" changes to "Rejected".
- Assert that a success message "Leave request rejected successfully." is displayed.

**Category:** positive

**Status:** not_automated

### OH-WEB-128 — Date To before Date From shows validation or empty results

**Pre-conditions:**
- User role: Admin
- Starting URL: /web/index.php/leave/viewLeaveList
- Any required data state: No specific data state needed.

**Test Data:**
| Field | Value          |
|-------|----------------|
| Date From | 2023-01-31   |
| Date To   | 2023-01-01   |

**Steps:**
1. Navigate to /web/index.php/leave/viewLeaveList.
2. Enter the Date From as "2023-01-31" and Date To as "2023-01-01".
3. Apply the filter by clicking on the corresponding button or pressing enter.

**Expected Result:** The leave request table should either display an error message indicating that the date range is invalid or should remain empty, showing no results.

**Validation:**
- Assert that either a validation error message "Date To must be on or after Date From" is displayed.
- Assert that if there are no valid requests, the table remains empty.

**Category:** negative

**Status:** not_automated
