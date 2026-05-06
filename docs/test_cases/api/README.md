# API Test Case Documentation

| File | Module | Endpoints |
|------|--------|-----------|
| [orangehrm_leave.md](orangehrm_leave.md) | Leave | `GET /leave/leave-types`, `POST /leave/leave-requests` |
| [orangehrm_admin.md](orangehrm_admin.md) | Admin Users | `GET /admin/users`, `POST /admin/users` |

Restful Booker and GraphQL API test cases are embedded in-code; docs pending generation.

To generate API docs:
```bash
python3 -m ai.generate_api_test_doc --endpoint /booking --method POST \
    --output docs/test_cases/api/booking_create.md
```

See [API Test Generation Guide](../../api_test_generation.md) for full options.
