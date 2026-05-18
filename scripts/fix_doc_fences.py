"""One-off script: strip stray code fences and normalize TC section spacing in existing docs."""
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

TARGETS = [
    "products/orangehrm/docs/test_cases/api/security.md",
    "products/orangehrm/docs/test_cases/mobile/login.md",
    "products/orangehrm/docs/test_cases/web/leave_list.md",
    "products/orangehrm/docs/test_cases/web/admin_users.md",
    "products/orangehrm/docs/test_cases/web/pim_employee.md",
    "products/orangehrm/docs/test_cases/web/login.md",
    "products/restfulbooker/docs/test_cases/web/admin.md",
    "products/restfulbooker/docs/test_cases/mobile/booking.md",
]

TC_SECTION_HEADERS = re.compile(
    r"(?<!\n\n)"
    r"(\*\*(?:Pre-conditions|Test Data|Request|Steps|Expected Result|Validation|Category|Status|Note)[^*]*\*\*)",
)

for path_str in TARGETS:
    p = ROOT / path_str
    if not p.exists():
        print("SKIP:", path_str)
        continue
    text = p.read_text(encoding="utf-8")
    # Fence glued to a TC heading:  ```### → \n\n###
    text = re.sub(r"```(###)", r"\n\n\1", text)
    # Fence glued after a line ending: word``` → word
    text = re.sub(r"(\w)```", r"\1", text)
    # Bare ``` lines (whole line is only the fence)
    text = re.sub(r"^```\s*$", "", text, flags=re.MULTILINE)
    # Ensure blank line before TC headings
    text = re.sub(r"(?<!\n\n)(### [A-Z])", r"\n\n\1", text)
    # Ensure blank line before bold section headers
    text = TC_SECTION_HEADERS.sub(r"\n\1", text)
    # Collapse triple+ blank lines
    text = re.sub(r"\n{3,}", "\n\n", text)
    p.write_text(text.strip() + "\n", encoding="utf-8")
    print("Fixed:", path_str)
