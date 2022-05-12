# tests/conftest.py
import dash
import dash_labs
from selenium.webdriver.chrome.options import Options


def pytest_setup_options():
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-gpu")
    return chrome_options
