# 901103 Biodiversity Project

## Run object detection on video(s) with elastic auto-scaling


AWS can be used for running object detection on video(s) with elastic auto-scaling.  This avoids the need to run a 
local server and allows for the use of AWS resources to scale up and down as needed.  This is useful for running 
large models or processing large amounts of data.  Once the model is deployed, it can be used as an endpoint, e.g.
http://fasta-fasta-1d0o3gwgv046e-143598223.us-west-2.elb.amazonaws.com/predict.  



# Installation

## Requirements

- AWS account and AWS CLI
- 
Designed to run on models trained with the [deepsea-ai](https://github.com/mbari-org/deepsea-ai) module.
using the FastAPI framework to serve a YOLOv5 model backed by an elastic auto-scaling back-end.

The model is served on port 8000 by default. 
See [https://github.com/mbari-org/fastapi-yolov5](https://github.com/mbari-org/fastapi-yolov5) for details on
setting up the model server.

Once that is setup, run the following command to run the detections against video

For example, to run detections 
- on a single video /data/ctenophora_sp_A_aug/CTENOPHORA_SP_A_AUG_00001.mp4
- against the model deployed at http://fasta-fasta-1d0o3gwgv046e-143598223.us-west-2.elb.amazonaws.com/predict
- with a stride of 2 seconds in 30 fps video (i.e. 2 seconds = 60 frames)
- and store the results in the "test" section of the database
    
```shell
cd 
python process_video_pipeline.py \
  --video ./data/ctenophora_sp_A_aug/CTENOPHORA_SP_A_AUG_00001.mp4 \
  --stride 60 \
  --min-frames 1 \
  --endpoint http://fasta-fasta-1d0o3gwgv046e-143598223.us-west-2.elb.amazonaws.com/predict 
```