# Web UI Test Case Documentation

Generated docs in this directory:

| File | Page | Coverage |
|------|------|----------|
| [login.md](login.md) | `/web/index.php/auth/login` | Positive login, invalid credentials, empty fields, SQL injection, case sensitivity |
| [pim_employee.md](pim_employee.md) | `/web/index.php/pim/viewEmployeeList` + `/pim/addEmployee` | Employee list load, search by name/ID, add employee (required + all fields), validation errors, cancel |

To regenerate docs from the KB:
```bash
python3 -m ai.generate_test_case_doc --config config/env_qa.yaml --output docs/test_cases/web/login.md
```

See [Web Test Generation Guide](../../web_test_generation.md) for full options.
