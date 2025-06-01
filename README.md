[![MBARI](https://www.mbari.org/wp-content/uploads/2014/11/logo-mbari-3b.png)](http://www.mbari.org)
[![Python](https://img.shields.io/badge/language-Python-blue.svg)](https://www.python.org/downloads/)

*aipipeline* is a library for running ai pipelines and monitoring the performance of the pipelines,
e.g. accuracy, precision, recall, F1 score. This may include object detection, 
clustering, classification, and vector search algorithms. It is designed to be used for a number of projects at MBARI 
that require advanced workflows to process large amounts of images or video.  After workflows are developed,
they may be moved to the project repositories for production use.  The roadmap includes adding the core functionality
of some of the processing components to more broad use in the MBARI AI ecosystem.

### See the [MBARI Internal AI documentation](https://docs.mbari.org/internal/ai) for more information on the tools and services used in the pipelines.

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
| Command | Description |
|---------------------------------------------|-------------|
| list                                        | List recipes |
| install                                     | Setup the environment |
| cp-env                                      | Copy the default .env file to the project |
| update_trackers                             | Update the environment. Run this command after checking out any code changes |
| update-env                                  | Update environment |
| cp-core                                     | Copy core dev code to the project on doris |
| cp-dev-cfe                                  | Copy cfe dev code to the project on doris |
| cp-dev-ptvr                                 | Copy planktivore dev code to the project on doris |
| cp-dev-uav                                  | Copy uav dev code to the project on doris |
| cp-dev-bio                                  | Copy bio dev code to the project on doris |
| cp-dev-i2map                                | Copy i2map dev code to the project on doris |
| init-labels project='uav' leaf_type_id='19' | Initialize labels for quick lookup, e.g. just init-labels uav 19 |
| plot-tsne-vss project='uav'                 | Generate a tsne plot of the VSS database |
| optimize-vss project='uav' *more_args=""    | Optimize the VSS database |
| calc-acc-vss project='uav'                  | Calculate the accuracy of the VSS database; run after download, then optimize |
| reset-vss-all                               | Reset the VSS database, removing all data. Proceed with caution!! |
| reset-vss project='uav'                     | Reset the VSS database, removing all data |
| remove-vss project='uav' *more_args=""      | Remove an entry from the VSS database |
| init-vss project='uav' *more_args=""        | Initialize the VSS database for a project |
| load-vss project='uav'                      | Load already computed exemplars into the VSS database |
| load-cfe-isiis-videos missions=""           | Load cfe ISII mission videos |
| cluster-cfe-isiis-frames roi_dir=...        | Cluster CFE ISIIS hawaii mission frames |
| load-ptvr-images images='tmp/roi' *args=""  | Load planktivore ROI images |
| cluster-ptvr-images *more_args=""           | Cluster planktivore ROI images |
| load-ptvr-clusters clusters='tmp/...' *args="" | Load planktivore ROI clusters |
| rescale-ifcb-images collection="2014"       | Rescale planktivore ROI images |
| rescale-ptvr-images collection="..."        | Rescale planktivore ROI images |
| download-rescale-ptvr-images collection="..." | Download and rescale planktivore ROI images |
| cluster-uav *more_args=""                   | Cluster mission in UAV project |
| detect-uav *more_args=""                    | Detect mission in UAV project |
| detect-uav-test                             | Detect mission data for testing |
| load-uav-images                             | Load UAV mission images |
| load-uav type="cluster"                     | Load UAV detections/clusters |
| fix-uav-metadata                            | Fix UAV metadata lat/lon/alt |
| compute-saliency project='uav' *args=""     | Compute saliency for downloaded VOC data |
| crop project='uav' *more_args=""            | Crop detections from VOC formatted downloads |
| download-crop project='uav' *more_args=""   | Download and crop with defaults |
| download project='uav'                      | Download only |
| cluster project='uav' *more_args=""         | Cluster only |
| predict-vss project='uav' image_dir=...     | Predict images using the VSS database |
| run-ctenoA-prod                             | Run strided inference on videos in TSV file |
| run-mega-inference                          | Run mega strided inference on single video |
| run-mega-stride-bio video=...               | Run mega strided pipeline for bio project |
| run-mega-track-bio video=...                | Run mega strided tracking pipeline for bio project |
| run-mega-stride-i2map video=...             | Run mega strided pipeline for i2map |
| run-mega-track-i2map video=...              | Run mega strided tracking pipeline for i2map |
| run-mega-track-test-1min                    | Test mega strided tracking pipeline on one video |
| run-mega-track-test-fastapiyv5              | Test mega strided pipeline with FastAPI |
| run-mega-track-isiis-video video=...        | Mega strided tracking pipeline for cfe project |
| cluster-i2mapbulk                           | Run inference and cluster on i2MAP bulk data |
| download-cluster project="i2map" ...        | Download and cluster data |
| cluster-ptvr-sweep roi_dir=... save_dir=... | Sweep clustering for planktivore data |
| load-i2mapbulk data='data'                  | Load i2MAP bulk data |
| load-cluster project="uav" data='data' ...  | Load clusters for any project |
| download-i2mapbulk-unlabeled                | Download i2MAP bulk unlabeled data |
| replace-m3-urls                             | Replace m3 URLs with mantis |
| gen-bio-data image_dir=""                   | Generate training data for the bio project |
| gen-cfe-data                                | Generate training data for the CFE project |
| gen-i2map-data                              | Generate training data for the i2map project |
| gen-i2mapbulk-data                          | Generate training data for the i2map project from bulk |
| gen-uav-data                                | Generate training data for the UAV project |
| gen-stats-csv project='UAV' data=...        | Generate training data stats |
| gen-ptvr-lowmag-data                        | Generate training data for the planktivore low mag |
| init-ptvr-lowmag-vss                        | Initialize VSS for planktivore low mag data |
| transcode-i2map                             | Transcode i2MAP videos from mov to mp4 |
--

### Related projects

- [aidata](https://github.com/mbari-org/aidata) -A tool to extract, transform, load and download operations on AI data.
- [sdcat](https://github.com/mbari-org/sdcat) - Sliced Detection and Clustering Analysis Toolkit; a tool to detect and cluster objects in images.
- [deepsea-ai](https://github.com/mbari-org/deepsea-ai) - A tool to train and run object detection and tracking on video at scale in the cloud (AWS).
- [fastapi-yolov5](https://github.com/mbari-org/fastapi-yolov5) - A RESTful API for running YOLOv5 object detection models on images either locally or in the cloud (AWS).
- [fastapi-vss](https://github.com/mbari-org/fastapi-vss) - A RESTful API for vector similarity search using foundational models.
- [fastapi-tator](https://github.com/mbari-org/fastapi-tator) - A RESTful API server for bulk operations on a Tator annotation database.


🗓️ Last updated: 2025-06-01