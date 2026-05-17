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

### OH-WEB-026 — Leave List Loads
**Pre-conditions:** Authenticated as Admin  
**Steps:** Navigate to Leave — Leave List  
**Expected:** Page loads; record count element present

### OH-WEB-027 — Record Count After Search
**Steps:** Navigate to leave list, click Search  
**Expected:** Text containing "Record" is visible

### OH-WEB-028 — Filter By Pending Status
**Steps:** Select "Pending Approval" from Status dropdown, click Search  
**Expected:** Results are non-empty OR record count reflects filtered state

### OH-WEB-029 — Future Date Range Shows No Records
**Test Data:** Date From = 2099-01-01, Date To = 2099-12-31  
**Steps:** Enter future dates, click Search  
**Expected:** No Records Found

### OH-WEB-030 — Date To Before Date From
**Test Data:** Date From = 2024-06-30, Date To = 2024-01-01  
**Steps:** Set inverted date range, click Search  
**Expected:** No Records Found or zero count  
**Note:** xfail on demo — demo does not enforce date-range order

### OH-WEB-070 — Filter By Leave Type (not_automated)
**Steps:** Select a specific leave type from filter, search  
**Expected:** Only records matching that leave type are shown

### OH-WEB-071 — Export To CSV (not_automatable)
**Note:** Requires verifying downloaded file contents. Browser download handling is environment-specific and unreliable in headless CI.
