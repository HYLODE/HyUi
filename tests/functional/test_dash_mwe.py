# tests/functional/test_dash_mwe.py
# from src import app
from dash.testing.application_runners import import_app
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions


def test_example1(dash_duo):
    # get the external app
    app = import_app(app_file='app')
    # 4. host the app locally in a thread, all dash server configs could be
    # passed after the first app argument
    # dash_duo.start_server(app)
    dash_duo.start_server(app, port=8051)
    # 5. use wait_for_* if your target element is the result of a callback,
    # keep in mind even the initial rendering can trigger callbacks
    dash_duo.wait_for_text_to_equal("#h1-title", "Gapminder example with callbacks", timeout=4)
    dash_duo.wait_for_element("#graph-with-slider", timeout=4)
    # assert dash_duo.driver.find_element("#h1-title").text == "Gapminder example with callbacks"
    # 7. to make the checkpoint more readable, you can describe the
    # acceptance criterion as an assert message after the comma.
    # assert dash_duo.get_logs() == [], "browser console should contain no error"
    # 8. visual testing with percy snapshot
    # dash_duo.percy_snapshot("example1-layout")

def test_example2(dash_duo):
    # get the app
    app = import_app(app_file='app')
    dash_duo.start_server(app, port=8051)

    WebDriverWait(dash_duo.driver, 10).until(
        expected_conditions.visibility_of_element_located(
            (By.CSS_SELECTOR, "#graph-with-slider")))
    assert dash_duo.driver.find_element(by=By.CSS_SELECTOR, value="#graph-with-slider").is_displayed()


def test_example3(dash_duo):
    app = import_app(app_file='app')
    dash_duo.start_server(app, port=8051)
    # #_dash-app-content > div > nav > div > span
    # //*[@id="_dash-app-content"]/div/nav/div/span
    # dash_duo.wait_for_text_to_equal("Multi Page App Plugin Demo", timeout=4)
    # dash_duo.wait_for_text_to_equal(
    #     "#_dash-app-content div nav div span",
    #     "Multi Page App Plugin Demo")

    dash_duo.wait_for_element("#histograms-graph", timeout=4)
    # css_selector="#histograms-graph"
    # assert dash_duo.driver.find_element(by=By.CSS_SELECTOR, value=css_selector).is_displayed()
    dash_duo.wait_for_page(url="http://127.0.0.1:8051/heatmaps", timeout=4)
    test_text = "#_pages_plugin_content > div > p"
    assert dash_duo.wait_for_contains_text(test_text, "Medals")
