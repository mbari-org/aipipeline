# heatmap_dash.py
import os
import logging
import datetime

import dotenv
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import dash
from dash import html, dcc

from aipipeline.db.tator.utils import init_api_project

# Set up logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
formatter = logging.Formatter("%(asctime)s %(levelname)s %(message)s")

# Load TATOR token
dotenv.load_dotenv()
token = os.getenv("TATOR_TOKEN")
if token is None:
    logger.error("TATOR_TOKEN environment variable must be set")
    exit(1)

# Configuration
config_dict = {
    "tator": {
        "host": "http://mantis.shore.mbari.org",
        "project": "901902-uavs",
    }
}

def load_localization_data(config_dict: dict, token: str, label: str = "Jelly"):
    host = config_dict["tator"]["host"]
    project_name = config_dict["tator"]["project"]
    api, project = init_api_project(host, token, project_name)

    medias = api.get_media_list(project.id, related_attribute_contains=[f"Label::{label}"])
    logger.info(f"Found {len(medias)} media in project {project.id} with label {label}")
    media_ids = [media.id for media in medias]

    all_localizations = api.get_localization_list(project.id, media_id=media_ids, attribute=[f"Label::{label}"])
    logger.info(f"Found {len(all_localizations)} localizations")

    if not all_localizations:
        return pd.DataFrame(), project.name

    df_loc = pd.DataFrame([loc.attributes for loc in all_localizations])
    df_media = pd.DataFrame([media.attributes for media in medias])
    df_media["media_ids"] = media_ids
    df_loc["media_ids"] = [loc.media for loc in all_localizations]
    df_loc = df_loc.merge(df_media, on="media_ids", how="left")

    df_loc.to_csv(f"{label}_loc_{datetime.datetime.now():%Y-%m-%d %H%M%S}.tsv", sep="\t")

    drop_cols = ["score", "exemplar", "saliency", "comment", "tator_user_sections", "altitude", "make", "cluster", "verified", "delete", "model", "FileType"]
    df_loc = df_loc.drop(columns=[c for c in drop_cols if c in df_loc.columns], errors="ignore")

    df_loc[f"LabelSum{label}"] = np.ones(len(df_loc))
    df_loc["longitude"] = -1 * df_loc["longitude"].astype(float)
    return df_loc, project.name

def create_heatmap_figure(df: pd.DataFrame, label: str, project_name: str):
    trace = go.Densitymapbox(
        lat=df["latitude"],
        lon=df["longitude"],
        z=df[f"LabelSum{label}"],
        radius=3,
        name=f"LabelSum{label}",
    )
    layout = go.Layout(
        title=f"{label} Density in {project_name} Project Missions",
        mapbox=dict(
            center=dict(lat=df["latitude"].mean(), lon=df["longitude"].mean()),
            zoom=11,
            style="carto-positron",
        ),
        margin={"r":0,"t":40,"l":0,"b":0}
    )
    return go.Figure(data=[trace], layout=layout)

# Load data at startup
label = "Jelly"
df, project_name = load_localization_data(config_dict, token, label)

# Dash app setup
app = dash.Dash(__name__)
app.title = "UAV Label Heatmap"

app.layout = html.Div([
    html.H2(f"{label} Localization Heatmap"),
    dcc.Graph(id='heatmap', figure=create_heatmap_figure(df, label, project_name))
])

if __name__ == "__main__":
    app.run_server(debug=True)
