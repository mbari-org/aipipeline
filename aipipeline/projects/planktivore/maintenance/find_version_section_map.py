import tator
import os

project_id = 12  # planktivore project in the database (mantis.shore.mbari.org)
version_section_lookup = {}

# Connect to Tator
token = os.getenv("TATOR_TOKEN")
api = tator.get_api(host='https://mantis.shore.mbari.org', token=token)

# Get all the versions
versions = api.get_version_list(project=project_id)
for version in versions:
    print(version)

# Get all the sections names
kwargs = {}
sections = api.get_section_list(project=project_id, **kwargs)
for section in sections:
    print(f'Section: {section.name} - {section.tator_user_sections}')


# For each version, get the localization count and a media if available
for version in versions:
    kwargs = {}
    kwargs["version"] = [f"{version.id}"]
    count = api.get_localization_count(project=project_id, type=17, **kwargs)

    print(f"Found: {count} localizations for version {version.name}")
    if count > 0:
        kwargs = {}
        kwargs["related_attribute"] = [f"$version::{version.id}"]
        media = api.get_media_list(project=project_id, start=0, stop=1, **kwargs)
        print(f"Media:  {media[0].name} - {media[0].attributes}")
        version_section_lookup[version.name] = media[0].attributes['tator_user_sections']


for key, value in version_section_lookup.items():
    section_name = [s.name for s in sections if s.tator_user_sections == value]
    print(f"Version: {key} - Section: {value} - {section_name[0] if len(section_name) > 0 else 'None'}")


# Should print out something like
#
# Version: mbari-ifcb2014-vitb16-20250318_20250320_002422 - Section: 23b85c28-ef19-11ef-98b8-0242ac130005 - aidata-export-03-low-mag
# Version: mbari-ifcb2014-vitb16-20250318_20250320_055433 - Section: 73f7b250-ef15-11ef-9982-0242ac130005 - aidata-export-02-high-mag
# Version: mbari-ifcb2014-vitb16-20250318_20250320_025000 - Section: 73f7b250-ef15-11ef-9982-0242ac130005 - aidata-export-02-high-mag