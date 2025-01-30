# 901103 Biodiversity Project

## Run object detection on video(s) with (optional) elastic auto-scaling

**process.py** is a command line tool to run object detection on video(s).
Supports multiple CPUs and GPUs.

Designed to run iwht YOLOv5,YOLOv11, or any other models that can be served by a FastAPI server for object detection,
and Vision Transformer (ViT) models for image classification.

For example, the tool can be used to run detections on videos using the YOLOv5 model served by the FastAPI server
at http://fasta-fasta-1d0o3gwgv046e-143598223.us-west-2.elb.amazonaws.com/predict

See [https://github.com/mbari-org/fastapi-yolov5](https://github.com/mbari-org/fastapi-yolov5) for details on
setting up the model server.

For example, to run detections 
- on a single video /data/ctenophora_sp_A_aug/CTENOPHORA_SP_A_AUG_00001.mp4
- with a detection model deployed at http://fasta-fasta-1d0o3gwgv046e-143598223.us-west-2.elb.amazonaws.com/predict
- with a classification model at /mnt/DeepSea-AI/models/m3midwater-vit-b-16/
- with a stride of 2 seconds
    
```shell
cd 
python process.py \
  --config config/config.yaml \
  --video ./data/ctenophora_sp_A_aug/CTENOPHORA_SP_A_AUG_00001.mp4 \
  --vits-model /mnt/DeepSea-AI/models/m3midwater-vit-b-16/ \
  --stride 2 \
  --endpoint http://fasta-fasta-1d0o3gwgv046e-143598223.us-west-2.elb.amazonaws.com/predict 
```