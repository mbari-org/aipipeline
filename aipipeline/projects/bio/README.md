# 901103 Biodiversity Project

## Run object detection on video(s) with elastic auto-scaling

**run_inference_video.py** is a command line tool to run object detection on video(s) with AWS elastic auto-scaling.
Supports multiple processors and CPUs.

Designed to run on models trained with the [deepsea-ai](https://github.com/mbari-org/deepsea-ai) module.
using the FastAPI framework to serve a YOLOv5 model backed by an elastic auto-scaling back-end.

The model is served on port 8000 by default. 
See [https://github.com/mbari-org/fastapi-yolov5](https://github.com/mbari-org/fastapi-yolov5) for details on
setting up the model server.

Once that is setup, run the following command to run the detections against video
For example, to run detections 
- on a single video /data/ctenophora_sp_A_aug/CTENOPHORA_SP_A_AUG_00001.mp4
- against the model deployed at http://fasta-fasta-1d0o3gwgv046e-143598223.us-west-2.elb.amazonaws.com/predict
- with a stride of 2 seconds
- and store the results in the "test" section of the database
    
```shell
cd 
python cluster_pipeline.py \
  --config config/config.yaml \
  --video ./data/ctenophora_sp_A_aug/CTENOPHORA_SP_A_AUG_00001.mp4 \
  --stride 2 \
  --endpoint http://fasta-fasta-1d0o3gwgv046e-143598223.us-west-2.elb.amazonaws.com/predict 
```