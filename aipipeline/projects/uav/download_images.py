from tator.openapi import tator_openapi
import tator

host = "https://drone.mbari.org"
token = "your_api_token" # Replace with your Tator API token
media_id = 84735  # Replace with your media ID

config = tator_openapi.Configuration()
config.host = host
config.verify_ssl = False  # Disable SSL verification for testing purposes
if token:
    config.api_key['Authorization'] = token
    config.api_key_prefix['Authorization'] = 'Token'

api = tator_openapi.TatorApi(tator_openapi.ApiClient(config))
media = api.get_media(media_id)
out_path = f'/tmp/{media.name}'
for progress in tator.util.download_media(api, media, out_path):
    print(f"Download {out_path} progress: {progress}%")

