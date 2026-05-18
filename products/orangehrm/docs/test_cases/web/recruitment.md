# Test Case Document — Recruitment

**Product:** OrangeHRM  
**Layer:** Web  
**Module:** Recruitment (`/web/index.php/recruitment/`)

---

## Test Case Index

| ID | Scenario | Type | Status | Script |
|---|---|---|---|---|
| OH-WEB-031 | Vacancies list loads with all active vacancies on navigation | positive | automated | test_recruitment.py |
| OH-WEB-032 | Filter vacancies by job title narrows list | positive | automated | test_recruitment.py |
| OH-WEB-033 | Filter by status Active shows only active vacancies | positive | automated | test_recruitment.py |
| OH-WEB-034 | Clicking Add navigates to Add Vacancy form | positive | automated | test_recruitment.py |
| OH-WEB-035 | Filter with no matching job title shows No Records Found | negative | automated | test_recruitment.py |
| OH-WEB-036 | Save vacancy with required fields only creates vacancy | positive | not_automated | — |
| OH-WEB-037 | Save vacancy with all fields creates complete vacancy record | positive | not_automated | — |
| OH-WEB-038 | Save vacancy without Vacancy Name shows required field error | negative | not_automated | — |
| OH-WEB-039 | Save vacancy without Job Title shows required field error | negative | not_automated | — |
| OH-WEB-040 | Save vacancy without Hiring Manager shows required field error | negative | not_automated | — |
| OH-WEB-041 | Vacancy Name exceeding 100 characters shows validation error | negative | not_automated | — |
| OH-WEB-042 | No. of Positions with value 0 or negative shows validation error | negative | not_automated | — |
| OH-WEB-043 | Cancel on Add Vacancy returns to vacancies list without saving | positive | not_automated | — |
| OH-WEB-044 | Add candidate with required fields (First Name, Last Name, Email, Date) | positive | not_automated | — |
| OH-WEB-045 | Add candidate with all fields including resume (valid PDF) | positive | not_automated | — |
| OH-WEB-046 | Save candidate without First Name shows required field error | negative | not_automated | — |
| OH-WEB-047 | Save candidate without Last Name shows required field error | negative | not_automated | — |
| OH-WEB-048 | Save candidate without Email shows required field error | negative | not_automated | — |
| OH-WEB-049 | Save candidate with invalid email format shows validation error | negative | not_automated | — |
| OH-WEB-050 | Resume upload with unsupported file type is rejected | negative | not_automated | — |
| OH-WEB-051 | Resume upload exceeding 2MB is rejected | edge | not_automated | — |
| OH-WEB-052 | Schedule interview with required fields (Title, Interviewer, Date) | positive | not_automated | — |
| OH-WEB-053 | Schedule interview without title shows required field error | negative | not_automated | — |
| OH-WEB-054 | Schedule interview without interviewer shows required field error | negative | not_automated | — |
| OH-WEB-055 | Multiple interviewers can be assigned to one interview | edge | not_automated | — |
| OH-WEB-056 | ESS user cannot access vacancies or candidates (access denied) | negative | not_automatable | — |
| OH-WEB-057 | Candidate status transitions through full hiring pipeline | positive | async_dependent | — |

> 
**Status values:** `automated` = script exists · `not_automated` = not yet scripted · `not_automatable` = human must mark; skipped by script generator · `async_dependent` = requires running workflow/scheduler

---

## Sub-modules

| Sub-module | URL | Scripted |
|---|---|---|
| Job Vacancies list | `/recruitment/viewJobVacancy` | Yes (OH-WEB-031 to 035) |
| Add Vacancy form | `/recruitment/addJobVacancy` | No (OH-WEB-036 to 043) |
| Candidates list | `/recruitment/viewCandidates` | No |
| Add Candidate form | `/recruitment/addCandidate` | No (OH-WEB-044 to 051) |
| Interview Schedule | `/recruitment/interviewSchedule` | No (OH-WEB-052 to 055) |

---

## 1. Job Vacancies List

**URL:** `/web/index.php/recruitment/viewJobVacancy`

### Fields (filter bar)
- Job Title (dropdown, optional)
- Vacancy (text, optional)
- Hiring Manager (autocomplete, optional)
- Status (dropdown: Active/Inactive, optional)
- Search button
- Add button
- Vacancies table

### OH-WEB-031 — Vacancies List Loads

**Pre-conditions:** Authenticated as Admin  

**Steps:** Navigate to `/recruitment/viewJobVacancy`  
**Expected:** Vacancies table is visible with active vacancies

### OH-WEB-032 — Filter By Job Title

**Test Data:** Job Title = "Software Engineer"  

**Steps:** Enter job title in filter, click Search  
**Expected:** Only vacancies matching that title are shown

### OH-WEB-033 — Filter By Status Active

**Steps:** Select "Active" from Status dropdown, click Search  
**Expected:** Only active vacancies displayed

### OH-WEB-034 — Add Button Navigates To Form

**Steps:** Click Add  
**Expected:** Redirected to Add Vacancy form

### OH-WEB-035 — No Match Shows No Records Found

**Test Data:** Job Title = "NonExistentJobTitle"  

**Steps:** Enter non-existent job title, click Search  
**Expected:** "No Records Found" displayed

---

## 2. Add Vacancy Form

**URL:** `/web/index.php/recruitment/addJobVacancy`

### Fields
| Field | Type | Required | Notes |
|---|---|---|---|
| Vacancy Name | text | Yes | Max 100 chars |
| Job Title | dropdown | Yes | Must exist in Admin config |
| Hiring Manager | autocomplete | Yes | Must be active employee |
| No. of Positions | number | No | Positive integer |
| Description | textarea | No | — |
| Status | dropdown | Yes | Active / Inactive |

### Business Rules
- Vacancy Name must be unique
- Hiring Manager must be an existing active employee
- No. of Positions: positive integer only; 0 and negatives are invalid

### OH-WEB-036 to OH-WEB-043
*(See Test Case Index above — not yet scripted)*

---

## 3. Add Candidate Form

**URL:** `/web/index.php/recruitment/addCandidate`

### Fields
| Field | Type | Required | Notes |
|---|---|---|---|
| First Name | text | Yes | Max 30 chars |
| Middle Name | text | No | Max 30 chars |
| Last Name | text | Yes | Max 30 chars |
| Email | email | Yes | Valid email format |
| Contact Number | text | No | Max 25 chars |
| Vacancy | dropdown | No | Links to a vacancy |
| Resume | file upload | No | PDF/DOC/DOCX, max 2MB |
| Date of Application | date | Yes | Defaults to today |
| Consent to Keep Data | checkbox | No | — |
| Keywords | text | No | — |
| Notes | textarea | No | — |

### OH-WEB-044 to OH-WEB-051
*(See Test Case Index above — not yet scripted)*

---

## 4. Interview Schedule

**URL:** `/web/index.php/recruitment/interviewSchedule`

### Fields
| Field | Type | Required | Notes |
|---|---|---|---|
| Interview Title | text | Yes | Max 100 chars |
| Interviewers | multi-select | Yes | Active employees |
| Interview Date | date | Yes | — |
| Interview Time | time | No | — |
| Duration (Hours/Minutes) | number | No | — |
| Location | text | No | Max 100 chars |
| Notes | textarea | No | — |

### OH-WEB-052 to OH-WEB-055
*(See Test Case Index above — not yet scripted)*

---

## 5. Special Cases

### OH-WEB-056 — ESS Access Denied (not_automatable)

**Note:** Requires a separate ESS user session on the demo. The demo's ESS test user (`Kris.Chapman / Admin123`) may have different access depending on demo state. Run manually against a controlled environment.

### OH-WEB-057 — Full Hiring Pipeline Status Transitions (async_dependent)

**Note:** Requires triggering multiple workflow steps (shortlist → schedule interview → record outcome → make offer → hire). Each step has a human or scheduled trigger. Use `wait_for()` with `WORKFLOW_STEP_TIMEOUT` between transitions.
