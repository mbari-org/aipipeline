# aipipeline, Apache-2.0 license
# Filename: ai_pipeline/prediction/leaf_init.py
# Description: This script is used to create a tree structure in Tator. It reads the tree structure from a yaml file and creates the tree structure in Tator.
from datetime import datetime

from aipipeline.db.utils import init_api_project
from aipipeline.config_setup import setup_config, parse_labels
import logging
import os
import dotenv
import sys
from textwrap import dedent

# Secrets
dotenv.load_dotenv()
TATOR_TOKEN = os.getenv("TATOR_TOKEN")

logger = logging.getLogger(__name__)
formatter = logging.Formatter("%(asctime)s %(levelname)s %(message)s")
# Also log to the console
console = logging.StreamHandler()
logger.addHandler(console)
logger.setLevel(logging.INFO)
# and log to file
now = datetime.now()
log_filename = f"leaf_init_{now:%Y%m%d}.log"
handler = logging.FileHandler(log_filename, mode="w")
handler.setFormatter(formatter)
handler.setLevel(logging.DEBUG)
logger.addHandler(handler)


def _create_children(api, tree, project, type_id, parent):
    children = tree.get('children')
    if children:
        specs = [{'project': project,
                  'type': type_id,
                  'name': child['name'],
                  'parent': parent} for child in children]
        logger.info(f"Creating {len(children)} children for parent {parent}")
        response = api.create_leaf_list(project, body=specs)
        for child_id, child in zip(response.id, children):
            logger.info(f"Created child {child['name']} with id {child_id}")
            _create_children(api, child, project, type_id, child_id)

if __name__ == "__main__":
    import os
    import argparse

    parser = argparse.ArgumentParser(description=dedent('''\
      Creates a label hierarchy with Leaf objects.

      This utility accepts a yaml file with the following format:

      name: taxa # The name of the hierarchy. Can be any string.
      children:
      - name: Pinniped
        children:
        - name: Seal
        - name: Sea Lion
      - name: Fish
        children:
        - name: Salmon
        - name: Tuna

      Once leaves are created, the autocomplete service will be available at:
      https://<domain>/rest/Leaves/Suggestion/<project_name>.taxa/<project>

      To narrow scope of the autocomplete service (for example just Pinniped), use the:
      https://<domain>/rest/Leaves/Suggestion/<project_name>.taxa.Pinniped/<project>

      To use an autocomplete service on a string attribute type, set the autocomplete field
      as follows:
      {...
       'autocomplete': {'serviceUrl': 'https://<domain>/rest/Leaves/Suggestion/<project_name>.taxa/<project>'},
       ...}

      '''), formatter_class=argparse.RawTextHelpFormatter)
    parser.add_argument("--config", required=True, help="Config file path")
    parser.add_argument("--labels", required=True, help="Labels file path")
    parser.add_argument('--type-id', help="Leaf type ID.", type=int, required=True)
    args = parser.parse_args()
    config_yaml = os.path.abspath(args.config)
    labels_yaml = os.path.abspath(args.labels)

    conf_files, config_dict = setup_config(config_yaml)
    label_tree_dict = parse_labels(labels_yaml)
    TATOR_TOKEN = os.environ["TATOR_TOKEN"]
    host = config_dict["tator"]["host"]
    project_name = config_dict["tator"]["project"]
    api, project_id = init_api_project(host=host, token=TATOR_TOKEN, project=project_name)

    # Get the leaf type.
    leaf_type = api.get_leaf_type(args.type_id)
    project = leaf_type.project

    # Create root leaf.
    root_spec = {
        'project': project,
        'type': leaf_type.id,
        'name': label_tree_dict['name'],
    }

    # Check if the root already exists
    leaf_id = None
    leaves = api.get_leaf_list(project=project, name=root_spec['name'])
    for leaf in leaves:
        if leaf.name == root_spec['name']:
            logger.info(f"Root leaf {root_spec['name']} already exists with id {leaf.id}. Delete it to recreate.")
            exit(0)

    logger.info(f"Creating root leaf {root_spec['name']}")
    response = api.create_leaf_list(project=project, body=root_spec)
    leaf_id = response.id[0]

    # Create children recursively.
    _create_children(api, label_tree_dict, project, leaf_type.id, leaf_id)

    logger.info("Label tree setup completed.")
    url_auto_complete = f"http://{host}/rest/Leaves/Suggestion/{project_name}.{label_tree_dict['name']}/{project}"
    logger.info(f"Enable autocomplete for the entire tree with the sourceUrl: {url_auto_complete}")