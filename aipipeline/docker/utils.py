import logging
import os
from typing import List

import docker
import torch

logger = logging.getLogger(__name__)
formatter = logging.Formatter("%(asctime)s %(levelname)s %(message)s")
# Also log to the console
console = logging.StreamHandler()
logger.addHandler(console)
logger.setLevel(logging.DEBUG)

MLDEVOPS_UID = os.getuid()
MLDEVOPS_GID = os.getgid()
ENVIRONMENT = os.getenv("ENVIRONMENT") if os.getenv("ENVIRONMENT") else None


def run_docker(image: str, name: str, args_list: List[str], env_list: List[str] = None, bind_volumes: dict = None, auto_remove: bool = True):
    try:
        client = docker.from_env()
    except Exception as e:
        logger.error(f"Error connecting to docker: {e}. Is the docker daemon running?")
        exit(-1)

    # Check the name for invalid characters, e.g. / : and replace https:// with blank
    if not name.isalnum():
        logger.error(f"Invalid container name: {name}. Only alphanumeric characters are allowed. Trying to replace invalid characters.")
        name = name.replace("https://", "").replace("/", "_").replace(":", "_")

    if bind_volumes is None:
        bind_volumes = {}

    if env_list is None:
        env_list = []

    args = " ".join(args_list)
    logger.info(f'Running {image} with mount {bind_volumes} '
                f'user {f"{MLDEVOPS_UID}:{MLDEVOPS_GID}"} '
                f'args {args} and naming image to {name}')
    if ENVIRONMENT == "testing":
        logger.info(f"Testing environment, skipping docker run")
        return
    else:
        # Stop any existing containers with the same name
        for container in client.containers.list(all=True):
            if container.name == name:
                logger.info(f"Stopping existing container: {name}")
                container.stop()
                logger.info(f"Removing existing container: {name}")
                container.remove()

        docker_args = {
            "image": image,
            "name": name,
            "command": args,
            "auto_remove": auto_remove,
            "volumes": bind_volumes,
            "environment": env_list,
            "detach": True,
            "network_mode": "host",
            "user": f"{MLDEVOPS_UID}:{MLDEVOPS_GID}"
        }

        if len(bind_volumes) > 0:
            docker_args["volumes"] = bind_volumes

        if "cuda" in image:
            # Check if CUDA is available using
            if not torch.cuda.is_available():
                logger.error(f"Sorry, CUDA not available and it is required for the docker image {image}.")
                return
            # Add the GPU device
            docker_args["runtime"] = "nvidia"
            docker_args["device_requests"] = [docker.types.DeviceRequest(count=-1, capabilities=[["gpu"]])]
            docker_args["environment"] = ["CUDA_VISIBLE_DEVICES=0,1"]

        try:
            container = client.containers.run(**docker_args)
            return container
        except Exception as e:
            logger.error(f"Error running docker: {e}")
            return None
