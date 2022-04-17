# this is the layout page; but the file name defines the page name
# via https://dash.plotly.com/basic-callbacks#dash-app-layout-with-figure-and-slider
import dash

dash.register_page(__name__, path='/gapminder', title='gapminder', name='gapminder')

from dash import dcc, html
from .callbacks import df



layout = html.Div([
    html.H1(id="h1-title", children=['Gapminder example with callbacks']),
    dcc.Graph(id='graph-with-slider'),
    dcc.Slider(
        df['year'].min(),
        df['year'].max(),
        step=None,
        value=df['year'].min(),
        marks={str(year): str(year) for year in df['year'].unique()},
        id='year-slider'
    )
])


