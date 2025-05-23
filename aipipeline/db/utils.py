import logging
from datetime import datetime
from typing import Any, Dict, List, Tuple

import pytz
import tator
from tator.openapi.tator_openapi import TatorApi, Project

from aipipeline.prediction.library import logger

logger = logging.getLogger(__name__)
formatter = logging.Formatter("%(asctime)s %(levelname)s %(message)s")
now = datetime.now()
log_filename = f"db_utils_{now:%Y%m%d}.log"
handler = logging.FileHandler(log_filename, mode="w")
handler.setFormatter(formatter)
handler.setLevel(logging.DEBUG)
logger.addHandler(handler)

def get_box_type(api: TatorApi, project_id: int) -> Any | None:
    types = api.get_localization_type_list(project=project_id)
    for t in types:
        if t.name == 'Box':
            return t
    return None


def get_video_type(api: TatorApi, project_id: int) -> Any | None:
    types = api.get_media_type_list(project=project_id)
    for t in types:
        if t.name == 'Video':
            return t
    return None


def get_media_ids(
        api: tator.api,
        project: Project,
        media_type: int,
        **kwargs
        ) -> Dict[str, int]:
        """
        `Get the media ids that match the filter
        :param api:  tator api
        :param kwargs:  filter arguments to pass to the get_media_list function
        :return: media name to id mapping
        """
        media_map = {}
        media_count = api.get_media_count(project=project.id, type=media_type, **kwargs)
        if media_count == 0:
            logger.err(f"No media found in project {project.name}")
            return media_map
        batch_size = min(1000, media_count)
        logger.debug(f"Searching through {media_count} medias with {kwargs}")
        for i in range(0, media_count, batch_size):
            media = api.get_media_list(project=project.id, start=i, stop=i + batch_size, **kwargs)
            logger.info(f"Found {len(media)} medias with {kwargs} {i} {i + batch_size}")
            for m in media:
                media_map[m.name] = m.id
                logger.debug(f"Found {len(media_map)} medias with {kwargs}")
        return media_map


def attribute_to_dict(attribute):
    """Converts a Tator attribute to a dictionary."""
    return {attr.key: attr.value for attr in attribute}

def load_bulk_boxes(project_id, api, specs):
    """
    Bulk load localization boxes associated with a media into the database
    :param api: Tator API
    :param project_id: project ID
    :param specs: List of localization specs
    :return:
    """
    logging.info(f"Loading {len(specs)} localizations into Tator")
    chunk_size = min(200, len(specs))
    loc_ids = [
        new_id
        for response in tator.util.chunked_create(
            api.create_localization_list, project_id, chunk_size=chunk_size, body=specs
        )
        for new_id in response.id
    ]
    logging.info(f"Loaded {len(loc_ids)} localizations into Tator")
    return loc_ids


def format_attributes(attributes: dict, attribute_mapping: dict) -> dict:
    """Formats attributes according to the attribute mapping."""
    attributes_ = {}
    for a_key, a_value in attributes.items():
        for m_key, m_value in attribute_mapping.items():
            a_key = a_key.lower()
            m_key = m_key.lower()
            m_key = m_key.lower()
            if a_key == m_key:
                if m_value["type"] == "datetime":
                    # Truncate datetime to milliseconds, convert to UTC, and format as ISO 8601
                    if isinstance(attributes[a_key], datetime):
                        dt_utc = attributes[a_key].astimezone(pytz.utc)
                        try:
                            dt_str = dt_utc.strftime("%Y-%m-%dT%H:%M:%S.%fZ")
                            dt_str = dt_str[:-3] + "Z"
                        except ValueError:
                            dt_str = dt_utc.strftime("%Y-%m-%dT%H:%M:%SZ")
                    else:
                        dt_str = attributes[a_key]
                    attributes_[a_key] = dt_str
                # Convert boolean to string
                if m_value["type"] == "bool":
                    if attributes[m_key] == 1:
                        attributes_[m_key] = "True"
                    else:
                        attributes_[m_key] = "False"
                if m_value["type"] == "float":
                    if attributes[m_key] is None:
                        attributes_[m_key] = -1
                    else:
                        attributes_[m_key] = float(attributes[m_key])
                if m_value["type"] == "int":
                    if attributes[m_key] is None:
                        attributes_[m_key] = -1
                    else:
                        attributes_[m_key] = int(attributes[m_key])
                if m_value["type"] == "string":
                    if m_key == "cluster":
                        attributes_[m_key] = f"Unknown C{attributes[m_key]}"
                    else:
                        attributes_[m_key] = str(attributes[m_key])
    return attributes_


def _find_types(api, project):
    """Returns dict containing mapping from dtype to type."""
    loc_types = api.get_localization_type_list(project)
    state_types = api.get_state_type_list(project)
    loc_types = {loc_type.dtype: loc_type for loc_type in loc_types}
    state_types = {state_type.association: state_type for state_type in state_types}
    return loc_types, state_types


def init_api_project(host: str, token: str, project_name: str) -> tuple[Any, int]:
    """
    Fetch the Tator API and project
    :param host: hostname, e.g. localhost
    :param token: api token
    :param project_name:  project name
    :return: Tator API and project id
    """
    try:
        logger.info(f"Connecting to Tator at {host}")
        api = tator.get_api(host, token)
    except Exception as e:
        raise e

    logger.info(f"Searching for project {project_name} on {host}.")
    projects = api.get_project_list()
    logger.info(f"Found {len(projects)} projects")
    project = None
    for p in projects:
        if p.name == project_name:
            project = p
            break
    if project is None:
        raise Exception(f"Could not find project {project_name}")

    logger.info(f"Found project {project.name} with id {project.id}")
    if project is None:
        raise Exception(f"Could not find project {project}")

    return api, project.id


def gen_spec(
    box: List[float],
    version_id: int,
    label: str,
    frame_number: int,
    type_id: int,
    media_id: int,
    project_id: int,
    attributes: dict,
) -> dict:
    """
    Generate a media spec for Tator
    :param box: box data [x1, y1, x2, y2]
    :param version_id: Version ID to associate to the localization.
    :param label: label of the box
    :param width: width of the image
    :param height: height of the image
    :param frame_number: frame number in the video (if video) 0-indexed, or 0 if image
    :param media_id: media ID
    :param type_id: box type ID
    :param project_id: project ID
    :param attributes: additional attributes
    :return: The localization spec
    """
    attributes["Label"] = label
    x1, y1, x2, y2 = box
    x = x1
    y = y1
    w = x2 - x1
    h = y2 - y1
    if w < 0.0:
        logger.info(f"Localization width negative {w} {box}")
        w = 0.0
    if h < 0.0:
        logger.info(f"Localization height negative {h} {box}")
        h = 0.0
    if w > 1.0:
        logger.info(f"Localization height too large {w} {box}")
        w = 1.0
    if h > 1.0:
        logger.info(f"Localization width too large {h} {box}")
        h = 1.0
    if w + x > 1.0:
        offset = 1.0 - (w + x)
        logger.info(f"Localization too large {x}+{w} by {offset} {box}")
        w -= offset
    if h + y > 1.0:
        offset = 1.0 - (h + y)
        logger.info(f"Localization too large {y}+{h} by {offset} {box}")
        h -= offset

    spec = {
        "version": version_id,
        "type": type_id,
        "media_id": media_id,
        "project": project_id,
        "x": x,
        "y": y,
        "width": w,
        "height": h,
        "frame": frame_number,
        "attributes": attributes,
    }
    return spec


def get_version_id(api: TatorApi, project_id: int, version: str) -> int:
    """
    Get the version ID for the given project
    :param api: :class:`TatorApi` object
    :param project_id: Project is
    :param version: version name
    :return: version ID
    """
    versions = api.get_version_list(project=project_id)
    logger.debug(versions)

    # Find the version by name
    version_match = [v for v in versions if v.name == version]
    if len(version_match) == 0:
        logger.error(f"Could not find version {version}")
        raise ValueError(f"Could not find version {version} in possible versions {versions}")
    if len(version_match) > 1:
        logger.error(f"Found multiple versions with name {version}")
        raise ValueError(f"Found multiple versions with name {version}")
    return version_match[0].id


def init_api_project(host: str, token: str, project: str) -> Tuple[TatorApi, tator.models.Project]:
    """
    Fetch the Tator API and project
    :param host: hostname, e.g. localhost
    :param token: api token
    :param project:  project name
    :return:
    """
    try:
        logger.info(f"Connecting to Tator at {host}")
        api = tator.get_api(host, token)
    except Exception as e:
        raise (e)

    logger.info(f"Searching for project {project} on {host}.")
    tator_project = find_project(api, project)
    logger.info(f"Found project {tator_project.name} with id {tator_project.id}")
    if tator_project is None:
        raise Exception(f"Could not find project {project}")

    return api, tator_project


def find_project(api: TatorApi, project_name: str) -> Any | None:
    """
    Find the project with the given name
    :param api: :class:`TatorApi` object
    :param project_name: Name of the project
    """
    projects = api.get_project_list()
    logger.info(f"Found {len(projects)} projects")
    for p in projects:
        if p.name == project_name:
            return p
    return None
