import pytest
from pages.web.home_page import HomePage


@pytest.mark.web
@pytest.mark.a11y
def test_RB_A11Y_001_home_page_has_main_heading(page, rb_web_base):
    HomePage(page, rb_web_base).navigate()
    headings = page.get_by_role("heading")
    assert headings.count() >= 1, "No heading element found on home page"


@pytest.mark.web
@pytest.mark.a11y
def test_RB_A11Y_002_room_images_have_alt_text(page, rb_web_base):
    HomePage(page, rb_web_base).navigate()
    images = page.locator("img")
    count = images.count()
    assert count > 0, "No images found on home page"
    missing = []
    for i in range(count):
        img = images.nth(i)
        alt = img.get_attribute("alt")
        if alt is None:
            src = img.get_attribute("src") or f"image[{i}]"
            missing.append(src)
    assert not missing, f"Images missing alt attribute: {missing}"


@pytest.mark.web
@pytest.mark.a11y
def test_RB_A11Y_003_contact_form_fields_have_labels(page, rb_web_base):
    HomePage(page, rb_web_base).navigate()
    # Contact section should have labelled inputs
    for field_hint in ("name", "email", "phone", "subject", "message"):
        inp = page.get_by_label(field_hint, exact=False)
        placeholder_inp = page.locator(f"input[placeholder*='{field_hint}' i], textarea[placeholder*='{field_hint}' i]")
        has_label = inp.count() > 0
        has_placeholder = placeholder_inp.count() > 0
        assert has_label or has_placeholder, \
            f"Contact form field '{field_hint}' has neither a label nor a placeholder"


@pytest.mark.web
@pytest.mark.a11y
def test_RB_A11Y_004_page_is_keyboard_navigable(page, rb_web_base):
    HomePage(page, rb_web_base).navigate()
    page.keyboard.press("Tab")
    focused_tag = page.evaluate("document.activeElement.tagName")
    assert focused_tag in ("A", "BUTTON", "INPUT", "SELECT", "TEXTAREA"), \
        f"First Tab did not land on an interactive element; focused: {focused_tag}"
