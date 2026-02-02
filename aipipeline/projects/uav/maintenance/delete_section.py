import os
from tator.openapi import tator_openapi

from tator.openapi.tator_openapi import TatorApi, CreateListResponse, CreateResponse  # type: ignore
from tator.openapi.tator_openapi.models import Project  # type: ignore
import tator  # type: ignore

project_id = 4  # planktivore project in the database (drone.mbari.org)
section_id = 281  # Section ID delete localizations for
box_type = 4  # Box type ID for planktivore localizations (e.g., 18 for bounding boxes)

# Connect to Tator
token = os.getenv("TATOR_TOKEN")
api = tator.get_api(host='https://drone.mbari.org', token=token)

config = tator_openapi.Configuration()
config.host = "drone.mbari.org"
config.verify_ssl = False
config.api_key['Authorization'] = token
config.api_key_prefix['Authorization'] = 'Token'

api = tator_openapi.TatorApi(tator_openapi.ApiClient(config))
api._create_media_list_impl = api.create_media_list

def create_media_list_wrapper(*args, **kwargs):
    response = api._create_media_list_impl(*args, **kwargs)
    if "id" in response and isinstance(response["id"], list):
        try:
            return CreateListResponse(**response)
        except Exception:
            return response
    try:
        return CreateResponse(**response)
    except Exception:
        return response

api.create_media_list = create_media_list_wrapper
def legacy_create_media(project, media_spec, **kwargs):
    return api.create_media_list(project, media_spec, **kwargs)

api.create_media = legacy_create_media

count = api.get_localization_count(project=project_id, type=box_type, section=section_id)

print(f"Found: {count} localizations for version {section_id}")
if count > 0:

    batch_size = 500
    while count > 0:
        deleted = api.delete_localization_list(project=project_id, section=section_id, start=0, stop=batch_size)
        print(f"Deleted {deleted if deleted is not None else 0} localizations in current batch.")
        count = api.get_localization_count(project=project_id, type=box_type, section=section_id)
        if count == 0:
            print(f"All localizations for section {section_id} have been deleted.")
            break