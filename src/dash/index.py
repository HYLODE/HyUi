# Run this app with `python app.py` and
# visit http://127.0.0.1:8050/ in your web browser.

from dash import dash_table as dt
from dash import dcc, html
import requests
import sys



from dash import Dash, html, dcc
import plotly.express as px

# API_URL = "http://uclvlddpragae07:8094/consultations_ed/"
API_URL = "http://api:8000/consultations_ed/"
# API_URL = "http://172.16.149.202:8094/consultations_ed/"

def request_data(url: str) -> list:
    """
    requests.json() should return a list of dicts
    """
    try:
        # import pdb; pdb.set_trace()
        response = requests.get(url)
        response.raise_for_status() # raises HTTP errors
    except requests.exceptions.HTTPError as e:
        print("!!! HTTP Error", e)
    except requests.exceptions.RequestException as e:
        print("!!! Catch-all Error", e)

    try:
        assert response.headers['Content-Type'] == 'application/json'
    except:
        raise ValueError('response is not JSON')
    return response.json()


api_json = request_data(API_URL)

debug = html.Div([
    html.P('Printing a simple table from the API'),
    dt.DataTable(
        id='api_table',
        columns = [{"name": i, "id": i} for i in api_json[0].keys()],
        data=api_json,
        filter_action="native",
        sort_action="native"

        )
])


app = Dash(__name__)

app.layout = html.Div(
    children=[
        debug
    ]
)

if __name__ == "__main__":
    # try:
    #     foo = requests.get('https://catfact.ninja/fact')
    #     assert foo.status_code == 200
    #     print(foo.text)
    # except Exception as e:
    #     sys.exit(e)
    app.run_server(debug=True, host='0.0.0.0' )
