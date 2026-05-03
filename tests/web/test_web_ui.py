import pytest
from pages.web.test_page import SeleniumTestPage


def test_fill_and_verify_form(page):
    test_page = SeleniumTestPage(page)
    test_page.navigate("https://automationintesting.com/selenium/testpage/")

    # Test data
    first_name = "John"
    surname = "Doe"
    gender = "male"
    color = "red"
    contacts = ["email", "sms"]
    message = "This is a test message"
    continents = ["asia", "europe"]

    # Steps
    test_page.fill_first_name(first_name)
    test_page.fill_surname(surname)
    test_page.select_gender(gender)
    test_page.select_color(color)
    for contact in contacts:
        test_page.check_contact(contact)
    test_page.fill_message(message)
    test_page.select_continents(continents)

    # Verify
    assert test_page.get_first_name_value() == first_name
    assert test_page.get_surname_value() == surname
    assert test_page.get_selected_gender() == gender
    assert test_page.is_color_selected(color)
    for contact in contacts:
        assert test_page.is_contact_checked(contact)
    assert test_page.get_message_value() == message
    selected_continents = test_page.get_selected_continents()
    for continent in continents:
        assert continent in selected_continents


def test_submit_form(page):
    test_page = SeleniumTestPage(page)
    test_page.navigate("https://automationintesting.com/selenium/testpage/")

    # Test data
    first_name = "Jane"
    surname = "Smith"
    gender = "female"
    color = "blue"
    contacts = ["email"]
    message = "Another test"
    continents = ["africa"]

    # Steps
    test_page.fill_first_name(first_name)
    test_page.fill_surname(surname)
    test_page.select_gender(gender)
    test_page.select_color(color)
    for contact in contacts:
        test_page.check_contact(contact)
    test_page.fill_message(message)
    test_page.select_continents(continents)
    test_page.submit_form()

    # Since button does nothing, just ensure no error
    assert test_page.page.title() == "Selenium Test Page | Automation in Testing"


def test_optional_fields_can_be_left_blank(page):
    test_page = SeleniumTestPage(page)
    test_page.navigate("https://automationintesting.com/selenium/testpage/")

    first_name = "Alice"
    surname = "Wonder"
    gender = "female"
    color = "blue"

    test_page.fill_first_name(first_name)
    test_page.fill_surname(surname)
    test_page.select_gender(gender)
    test_page.select_color(color)
    test_page.submit_form()

    assert test_page.page.title() == "Selenium Test Page | Automation in Testing"


def test_invalid_name_characters_are_retained(page):
    test_page = SeleniumTestPage(page)
    test_page.navigate("https://automationintesting.com/selenium/testpage/")

    invalid_first_name = "J0hn@123"
    invalid_surname = "D0e#$%"

    test_page.fill_first_name(invalid_first_name)
    test_page.fill_surname(invalid_surname)
    test_page.select_gender("male")
    test_page.select_color("red")
    test_page.submit_form()

    assert test_page.get_first_name_value() == invalid_first_name
    assert test_page.get_surname_value() == invalid_surname


def test_long_message_input(page):
    test_page = SeleniumTestPage(page)
    test_page.navigate("https://automationintesting.com/selenium/testpage/")

    long_message = "A" * 512

    test_page.fill_first_name("Max")
    test_page.fill_surname("Length")
    test_page.select_gender("male")
    test_page.select_color("red")
    test_page.fill_message(long_message)
    test_page.submit_form()

    assert test_page.get_message_value() == long_message
