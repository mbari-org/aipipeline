# aipipeline, Apache-2.0 license
# Filename: projects/uav-901902/scripts/report.py
# Description:  Generate reports for the uav-901902 project
import logging

import dotenv
import pandas as pd

from aidata.generators.coco import get_media
from submodules.aidata.aidata.plugins.loaders.tator.common import init_api_project, find_project

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
formatter = logging.Formatter("%(asctime)s %(levelname)s %(message)s")


def gen_report(config_dict: dict, token: str):
    """
    Generate a report of the annotations in the database
    """
    host = config_dict["tator"]["host"]
    project_name = config_dict["tator"]["project"]

    # Get the api
    api, project = init_api_project(host, token, project_name)

    # Get the annotations from the database
    num_annotations = 1000
    total_annotations = api.get_num_localizations(project.id)
    logger.info(f"Found {total_annotations} annotations in project {project.id}")

    all_localizations = []
    for offset in range(0, total_annotations, num_annotations):
        localizations = api.get_localizations_list(project.id, offset=offset, limit=num_annotations)
        all_localizations.extend(localizations)

    df_loc = pd.DataFrame(all_localizations)

    # Extract the unique labels from the list
    unique_labels = df_loc["Label"].unique()

    logger.info(f"Found {len(unique_labels)} labels in project {project.id}")

    # Get all the unique media ids as a list
    media_ids = df_loc["media"].unique().astype(int).tolist()

    logger.info(f"Found {len(media_ids)} media in project {project.id}")

    # Get all the media metadata for those ids
    df_media = get_media(api, project.id, media_ids)

    # Drop columns 'comment', 'delete', 'saliency',
    df_loc = df_loc.drop(["comment", "delete", "saliency"], axis=1)
    df_loc = df_loc.merge(df_media, left_on="media", right_on="id")

    # Drop any row with a latitude and longitude of 0
    df_loc["latitude"] = df_loc["latitude"].astype(float)
    df_loc["longitude"] = -1 * df_loc["longitude"].astype(float)
    df_loc = df_loc[(df_loc["latitude"] != 0.0) | (df_loc["longitude"] != 0.0)]

    # Plot the annotation heat map with the lat and lon
    import plotly.express as px
    import plotly.io as pio

    pio.renderers.default = "firefox"
    import plotly.graph_objects as go
    # Convert the lat/lon to floats

    # Drop the labels with Reflector in them
    label = ["Seagull"]
    # df_loc = df_loc[~df_loc['Label'].str.contains('Reflections')]
    # df_loc = df_loc[~df_loc['Label'].str.contains('Foam')]
    # df_loc = df_loc[~df_loc['Label'].str.contains('Delete')]
    # df_loc = df_loc[~df_loc['Label'].str.contains('Unknown')]

    # Add a column that is the sum of the labels of Seagull
    df_loc["LabelSumSeagull"] = df_loc["Label"].apply(lambda x: 1 if x in "Seagull" else 0)
    df_loc["LabelSumPinniped"] = df_loc["Label"].apply(lambda x: 1 if x in "Pinniped" else 0)
    df_loc["LabelSumKelp"] = df_loc["Label"].apply(lambda x: 1 if x in "Kelp" else 0)
    df_loc["LabelSumJelly"] = df_loc["Label"].apply(lambda x: 1 if x in "Jelly" else 0)
    #
    # fig = px.density_mapbox(df_loc,
    #                         lat='latitude',
    #                         lon='longitude',
    #                         z=['LabelSumSeagull', 'LabelSumKelp'],
    #                         zoom=10,
    #                         )
    # fig.update_layout(mapbox_style="carto-darkmatter")
    # fig.update_layout(title_text=f"{label} Density in {project.name} Project Missions")
    # fig.show()

    traces = []
    for column in ["LabelSumSeagull", "LabelSumJelly"]:
        trace = go.Densitymapbox(
            lat=df_loc["latitude"],
            lon=df_loc["longitude"],
            z=df_loc[column],
            radius=1,
            name=column,
        )
        traces.append(trace)

    # Layout settings
    layout = go.Layout(
        mapbox=dict(
            center=dict(lat=df_loc["latitude"].mean(), lon=df_loc["longitude"].mean()),
            zoom=4,
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
            "host": "https://mantis.shore.mbari.org",
            "project": "901902-uavs",
        }
    }
    if token is None:
        logger.error("TATOR_TOKEN environment variable must be set")
        exit(1)

    gen_report(config_dict, token)
