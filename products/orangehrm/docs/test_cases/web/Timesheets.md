```markdown
# Test Case Document for Timesheets Web Feature

## TC_ID — Employee Timesheet Submission with Valid Data (Positive Scenario)
**Pre-conditions:**
- User role: ESS User
- Starting URL: `/Timesheets`
- Any required data state: An active and existing employee record linked to the ESS user's system account.
**Test Data:**
| Field | Value |
|---|---|
| employee_firstname | John |
| employee_lastname | Doe |
| timesheet_date | YYYY-MM-DD (today's date) |
| hours_worked | 8 |
**Steps:**
1. Navigate to the Timesheets page at `/Timesheets`.
2. Input the employee first name, last name, timesheet date, and hours worked.
3. Submit the timesheet for approval.
**Expected Result:** The timesheet is successfully submitted and saved in the system. An approval message appears with the option to view the submitted timesheet.
**Validation:** Check that the employee's timesheet record contains the correct information, including the submitted hours worked for the specified date. Verify that the timesheet status changes from 'Pending' to 'Approval Pending'.
**Category:** positive
**Status:** not_automated

## TC_ID — Employee Timesheet Submission with Incomplete Data (Negative Scenario)
**Pre-conditions:**
- User role: ESS User
- Starting URL: `/Timesheets`
- Any required data state: An active and existing employee record linked to the ESS user's system account.
**Test Data:**
| Field | Value |
|---|---|
| employee_firstname | John |
| timesheet_date | YYYY-MM-DD (today's date) |
**Steps:**
1. Navigate to the Timesheets page at `/Timesheets`.
2. Input the employee first name and timesheet date but leave the hours worked field empty.
3. Submit the timesheet for approval.
**Expected Result:** An error message appears informing the user that all fields are required. The submitted timesheet is not saved, and the user is prompted to correct the missing data.
**Validation:** Check that no changes have been made to the employee's timesheet record or any other records in the system. Verify that the error message clearly explains which field(s) are missing data.
**Category:** negative
**Status:** not_automated

## TC_ID — Supervisor Approval of Timesheets (Positive Scenario)
**Pre-conditions:**
- User role: Supervisor
- Starting URL: `/Timesheets`
- Any required data state: An active and existing employee record linked to the ESS user's system account, and a submitted timesheet awaiting approval by the supervisor.
**Test Data:**
| Field | Value |
|---|---|
| timesheet_id | Auto-generated ID of the pending timesheet |
**Steps:**
1. Navigate to the Timesheets page at `/Timesheets`.
2. Locate and select the pending timesheet for approval.
3. Approve the timesheet.
**Expected Result:** The timesheet is successfully approved, and its status changes from 'Approval Pending' to 'Approved'. A success message appears confirming the approval, and the approved timesheet can be viewed.
**Validation:** Check that the employee's timesheet record contains the correct information, including the approved hours worked for the specified date. Verify that the timesheet status changes from 'Pending' to 'Approved', and no further action is required by the employee or supervisor.
**Category:** positive
**Status:** not_automated
```