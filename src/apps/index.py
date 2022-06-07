"""
Principle application file
https://dash.plotly.com/urls
"""
from dash import Input, Output, dcc, html

from landing import landing
from consults.consults import consults

from app import app

app.layout = html.Div(
    [dcc.Location(id="url", refresh=False), html.Div(id="page-content")]
)


@app.callback(Output("page-content", "children"), Input("url", "pathname"))
def display_page(pathname):
    if pathname == "/":
        return landing
    elif pathname == "/consults":
        return consults
    else:
        # TODO proper 404  route
        return "404"


if __name__ == "__main__":
    app.run_server(host="0.0.0.0", port=8095, debug=True)
