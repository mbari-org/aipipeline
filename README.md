[![MBARI](https://www.mbari.org/wp-content/uploads/2014/11/logo-mbari-3b.png)](http://www.mbari.org)
[![Python](https://img.shields.io/badge/language-Python-blue.svg)](https://www.python.org/downloads/)

*aipipeline* is a library for running ai pipelines and monitoring the performance of the pipelines,
e.g. accuracy, precision, recall, F1 score. This may include object detection, 
clustering, classification, and vector search algorithms. It is designed to be used for a number of projects at MBARI 
that require advanced workflows to process large amounts of images or video.

### See the [MBARI AI documentation](https://docs.mbari.org/internal/ai) for more information on the tools and services used in the pipelines.

---
Example plots from the t-SNE, confusion matrix and accuracy analysis of examplar data.

![example tsne plots](docs/imgs/tsne_plot_example.png)
![example cm_ac](docs/imgs/cm_ac_example.png)

--- 
## Requirements

Three tools are required to run the code in this repository:

### [Anaconda](https://www.anaconda.com/products/distribution) environment
This is a package manager for python.  We recommend using the [Miniconda](https://docs.conda.io/en/latest/miniconda.html) version of Anaconda.
Install on **Mac OS X** with the following command:
```shell
brew install miniconda
```
or on **Ubuntu** with the following command:
```shell
sudo apt install miniconda
```
### [Docker](https://www.docker.com)
This is a containerization tool that allows you to run code in a container.

### [just](https://github.com/casey/just) tool. 
This is a handy tool for running scripts in the project. This is easier to use than `make` 
and more clean than bash scripts. Try it out!

Install on **Mac OS X** with the following command:
```shell
port install just
```
or on **Ubuntu** with the following command:
```shell
sudo apt install just
```

## Installation 

Clone the repository and run the setup command.
```shell
git clone http://github.com/mbari-org/aipipeline.git
cd aipipeline
just setup
``` 
Sensitive information is stored in a .env file in the root directory of the project,
so you need to create a .env file with the following contents in the root directory of the project:

```shell
TATOR_TOKEN=your_api_token
REDIS_PASSWORD=your_redis_password
ENVIRONMENT=testing or production
```


## Usage

Recipes are available to run the pipelines.  To see the available recipes, run the following command:
```shell
just list
```
# Available Recipes

| **Recipe**                          | **Description**                                                                                          |
|-------------------------------------|----------------------------------------------------------------------------------------------------------|
| `list`                              | List recipes.                                                                                           |
| `install`                           | Setup the environment.                                                                                  |
| `cp-env`                            | Copy the default `.env` file to the project.                                                            |
| `update_trackers`                   | Update the environment. Run this command after checking out any code changes.                           |
| `update-env`                        | Update environment.                                                                                     |
| `cp-core`                           | Copy core dev code to the project on Doris.                                                             |
| `cp-dev-uav`                        | Copy UAV dev code to the project on Doris.                                                              |
| `cp-dev-bio`                        | Copy bio dev code to the project on Doris.                                                              |
| `cp-dev-i2map`                      | Copy i2map dev code to the project on Doris.                                                            |
| `plot-tsne-vss project='uav'`       | Generate a t-SNE plot of the VSS database.                                                              |
| `optimize-vss project='uav'`        | Optimize the VSS database.                                                                              |
| `calc-acc-vss project='uav'`        | Calculate the accuracy of the VSS database; run after download, then optimize.                          |
| `reset-vss-all`                     | Reset the VSS database, removing all data. Proceed with caution!                                        |
| `reset-vss project='uav'`           | Reset the VSS database for the specified project (e.g., `uav`).                                         |
| `remove-vss project='uav'`          | Remove an entry from the VSS database (e.g., `remove-vss i2map --doc 'doc:marine organism:*'`).         |
| `init-vss project='uav'`            | Initialize the VSS database for a project.                                                              |
| `load-vss project='uav'`            | Load precomputed exemplars into the VSS database.                                                       |
| `load-cfe-isiis-videos`             | Load CFE ISII mission videos listed in `missions-to-process.txt`.                                       |
| `cluster-uav`                       | Cluster missions listed in `missions-to-process.txt`.                                                   |
| `detect-uav`                        | Detect missions listed in `missions-to-process.txt`.                                                    |
| `detect-uav-test`                   | Detect mission data for testing purposes.                                                               |
| `load-uav-images`                   | Load UAV mission images listed in `missions-to-process.txt`.                                            |
| `load-uav type="cluster"`           | Load UAV detections or clusters from `missions-to-process.txt`.                                         |
| `fix-uav-metadata`                  | Fix UAV metadata for latitude, longitude, and altitude.                                                 |
| `compute-saliency project='uav'`    | Compute saliency for downloaded VOC data and update the Tator database.                                 |
| `crop project='uav'`                | Crop detections from VOC-formatted downloads.                                                           |
| `download-crop project='uav'`       | Download and crop images.                                                                               |
| `download project='uav'`            | Download only.                                                                                          |
| `predict-vss project='uav'`         | Predict images using the VSS database.                                                                  |
| `run-ctenoA-test`                   | Run strided inference on a single video.                                                                |
| `run-ctenoA-prod`                   | Run strided inference on a collection of videos listed in a TSV file.                                   |
| `run-mega-inference`                | Run mega strided inference on a single video.                                                           |
| `run-mega-track-bio-video`          | Run mega strided tracking for a single video in the bio project.                                        |
| `run-mega-track-bio-dive`           | Run mega strided tracking for an entire dive in the bio project.                                        |
| `run-mega-track-i2map-video`        | Run mega strided tracking for a single video in the i2map project.                                      |
| `run-mega-track-test-1min`          | Run mega strided tracking on a single video to test the pipeline.                                       |
| `run-mega-track-test-fastapiyv5`    | Run mega strided tracking on a single video with FastAPI.                                               |
| `cluster-i2mapbulk`                 | Run inference and clustering on i2map bulk data.                                                        |
| `load-i2mapbulk`                    | Load i2map bulk data using a `cluster_detections.csv` file.                                             |
| `gen-cfe-data`                      | Generate training data for the CFE project.                                                             |
| `gen-i2map-data`                    | Generate training data for the i2map project.                                                           |
| `gen-i2mapbulk-data`                | Generate training data for i2map from bulk server data.                                                 |
| `gen-uav-data`                      | Generate training data for the UAV project.                                                             |
| `gen-stats-csv project='UAV'`       | Generate training data statistics.                                                                      |

--

### Related projects

- [aidata](https://github.com/mbari-org/aidata) -A tool to extract, transform, load and download operations on AI data.
- [sdcat](https://github.com/mbari-org/sdcat) - Sliced Detection and Clustering Analysis Toolkit; a tool to detect and cluster objects in images.
- [deepsea-ai](https://github.com/mbari-org/deepsea-ai) - A tool to train and run object detection and tracking on video at scale in the cloud (AWS).
- [fastapi-yolov5](https://github.com/mbari-org/fastapi-yolov5) - A RESTful API for running YOLOv5 object detection models on images either locally or in the cloud (AWS).
- [fastapi-vss](https://github.com/mbari-org/fastapi-vss) - A RESTful API for vector similarity search using foundational models.
- [fastapi-tator](https://github.com/mbari-org/fastapi-tator) - A RESTful API server for bulk operations on a Tator annotation database.

**updated: 2025-01-13**