# tests/functional/test_dash_mwe.py
# from src import app
from dash.testing.application_runners import import_app
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions


# def test_dash_mwe():
#     """
#     GIVEN a basic dev set-up
#     WHEN the mwe app is run
#     THEN check the response is valid
#     """
#     with app.test_client() as client:
#         response = client.get('/')
#         assert response.status_code == 200
#         assert b'Hello Dash' in response.data


def test_example(dash_duo):
    app = import_app(app_file='src.app')
    dash_duo.start_server(app)
    WebDriverWait(dash_duo.driver, 10).until(
        expected_conditions.visibility_of_element_located(
            (By.CSS_SELECTOR, "#example-graph")))
    assert dash_duo.driver.find_element(by=By.CSS_SELECTOR, value="#example-graph").is_displayed()
