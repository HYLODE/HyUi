# Run this app with `python app.py` and
# visit http://127.0.0.1:8050/ in your web browser.

from dash import Dash, html, dcc, Input, Output, dash_table
import pandas as pd
import dash_bootstrap_components as dbc
import numpy as np
import re
import colorlover

###First read in the data and then make the predictions:
# Read in data
morning_data = pd.read_csv("saved_data/practice_dataset.csv", index_col=0)
extra_data = pd.read_csv("saved_data/extra_data.csv", index_col=0)

# Load the model and shap model
model = pickle.load(open("models/final_model.pkl", "rb"))
explainer = shap.TreeExplainer(model)

# Remove columns with 'ward' in them (these may cause model drift)
ward_columns = [i for i in morning_data.columns if re.match(".*_ward$", i)]
ward_columns.extend(["icu_admission"])
cols_for_use = [i for i in morning_data.columns if not i in ward_columns]

# Make our predictions
predictions = model.predict_proba(morning_data.loc[:, cols_for_use])[:, 1]

# Join this onto our extra data table
prediction_df = pd.DataFrame(
    predictions, index=morning_data.index, columns=["Admission_probability"]
)

# Join this to the extra data table
living_sketch = extra_data.merge(
    prediction_df, left_on="hospital_visit_id", right_index=True
)

# Get the explanation values
explainer.feature_names = morning_data.loc[:, cols_for_use].columns
X = np.array(morning_data.loc[:, cols_for_use])
shap_values = explainer.shap_values(X)

# Make a table of the shap values
shap_values_df = pd.DataFrame(shap_values, columns=cols_for_use)
shap_value_names = pd.DataFrame(
    shap_values_df.columns[-np.argsort(shap_values_df, axis=1)],
    index=morning_data.index,
)
df_unsorted = living_sketch.merge(
    shap_value_names.loc[:, range(5)], left_on="hospital_visit_id", right_index=True
)

# Sort the data
df_unsorted = df_unsorted.iloc[:, 4:]
sorted_locs = np.argsort(-df_unsorted["Admission_probability"])
df = df_unsorted.loc[sorted_locs, :]

# Split the dataframe to get a better ward name
whole_locs = [re.split("\^", i)[1] for i in df.location_string]
wards = [re.split(" ", i)[:-1] for i in whole_locs]
df["ward"] = [i[-1] for i in wards]

# Make table of hotspots
hotspots = pd.DataFrame(np.sort(df["ward"].unique()))
hotspots.columns = ["Ward"]

# Calculate different NEWS levels
hotspots["ward_NEWS_over_3"] = np.nan
hotspots["ward_NEWS_over_5"] = np.nan
hotspots["ward_NEWS_over_7"] = np.nan
hotspots["ward_NEWS_over_9"] = np.nan
hotspots["ward_NEWS_over_11"] = np.nan

hotspots["average_ward_NEWS"] = np.nan
hotspots["total_icu_admission"] = np.nan

for i in hotspots["Ward"]:
    ward_locs = df["ward"] == i

    # Patients with a NEWS >5
    ward_NEWS_over_3 = len(
        np.intersect1d(
            np.where(pd.to_numeric(df["news_score"]) >= 3), np.where(ward_locs)
        )
    )
    ward_NEWS_over_5 = len(
        np.intersect1d(
            np.where(pd.to_numeric(df["news_score"]) >= 5), np.where(ward_locs)
        )
    )
    ward_NEWS_over_7 = len(
        np.intersect1d(
            np.where(pd.to_numeric(df["news_score"]) >= 7), np.where(ward_locs)
        )
    )
    ward_NEWS_over_9 = len(
        np.intersect1d(
            np.where(pd.to_numeric(df["news_score"]) >= 9), np.where(ward_locs)
        )
    )
    ward_NEWS_over_11 = len(
        np.intersect1d(
            np.where(pd.to_numeric(df["news_score"]) >= 11), np.where(ward_locs)
        )
    )

    # Mean news
    mean_NEWS = np.nanmean(df.news_score[ward_locs])

    # Total ICU admission
    total_admission = np.nansum(df.Admission_probability[ward_locs])

    # Now re_allocate
    hotspots.loc[hotspots.Ward == i, ["average_ward_NEWS"]] = mean_NEWS
    hotspots.loc[hotspots.Ward == i, ["total_icu_admission"]] = total_admission
    hotspots.loc[hotspots.Ward == i, ["ward_NEWS_over_3"]] = ward_NEWS_over_3
    hotspots.loc[hotspots.Ward == i, ["ward_NEWS_over_5"]] = ward_NEWS_over_5
    hotspots.loc[hotspots.Ward == i, ["ward_NEWS_over_7"]] = ward_NEWS_over_7
    hotspots.loc[hotspots.Ward == i, ["ward_NEWS_over_9"]] = ward_NEWS_over_9
    hotspots.loc[hotspots.Ward == i, ["ward_NEWS_over_11"]] = ward_NEWS_over_11

# Pull in the example inputs
input_data = pd.read_csv(
    "~/Documents/F4/Data_science/Deterioration/morning_data_example_df.csv"
)
# Sort it by admission probability
input_data = input_data.loc[sorted_locs, :]

markdown_text = """
# Interactive Deterioration App

This is an app to allow clinicians to interact with the list of who is deteriorating.
"""


app = Dash(__name__)

app.layout = html.Div(
    [
        # Title
        html.Div(html.H4(children="Deterioration App"), style={"textAlign": "center"}),
        # html.Div(html.)
        # Options
        html.Div(
            [
                html.Div(
                    children=[
                        html.Label("Number of Rows"),
                        dcc.Dropdown([10, 20, 30, 40], 10, id="nrows"),
                        html.Br(),
                        html.Label("Wards to Include"),
                        dcc.Dropdown(
                            [i for i in np.unique(hotspots["Ward"])],
                            [i for i in np.unique(hotspots["Ward"])],
                            id="dropdown",
                            multi=True,
                        ),
                    ],
                    style={"padding": 10, "flex": 1},
                ),
                html.Div(
                    children=[
                        html.Label("Include Patients Not For Resus"),
                        dcc.Checklist(["True"], ["True"], id="dnacpr")
                        # html.Label('Text Input'),
                        # dcc.Input(value='MTL', type='text'),
                    ],
                    style={"padding": 10, "flex": 1},
                ),
            ],
            style={"display": "flex", "flex-direction": "row"},
        ),
        # Table
        html.Div(id="my-output"),
        # Table
        # html.Div(id = 'states_out'),
    ]
)


@app.callback(
    Output(component_id="my-output", component_property="children"),
    Input(component_id="dropdown", component_property="value"),
    Input(component_id="nrows", component_property="value"),
)
def generate_table(search_value, max_rows):

    # Chose only certain wards
    ward_index = [i for i, j in enumerate(hotspots["Ward"]) if j in search_value]
    hotspots1 = hotspots.iloc[ward_index, :]

    # global input_data1
    # input_data1 = input_data0.iloc[ward_index, :]

    global hotspots2
    hotspots2 = hotspots1.iloc[:max_rows, :]

    def discrete_background_color_bins(df, n_bins=5, columns="all"):
        import colorlover

        bounds = [i * (1.0 / n_bins) for i in range(n_bins + 1)]
        if columns == "all":
            if "id" in df:
                df_numeric_columns = df.select_dtypes("number").drop(["id"], axis=1)
            else:
                df_numeric_columns = df.select_dtypes("number")
        else:
            df_numeric_columns = df[columns]
        df_max = df_numeric_columns.max().max()
        df_min = df_numeric_columns.min().min()
        ranges = [((df_max - df_min) * i) + df_min for i in bounds]
        styles = []
        legend = []
        for i in range(1, len(bounds)):
            min_bound = ranges[i - 1]
            max_bound = ranges[i]
            backgroundColor = colorlover.scales[str(n_bins)]["seq"]["Blues"][i - 1]
            color = "white" if i > len(bounds) / 2.0 else "inherit"

            for column in df_numeric_columns:
                styles.append(
                    {
                        "if": {
                            "filter_query": (
                                "{{{column}}} >= {min_bound}"
                                + (
                                    " && {{{column}}} < {max_bound}"
                                    if (i < len(bounds) - 1)
                                    else ""
                                )
                            ).format(
                                column=column, min_bound=min_bound, max_bound=max_bound
                            ),
                            "column_id": column,
                        },
                        "backgroundColor": backgroundColor,
                        "color": color,
                    }
                )
            legend.append(
                html.Div(
                    style={"display": "inline-block", "width": "60px"},
                    children=[
                        html.Div(
                            style={
                                "backgroundColor": backgroundColor,
                                "borderLeft": "1px rgb(50, 50, 50) solid",
                                "height": "10px",
                            }
                        ),
                        html.Small(round(min_bound, 2), style={"paddingLeft": "2px"}),
                    ],
                )
            )

        return (styles, html.Div(legend, style={"padding": "5px 0 5px 0"}))

    (styles, legend) = discrete_background_color_bins(
        hotspots, columns=["total_icu_admission"]
    )

    # TO do - make checkbox tower vs ega vs

    return dbc.Container(
        [
            dbc.Label("Hotspots Table"),
            legend,
            dash_table.DataTable(
                hotspots2.to_dict("records"),
                [{"name": i, "id": i} for i in hotspots2.columns],
                sort_action="native",
                id="tbl",
                style_cell={"font-family": "sans-serif"},
                style_data_conditional=styles,
            ),
            dbc.Alert(id="tbl_out"),
        ]
    )


"""
@app.callback(Output('tbl_out', 'children'),
              Input('tbl', 'active_cell'))
def update_graphs(active_cell):

    #return dff.loc[active_cell['row'], active_cell['column_id']] if active_cell else "Click the table"
    if active_cell:
        if active_cell['column'] > 7:

            #Pull what's in the box
            location = dff.iloc[active_cell['row'], active_cell['column']]
            return input_data1.loc[active_cell['row'], location]

        else:
            return dff.loc[active_cell['row'], active_cell['column_id']]
    else:
        return 'Click the table'
"""

if __name__ == "__main__":
    app.run_server(debug=True)

# Think about putting the last 12 hours of observations underneath for when you click on a given patient? And or some additional information about them?
