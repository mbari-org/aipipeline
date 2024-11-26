# aipipeline, Apache-2.0 license
# Filename: projects/uav/reports/heatmap.py
# Description:  Generate reports for the uav-901902 project
import datetime
import logging

import dotenv
import pandas as pd
import plotly.express as px
import plotly.io as pio
import plotly.graph_objects as go
import numpy as np
pio.renderers.default = "firefox"

from deps.aidata.aidata.plugins.loaders.tator.common import init_api_project

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
formatter = logging.Formatter("%(asctime)s %(levelname)s %(message)s")


def gen_report(config_dict: dict, token: str, label: str = "Jelly"):
    """
    Generate a report of the label annotations in the database
    """
    host = config_dict["tator"]["host"]
    project_name = config_dict["tator"]["project"]

    # Get the api
    api, project = init_api_project(host, token, project_name)

    # Get the annotations for Jelly in the project
    # Since there are no labels in the project, we do not need to paginate here
    medias = api.get_media_list(project.id, related_attribute_contains=[f"Label::{label}"])
    logger.info(f"Found {len(medias)} media in project {project.id} with label {label}")

    media_ids = [media.id for media in medias]
    all_localizations = api.get_localization_list(project.id, media_id=media_ids, attribute=[f"Label::{label}"])
    logger.info(f"Found {len(all_localizations)} localizations")

    df_loc = pd.DataFrame([loc.attributes for loc in all_localizations])

    # Get all the media metadata for those ids
    df_media = pd.DataFrame([media.attributes for media in medias])
    df_media["media_ids"] = media_ids

    # Add a column for the media id which we can use to merge the dataframes
    ids = [loc.media for loc in all_localizations]
    df_loc["media_ids"] = ids

    df_loc = df_loc.merge(df_media, left_on="media_ids", right_on="media_ids")

    # Save the data to a tsv file
    df_loc.to_csv(f"{label}_loc_updated{datetime.datetime.now()}.tsv", sep="\t")

    # Drop the columns that are not needed, and keep the lat and lon
    df_loc = df_loc.drop(columns=["score", "exemplar", "saliency", "comment", "tator_user_sections", "altitude", "make", "cluster", "verified", "delete","model", "FileType"])


    df_loc[f"LabelSum{label}"] = np.ones(len(df_loc))

    df_loc["longitude"] = -1*df_loc["longitude"].astype(float)

    # Plot the annotation heat map with the lat and lon
    traces = []
    for column in [f"LabelSum{label}"]:
        trace = go.Densitymapbox(
            lat=df_loc["latitude"],
            lon=df_loc["longitude"],
            z=df_loc[column],
            radius=3,
            name=column,
        )
        traces.append(trace)

    # Layout settings
    layout = go.Layout(
        title=f"{label} Density in {project.name} Project Missions",
        mapbox=dict(
            center=dict(lat=df_loc["latitude"].mean(), lon=df_loc["longitude"].mean()),
            zoom=11,
            style="carto-positron",
        )
    )

    # Create figure and plot
    fig = go.Figure(data=traces, layout=layout)
    fig.show()


if __name__ == "__main__":
    import os

    dotenv.load_dotenv()
    token = os.getenv("TATOR_TOKEN")
    config_dict = {
        "tator": {
            "host": "http://mantis.shore.mbari.org",
            "project": "901902-uavs",
        }
    }
    if token is None:
        logger.error("TATOR_TOKEN environment variable must be set")
        exit(1)

    gen_report(config_dict, token)
