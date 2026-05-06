# Web UI Test Case Documentation

Generated docs in this directory:

| File | Page | Coverage |
|------|------|----------|
| [login.md](login.md) | `/auth/login` | Valid login, invalid creds, empty fields, SQL injection, case sensitivity |
| [pim_employee.md](pim_employee.md) | `/pim/viewEmployeeList` + `/pim/addEmployee` | Employee list, search, add (required + all fields), validation, cancel |
| [leave_list.md](leave_list.md) | `/leave/viewLeaveList` | Leave list load, date range filter, status filter, no-records |
| [admin_users.md](admin_users.md) | `/admin/viewSystemUsers` + add form | User list, search, add user validation, cancel |

To regenerate a doc from the KB:
```bash
python3 -m ai.generate_test_case_doc --config config/env_qa.yaml \
    --output docs/test_cases/web/<page>.md
```

See [Web Test Generation Guide](../../web_test_generation.md) for full options.
