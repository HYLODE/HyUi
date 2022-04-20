# tests/functional/test_dash_mwe.py

from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions

from . import prepare_app, prepare_page
# FIXME: tests 2+ fail; something to do with reinstantiating the app?
# but any single test passes


def test_example1(dash_duo):
    prepare_app(dash_duo)
    prepare_page(dash_duo, 'gapminder')
    dash_duo.wait_for_text_to_equal(
        "#h1-title", "Gapminder example with callbacks", timeout=4)
    dash_duo.wait_for_element("#graph-with-slider", timeout=4)


def test_example2(dash_duo):
    prepare_app(dash_duo)
    prepare_page(dash_duo, 'gapminder')
    WebDriverWait(dash_duo.driver, 10).until(
        expected_conditions.visibility_of_element_located(
            (By.CSS_SELECTOR, "#graph-with-slider")))
    assert dash_duo.driver.find_element(
        by=By.CSS_SELECTOR, value="#graph-with-slider").is_displayed()


def test_example3(dash_duo):
    prepare_app(dash_duo)
    prepare_page(dash_duo, '/')
    dash_duo.wait_for_element("#histograms-graph", timeout=4)
    prepare_page(dash_duo, 'heatmaps')
    test_text = "#_pages_plugin_content > div > p"
    assert dash_duo.wait_for_contains_text(test_text, "Medals")
