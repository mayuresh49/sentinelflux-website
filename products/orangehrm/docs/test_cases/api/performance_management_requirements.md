# Endpoint Scope: /performance/* (Performance Management Module)

## Endpoints in Scope
- `POST /performance/configure/kpi`
- `PUT /performance/configure/kpi/assign`
- `POST /performance/trackers`
- `POST /performance/reviews`

## Test Cases

| ID | Scenario | Type | Status | Script |
|---|---|---|---|---|
| OH-API-029 | Configure KPIs — valid payload | positive | not_automated | test_performance_management_requirements.py |
| OH-API-030 | Configure KPIs — missing required field | negative | not_automated | test_performance_management_requirements.py |
| OH-API-031 | Configure KPIs — unauthorized | negative | not_automated | test_performance_management_requirements.py |
| OH-API-032 | Assign KPIs by Job Title — valid payload | positive | not_automated | test_performance_management_requirements.py |
| OH-API-033 | Assign KPIs by Job Title — invalid jobTitleId | negative | not_automated | test_performance_management_requirements.py |
| OH-API-034 | Create Performance Tracker — valid payload | positive | not_automated | test_performance_management_requirements.py |
| OH-API-035 | Create Performance Tracker — missing employeeId | negative | not_automated | test_performance_management_requirements.py |
| OH-API-036 | Create Performance Review — valid payload | positive | not_automated | test_performance_management_requirements.py |
| OH-API-037 | Create Performance Review — bad request (missing kpiId) | negative | not_automated | test_performance_management_requirements.py |

---

### OH-API-029 — Configure KPIs — valid payload (positive)

**Pre-conditions:**
- Auth state: "Authenticated as Admin via POST /auth/login"
- At least one Job Title exists in the system

**Test Data:**
- `jobTitleId`: valid integer (e.g. 1)
- `kpiList`: `[{"name": "Productivity", "description": "Tasks completed per sprint"}]`

**Steps:**
1. Authenticate and obtain session token using Admin credentials from KB
2. Send `POST /performance/configure/kpi` with body `{"jobTitleId": 1, "kpiList": [{"name": "Productivity", "description": "Tasks completed per sprint"}]}`
3. Assert response status code is `200`
4. Assert response body confirms KPI was created (contains id or confirmation)

**Expected Result:** HTTP `200` — KPI configured successfully for the given Job Title.

**Category:** positive

**Status:** not_automated

---

### OH-API-030 — Configure KPIs — missing required field (negative)

**Pre-conditions:**
- Auth state: "Authenticated as Admin via POST /auth/login"

**Test Data:**
- Request body omits `jobTitleId`

**Steps:**
1. Authenticate and obtain session token using Admin credentials from KB
2. Send `POST /performance/configure/kpi` with body `{"kpiList": [{"name": "Productivity"}]}` (no jobTitleId)
3. Assert response status code is `400`

**Expected Result:** HTTP `400` — Bad request due to missing required field `jobTitleId`.

**Category:** negative

**Status:** not_automated

---

### OH-API-031 — Configure KPIs — unauthorized (negative)

**Pre-conditions:**
- No valid session token

**Test Data:**
- `Authorization: Bearer invalid_token`

**Steps:**
1. Send `POST /performance/configure/kpi` with header `Authorization: Bearer invalid_token` and a valid body
2. Assert response status code is `401`

**Expected Result:** HTTP `401` — Request rejected due to missing or invalid authentication credentials.

**Category:** negative

**Status:** not_automated

---

### OH-API-032 — Assign KPIs by Job Title — valid payload (positive)

**Pre-conditions:**
- Auth state: "Authenticated as Admin via POST /auth/login"
- At least one KPI and one Job Title exist

**Test Data:**
- `jobTitleId`: valid integer (e.g. 1)
- `kpiIds`: `[1, 2]`

**Steps:**
1. Authenticate and obtain session token using Admin credentials from KB
2. Send `PUT /performance/configure/kpi/assign` with body `{"jobTitleId": 1, "kpiIds": [1, 2]}`
3. Assert response status code is `200`

**Expected Result:** HTTP `200` — KPIs successfully assigned to the specified Job Title.

**Category:** positive

**Status:** not_automated

---

### OH-API-033 — Assign KPIs by Job Title — invalid jobTitleId (negative)

**Pre-conditions:**
- Auth state: "Authenticated as Admin via POST /auth/login"

**Test Data:**
- `jobTitleId`: 99999 (non-existent)
- `kpiIds`: `[1]`

**Steps:**
1. Authenticate and obtain session token using Admin credentials from KB
2. Send `PUT /performance/configure/kpi/assign` with body `{"jobTitleId": 99999, "kpiIds": [1]}`
3. Assert response status code is `404`

**Expected Result:** HTTP `404` — Job Title not found.

**Category:** negative

**Status:** not_automated

---

### OH-API-034 — Create Performance Tracker — valid payload (positive)

**Pre-conditions:**
- Auth state: "Authenticated as Admin via POST /auth/login"
- A valid employee and KPI exist

**Test Data:**
- `employeeId`: valid integer (e.g. 1)
- `trackerData`: `[{"kpiId": 1, "value": 4.5}]`

**Steps:**
1. Authenticate and obtain session token using Admin credentials from KB
2. Send `POST /performance/trackers` with body `{"employeeId": 1, "trackerData": [{"kpiId": 1, "value": 4.5}]}`
3. Assert response status code is `200`

**Expected Result:** HTTP `200` — Continuous feedback logged successfully for the employee.

**Category:** positive

**Status:** not_automated

---

### OH-API-035 — Create Performance Tracker — missing employeeId (negative)

**Pre-conditions:**
- Auth state: "Authenticated as Admin via POST /auth/login"

**Test Data:**
- Request body omits `employeeId`

**Steps:**
1. Authenticate and obtain session token using Admin credentials from KB
2. Send `POST /performance/trackers` with body `{"trackerData": [{"kpiId": 1, "value": 4.5}]}` (no employeeId)
3. Assert response status code is `400`

**Expected Result:** HTTP `400` — Bad request due to missing required field `employeeId`.

**Category:** negative

**Status:** not_automated

---

### OH-API-036 — Create Performance Review — valid payload (positive)

**Pre-conditions:**
- Auth state: "Authenticated as Admin via POST /auth/login"
- A valid employee and KPI exist

**Test Data:**
- `employeeId`: valid integer (e.g. 1)
- `reviewData`: `[{"kpiId": 1, "rating": 4.0}]`

**Steps:**
1. Authenticate and obtain session token using Admin credentials from KB
2. Send `POST /performance/reviews` with body `{"employeeId": 1, "reviewData": [{"kpiId": 1, "rating": 4.0}]}`
3. Assert response status code is `200`

**Expected Result:** HTTP `200` — Performance review created successfully for the employee.

**Category:** positive

**Status:** not_automated

---

### OH-API-037 — Create Performance Review — bad request (negative)

**Pre-conditions:**
- Auth state: "Authenticated as Admin via POST /auth/login"

**Test Data:**
- Request body omits `reviewData`

**Steps:**
1. Authenticate and obtain session token using Admin credentials from KB
2. Send `POST /performance/reviews` with body `{"employeeId": 1}` (no reviewData)
3. Assert response status code is `400`

**Expected Result:** HTTP `400` — Bad request due to missing required field `reviewData`.

**Category:** negative

**Status:** not_automated
