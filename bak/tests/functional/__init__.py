from dash.testing.application_runners import import_app

PORT = 8051


def prepare_app(dash_duo, port=PORT):
    # get the external app
    app = import_app(app_file="app")
    # 4. host the app locally in a thread, all dash server configs could be
    # passed after the first app argument
    dash_duo.start_server(app, port=port)


def prepare_page(dash_duo, page, host="http://127.0.0.1", port=PORT):
    path = f"{host}:{port}/{page}"
    dash_duo.wait_for_page(path)
