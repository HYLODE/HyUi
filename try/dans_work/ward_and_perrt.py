# Run this app with `python app.py` and
# visit http://127.0.0.1:8050/ in your web browser.

from dash import Dash, html, dcc, Input, Output, dash_table
import pandas as pd
import dash_bootstrap_components as dbc
import numpy as np
import plotly.express as px
import re
from dash.dependencies import State
import pickle
import shap
import xgboost

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

# df_unsorted = df_unsorted.iloc[:, 4:]
sorted_locs = np.argsort(-df_unsorted["Admission_probability"])
df = df_unsorted.loc[sorted_locs, :]
df.Admission_probability = np.round(df.Admission_probability, decimals=3)

# Fix the datetime stamp
df.admission_time = pd.to_datetime(df.admission_time, utc=True)
df.admission_time = df.admission_time.dt.strftime("%d/%m, %H:%M")

df.news_time = pd.to_datetime(df.news_time, utc=True)
df.news_time = df.news_time.dt.strftime("%d/%m, %H:%M")

# Pull in other inputs
labs_data = pd.read_csv("saved_data/labs_only_df.csv", index_col=0)
others_df = pd.read_csv("saved_data/others_df.csv", index_col=0)
df = pd.merge(
    df,
    others_df.loc[:, ["hospital_visit_id", "time_since_perrt_ref"]],
    on=["hospital_visit_id"],
)


# Make the perrt list and change column order
df["perrt_list"] = df.time_since_perrt_ref.isna() == False

# Fix the ward purpose
whole_locs = [re.split("\^", i)[1] for i in df.location_string]
wards = [re.split(" ", i)[:-1] for i in whole_locs]
df.ward_purpose = [i[-1] for i in wards]

# Get just granular location
df.location_string = [re.split("\^", i)[2] for i in df.location_string]

# Pull in the example inputs
results_df = pd.read_csv("saved_data/results_df.csv")
# Sort it by admission probability
input_data = df


#### Processing observations data for plotting

# process obs data
# Split BP
BP_df = results_df.loc[results_df.vital == "BP", :]
BP_df = BP_df.reset_index()

# Make new dfs that we will paste on the end
MAP_df = BP_df.copy()
SBP_df = BP_df.copy()
DBP_df = BP_df.copy()

# Split them and force numeric
SBP_df.value = pd.to_numeric(BP_df.value.str.split("/", 1, expand=True)[0])
SBP_df.vital = "SBP"
DBP_df.value = pd.to_numeric(BP_df.value.str.split("/", 1, expand=True)[1])
DBP_df.vital = "DBP"
MAP_df.value = DBP_df.value + (SBP_df.value - DBP_df.value) * (1 / 3)
MAP_df.vital = "MAP"

# Now just pull observations
obs_columns = [
    "Oxygen",
    "AVPU",
    "SpO2",
    "Resp",
    "Pulse",
    "Temp",
    "NEWS Score",
    "Oxygen delivery device",
    "GCS Total",
    "Oxygen therapy flow rate",
    "NEWS2 Score",
]
obs_locs = [i for i, j in enumerate(results_df.vital) if j in obs_columns]
extra_obs = results_df.loc[obs_locs, :]

# Rename NEWS2 to NEWS
extra_obs.loc[extra_obs.vital == "NEWS2 Score", ["vital"]] = "NEWS Score"

# Add back BPs
extra_obs = pd.concat([extra_obs, MAP_df, SBP_df, DBP_df])
extra_obs = extra_obs.reset_index()

# Convert temp back to C
Temp_F = extra_obs.loc[extra_obs.vital == "Temp", "value"]
extra_obs.loc[extra_obs.vital == "Temp", "value"] = (Temp_F.astype(float) - 32) * (
    5 / 9
)


def plot_selected_columns(plot_type: str, patient: int, df: pd.DataFrame) -> None:
    """Function that wraps plotly express to make a plot of obs
    for a given patient. Pass a list of observations and an hv_id"""

    # Should set some defaults depending on what obs we choose to plot. May also want to include AVPU?
    if plot_type == "BP":
        cols = ["Pulse", "SBP", "DBP", "MAP"]
        rangey = [40, 200]
        colors = {"Pulse": "red", "SBP": "blue", "DBP": "blue", "MAP": "green"}
        plot_height = 400
        titles = "Pulse and BP"

    elif plot_type == "Temp":
        cols = ["Temp"]
        rangey = [33, 41]
        colors = {"Temp": "red"}
        plot_height = 300
        titles = "Temperature"

    elif plot_type == "GCS":
        # Map AVPU to numeric
        df.loc[df.vital == "AVPU", "value"] = df.loc[df.vital == "AVPU", "value"].map(
            {"A": 5, "C": 4, "V": 3, "P": 2, "U": 1}
        )
        cols = ["AVPU", "GCS"]
        rangey = [0, 16]
        colors = {"AVPU": "red", "GCS": "blue"}
        plot_height = 300
        titles = "Consciousness"

    elif plot_type == "Resp":
        cols = ["Oxygen therapy flow rate", "Resp"]
        rangey = [0, 30]
        colors = {"Oxygen therapy flow rate": "red", "Resp": "blue"}
        plot_height = 300
        titles = "Resp rate and oxygen"

    elif plot_type == "Sats":
        cols = "SpO2"
        rangey = [80, 101]
        colors = {"SpO2": "blue"}
        plot_height = 300
        titles = "Sats"

    else:
        raise ValueError("Plot type must be one of BP, Sats, Resp, GCS, Temp")

    # Just choose some for plotting
    plotting_cols = cols
    plotting_locs = [i for i, j in enumerate(df.vital) if j in plotting_cols]
    plotting_df = df.loc[plotting_locs, :]

    patient_id = patient
    plotting_df.value = plotting_df.value.astype(np.float64)

    # Make the plot
    fig = px.line(
        plotting_df.loc[plotting_df.hospital_visit_id == int(patient_id), :],
        x="observation_datetime",
        y="value",
        color="vital",
        symbol="vital",
        width=700,
        height=plot_height,
        color_discrete_map=colors,
        range_y=rangey,
        title=titles,
    )

    # Make the background white/ see through
    fig.update_layout(
        {"plot_bgcolor": "rgba(0, 0, 0, 0)", "paper_bgcolor": "rgba(0, 0, 0, 0)"}
    )
    return fig


### Now process labs data
# Keep only the most recent labs
sorted_labs = labs_data.sort_values(
    ["hospital_visit_id", "observation_datetime", "vital"], ascending=False
)
sorted_unique_labs = sorted_labs.drop_duplicates(
    ["hospital_visit_id", "observation_datetime", "vital"]
)

# Make a pivot table
pivot_labs = sorted_unique_labs.pivot(
    index=["hospital_visit_id", "observation_datetime"],
    columns="vital",
    values=["value"],
)
pivot_labs.columns = [i[1] for i in pivot_labs.columns.to_flat_index()]
pivot_labs = pivot_labs.reset_index()

pivot_labs.observation_datetime = pd.to_datetime(pivot_labs.observation_datetime)
pivot_labs["date_time"] = pivot_labs.observation_datetime.dt.strftime("%d/%m, %H:%M")

# Make sure all columns available (even if nan)
all_labs = [
    "HBGL",
    "RCC",
    "HCT",
    "HCTU",
    "MCVU",
    "PLT",
    "NE",
    "WCC",
    "LY",
    "NA",
    "K",
    "CREA",
    "GFR",
    "UREA",
    "BILI",
    "ALP",
    "ALT",
    "ALB",
    "CRP",
    "MG",
    "CA",
    "CCA",
    "PHOS",
    "LDH",
    "HTRT",
    "INR",
    "PT",
    "APTT",
    "GLU",
    "Glu",
    "pH",
    "pCO2",
    "K+",
    "Na+",
    "Lac",
    "Urea",
    "Crea",
    "tHb",
    "COHb",
    "Ferr",
    "pO2",
    "Urea",
]
for i in all_labs:
    if not i in pivot_labs.columns:
        pivot_labs[i] = np.nan


def results_table(
    pt_id: int, input_tab: pd.DataFrame, colnames: list, new_names: list = None
) -> pd.DataFrame:
    """function to return a nicely formatted df with lab results"""

    # Ensure all the columns are in input_tab
    missing_columns = [
        colnames[i]
        for i in np.where(pd.Series(colnames).isin(input_tab.columns) == False)[0]
    ]
    input_tab.loc[:, missing_columns] = np.nan

    # Pull out only rows where none of the labs are na
    labs_not_nan = input_tab.loc[:, colnames[2:]].isna().apply(all, axis=1)
    pt_labs = np.intersect1d(
        np.where(input_tab.hospital_visit_id == pt_id), np.where(-labs_not_nan)
    )
    pt_labs = input_tab.loc[pt_labs, colnames]
    pt_labs.index = pt_labs.date_time

    # If renaming
    if new_names:
        pt_labs.columns = new_names

    pt_labs = pt_labs.loc[:, pt_labs.columns[1:]].transpose()

    return pt_labs.rename_axis("date_time").reset_index()


markdown_text = """
# Interactive Deterioration App

This is an app to allow clinicians to interact with the list of who is deteriorating.
"""


app = Dash(
    __name__,
    title="Deterioration",
    update_title=None,
    external_stylesheets=[
        dbc.themes.YETI,
        dbc.icons.FONT_AWESOME,
    ],
)

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
                            [i for i in np.unique(df["ward_purpose"])],
                            [i for i in np.unique(df["ward_purpose"])],
                            id="dropdown",
                            multi=True,
                        ),
                    ],
                    style={"padding": 10, "flex": 1},
                ),
                html.Div(
                    children=[
                        html.Label("Include Patients Not For Resus"),
                        dcc.Checklist(["True"], ["True"], id="dnacpr"),
                        html.Label("Include Only PERRT List"),
                        dcc.Checklist(["True"], [], id="perrt"),
                        html.Br(),
                        # html.Label('Text Input'),
                        # dcc.Input(value='MTL', type='text'),
                        html.Br(),
                        html.Label("Number of SHAP Features"),
                        dcc.Slider(
                            id="slider-input",
                            min=0,
                            max=len(df.columns),
                            marks={i: f"{i}" if i == 1 else str(i) for i in range(6)},
                            value=0,
                        ),
                    ],
                    style={"padding": 10, "flex": 1},
                ),
            ],
            style={"display": "flex", "flex-direction": "row"},
        ),
        # Table
        html.Div(id="my-output", style={"color": "black", "fontSize": 14}),
        # Table
        html.Button(
            id="submit-button-state",
            n_clicks=0,
            children="Add/remove selected patients to PERRT list",
        ),
        html.Div(id="datatable-row-ids-container"),
        # Figure
        html.Div(
            [
                dbc.Row(
                    [
                        dbc.Col(
                            [
                                dcc.Graph(id="obs_graph"),
                                dcc.Graph(id="gcs_graph"),
                                dcc.Graph(id="temp_graph"),
                                dcc.Graph(id="oxygen_graph"),
                                dcc.Graph(id="sats_graph"),
                            ]
                        ),
                        dbc.Col(
                            [
                                html.Label("Recent Blood Tests"),
                                html.Div(
                                    id="LFTs", style={"color": "black", "fontSize": 12}
                                ),
                            ]
                        ),
                    ]
                )
            ]
        ),
    ]
)


#### Callback to generate initial data table
@app.callback(
    Output(component_id="my-output", component_property="children"),
    Input(component_id="slider-input", component_property="value"),
    Input(component_id="dropdown", component_property="value"),
    Input(component_id="nrows", component_property="value"),
    Input(component_id="dnacpr", component_property="value"),
    Input(component_id="perrt", component_property="value"),
)
def generate_table(ncols, search_value, max_rows, dnacpr, perrt):

    # Include patients not for resus
    if not dnacpr:
        df0 = df.loc[df["dnacpr"] != "DNACPR", :]
        input_data0 = input_data.loc[df["dnacpr"] != "DNACPR", :]
    else:
        df0 = df
        input_data0 = input_data

    # Include only PERRT list
    if perrt:
        df01 = df0.loc[df0["perrt_list"] == True, :]
        # input_data01 = input_data0.loc[df0['perrt_list'] == True, :]
    else:
        df01 = df0

    # Chose only certain wards
    ward_index = [i for i, j in enumerate(df01["ward_purpose"]) if j in search_value]
    df1 = df01.iloc[df01.index[ward_index], :]

    global input_data1
    input_data1 = input_data0.iloc[ward_index, :]

    global dff
    dff = df1.iloc[1:, : (13 + ncols)]

    return dbc.Container(
        [
            dbc.Label("Click a cell in the table:"),
            dash_table.DataTable(
                dff.to_dict("records"),
                [{"name": i, "id": i} for i in dff.iloc[:, 1:].columns],
                id="tbl",
                style_cell={"font-family": "sans-serif"},
                style_table={"overflowX": "auto"},
                editable=True,
                filter_action="native",
                sort_action="native",
                sort_mode="multi",
                row_selectable="multi",
                row_deletable=True,
                selected_rows=[],
                page_action="native",
                page_current=0,
                page_size=max_rows,
            ),
            dbc.Alert(id="tbl_out"),
        ]
    )


#### Callback to use table to return
@app.callback(Output("tbl_out", "children"), Input("tbl", "active_cell"))
def update_graphs(active_cell):

    # return dff.loc[active_cell['row'], active_cell['column_id']] if active_cell else "Click the table"
    if active_cell:
        # Pull what's in the box
        location = active_cell["row"]
        # dff.iloc[active_cell['row'], active_cell['column']]

        if active_cell["column"] > 7:

            return location

        else:
            return location
    else:
        return "Click the table"


@app.callback(Output("obs_graph", "figure"), Input("tbl", "active_cell"))
def obs_graph(active_cell):

    # return dff.loc[active_cell['row'], active_cell['column_id']] if active_cell else "Click the table"
    if active_cell:
        # Pull what's in the box
        location = dff.loc[dff.index[active_cell["row"]], ["hospital_visit_id"]]

        return plot_selected_columns("BP", location, extra_obs)

    else:
        return plot_selected_columns(
            "BP", results_df.hospital_visit_id.unique()[1], extra_obs
        )


@app.callback(Output("oxygen_graph", "figure"), Input("tbl", "active_cell"))
def oxygen_graph(active_cell):

    # return dff.loc[active_cell['row'], active_cell['column_id']] if active_cell else "Click the table"
    if active_cell:
        # Pull what's in the box
        location = dff.loc[dff.index[active_cell["row"]], ["hospital_visit_id"]]

        return plot_selected_columns("Resp", location, extra_obs)

    else:
        return plot_selected_columns(
            "Resp", results_df.hospital_visit_id.unique()[1], extra_obs
        )


@app.callback(Output("temp_graph", "figure"), Input("tbl", "active_cell"))
def temp_graph(active_cell):

    # return dff.loc[active_cell['row'], active_cell['column_id']] if active_cell else "Click the table"
    if active_cell:
        # Pull what's in the box
        location = dff.loc[dff.index[active_cell["row"]], ["hospital_visit_id"]]

        return plot_selected_columns("Temp", location, extra_obs)

    else:
        return plot_selected_columns(
            "Temp", results_df.hospital_visit_id.unique()[1], extra_obs
        )


@app.callback(Output("gcs_graph", "figure"), Input("tbl", "active_cell"))
def gcs_graph(active_cell):

    # return dff.loc[active_cell['row'], active_cell['column_id']] if active_cell else "Click the table"
    if active_cell:
        # Pull what's in the box
        location = dff.loc[dff.index[active_cell["row"]], ["hospital_visit_id"]]

        return plot_selected_columns("GCS", location, extra_obs)

    else:
        return plot_selected_columns(
            "GCS", results_df.hospital_visit_id.unique()[1], extra_obs
        )


@app.callback(Output("sats_graph", "figure"), Input("tbl", "active_cell"))
def sats_graph(active_cell):

    # return dff.loc[active_cell['row'], active_cell['column_id']] if active_cell else "Click the table"
    if active_cell:
        # Pull what's in the box
        location = dff.loc[dff.index[active_cell["row"]], ["hospital_visit_id"]]

        return plot_selected_columns("Sats", location, extra_obs)

    else:
        return plot_selected_columns(
            "Sats", results_df.hospital_visit_id.unique()[1], extra_obs
        )


# Generate tables of bloods
@app.callback(
    Output(component_id="LFTs", component_property="children"),
    Input("tbl", "active_cell"),
)
def generate_lfts(active_cell):

    if active_cell:
        # Pull what's in the box
        location = dff.loc[dff.index[active_cell["row"]], ["hospital_visit_id"]]

    else:
        location = dff.loc[dff.index[0], ["hospital_visit_id"]]

    bloods = [
        "date_time",
        "FBC",
        "HBGL",
        "PLT",
        "WCC",
        "NE",
        "LY",
        "CRP",
        "U+E",
        "NA",
        "K",
        "CREA",
        "GFR",
        "UREA",
        "Bone profile",
        "MG",
        "CCA",
        "PHOS",
        "LFTs",
        "ALB",
        "ALP",
        "ALT",
        "BILI",
        "Clotting",
        "INR",
        "PT",
        "APTT",
        "Point of care",
        "GLU",
        "Blood gas",
        "pH",
        "pO2",
        "pCO2",
        "K+",
        "Na+",
        "Lac",
        "Glu",
        "Urea",
        "Crea",
        "tHb",
    ]

    new_names = [
        "date_time",
        "FBC",
        "Hb",
        "Plt",
        "WCC",
        "Neuts",
        "Lymph",
        "CRP",
        "U+E",
        "Na",
        "K",
        "Cre",
        "eGFR",
        "Urea",
        "Bone profile",
        "Mg",
        "Cor Ca",
        "Phos",
        "LFTs",
        "Alb",
        "ALP",
        "ALT",
        "Bili",
        "Clotting",
        "INR",
        "PT",
        "APTT",
        "Point of care",
        "GLU",
        "Blood gas",
        "pH",
        "pO2",
        "pCO2",
        "K+",
        "Na+",
        "Lac",
        "Glu",
        "Urea",
        "Crea",
        "tHb",
    ]

    table = results_table(int(location), pivot_labs, bloods, new_names)

    return dbc.Container(
        [
            dbc.Label("Recent Bloods"),
            dash_table.DataTable(
                table.to_dict("records"),
                [{"name": i, "id": i} for i in table.columns],
                id="tbl2",
                style_cell={"font-family": "sans-serif"},
            ),
            dbc.Alert(id="tbl2"),
        ]
    )


# Generate tables of bloods
@app.callback(
    Output(component_id="U_Es", component_property="children"),
    Input("tbl", "active_cell"),
)
def generate_ues(active_cell):

    if active_cell:
        # Pull what's in the box
        location = dff.loc[dff.index[active_cell["row"]], ["hospital_visit_id"]]

    else:
        location = dff.loc[dff.index[0], ["hospital_visit_id"]]

    UEs = ["date_time", "NA", "K", "CREA", "GFR", "UREA"]
    table = results_table(int(location), pivot_labs, UEs)

    return dbc.Container(
        [
            dbc.Label("U_Es"),
            dash_table.DataTable(
                table.to_dict("records"),
                [{"name": i, "id": i} for i in table.columns],
                id="tbl3",
                style_cell={
                    "font-family": "sans-serif",
                    "overflow": "hidden",
                    "textOverflow": "ellipsis",
                    "minWidth": "180px",
                    "width": "180px",
                    "maxWidth": "180px",
                    "maxWidth": 0,
                },
                style_table={"overflowX": "auto"},
            ),
            dbc.Alert(id="tbl3"),
        ]
    )


@app.callback(
    Output("datatable-row-ids-container", "children"),
    Input("submit-button-state", "n_clicks"),
    State("tbl", "derived_virtual_selected_rows"),
)
def add_remove_from_PERRT(n_clicks, selected_row_ids):
    """Add or remove selected patients from the PERRT list

    Args:
        selected_row_ids (active cell): output from selected row ids from our big datatable at the top
    """
    if selected_row_ids:
        table = dff.loc[selected_row_ids, :]

    else:
        table = dff.loc[[0], :]
    return dbc.Container(
        [
            dbc.Label("datatable-row-ids"),
            dash_table.DataTable(
                table.to_dict("records"),
                [{"name": i, "id": i} for i in table.columns],
                id="tbl3",
                style_cell={
                    "font-family": "sans-serif",
                    "overflow": "hidden",
                    "textOverflow": "ellipsis",
                    "minWidth": "180px",
                    "width": "180px",
                    "maxWidth": "180px",
                    "maxWidth": 0,
                },
                style_table={"overflowX": "auto"},
            ),
            dbc.Alert(id="tbl3"),
        ]
    )


if __name__ == "__main__":
    app.run_server(debug=True)

# Think about putting the last 12 hours of observations underneath for when you click on a given patient? And or some additional information about them?
