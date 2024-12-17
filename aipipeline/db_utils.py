# aipipeline, Apache-2.0 license
# Filename: aipipeline/db_utils.py
# Description: Database utilities
import logging
from datetime import datetime
from typing import Tuple, Any

import tator
from tator.openapi.tator_openapi import TatorApi, Project

logger = logging.getLogger(__name__)

formatter = logging.Formatter("%(asctime)s %(levelname)s %(message)s")
# Also log to the console
console = logging.StreamHandler()
logger.addHandler(console)
logger.setLevel(logging.INFO)
# and log to file
now = datetime.now()
log_filename = f"pred_utils_{now:%Y%m%d}.log"
handler = logging.FileHandler(log_filename, mode="w")
handler.setFormatter(formatter)
handler.setLevel(logging.DEBUG)
logger.addHandler(handler)


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
