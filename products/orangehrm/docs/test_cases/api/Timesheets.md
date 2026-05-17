```markdown
# TC_ID — Retrieve All Timesheets (ALL)
**Pre-conditions:**
- Auth state: Authenticated as Admin via POST /auth/login
- Any prerequisite data: Employees with timesheet records exist in the system

**Request:**
- Method: GET
- Path: /api/v2/timesheets
- Headers:
    - Authorization: Bearer {access_token}

**Steps:**
1. Authenticate and obtain access token using exact credentials from KB
2. Send GET /api/v2/timesheets request with the obtained access token in the Authorization header
3. Assert response status code is 200

**Expected Result:** HTTP 200 — The response body must contain an array of timesheet objects, each with fields: empNumber, firstName, lastName, timesheetId, weekStartDate, weekEndDate, hoursWorked, and approved (true/false).

**Validation:**
- Response field assertions:
    - response.data is an array
    - length(response.data) > 0
    - for timesheet in response.data:
        - timesheet has all required fields mentioned above
    - Additional validation can be added as needed to check the structure and values of each timesheet object

**Category:** positive | edge
**Status:** not_automated

---

# TC_ID — Retrieve Timesheets with Invalid Access Token (ALL)
**Pre-conditions:**
- Auth state: Authenticated as Admin via POST /auth/login but with an expired access token or incorrect access token
- Any prerequisite data: Employees with timesheet records exist in the system

**Request:**
- Method: GET
- Path: /api/v2/timesheets
- Headers:
    - Authorization: Bearer {invalid_access_token}

**Steps:**
1. Authenticate and obtain an invalid access token using exact credentials from KB (e.g., expired or incorrect)
2. Send GET /api/v2/timesheets request with the obtained invalid access token in the Authorization header
3. Assert response status code is 401 or 403

**Expected Result:** HTTP 401 (Unauthorized) or HTTP 403 (Forbidden) — The response body must contain an error message indicating that authentication has failed, and/or access to the requested resource is denied.

**Validation:**
- Response field assertions:
    - response.status == "UNAUTHORIZED" or response.status == "FORBIDDEN"
    - response.message contains an error message indicating that authentication has failed, and/or access to the requested resource is denied

**Category:** negative | security
**Status:** not_automated
```