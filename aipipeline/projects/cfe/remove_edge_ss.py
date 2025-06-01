import cv2

# Before running this code, ensure you have the required libraries installed: pip install opencv-python opencv-python-headless
# and segment-anything
# git clone https://github.com/facebookresearch/segment-anything.git
# cd segment-anything
# pip install -e .
# and download the model with wget https://dl.fbaipublicfiles.com/segment_anything/sam_vit_h_4b8939.pth
# or curl -O https://dl.fbaipublicfiles.com/segment_anything/sam_vit_h_4b8939.pth
# this can take 5 minutes over a home network


import numpy as np
from segment_anything import SamPredictor, sam_model_registry

# Load image
img = cv2.imread('/Users/dcline/Dropbox/data/STT/STT25-1_gel_small.png')

# Detect blobs (plastic rim should show up well)
params = cv2.SimpleBlobDetector_Params()
params.filterByColor = True
params.blobColor = 255
params.filterByArea = True
params.minArea = 50
params.maxArea = 5000
detector = cv2.SimpleBlobDetector_create(params)

gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
keypoints = detector.detect(gray)

# Convert keypoints to numpy array
input_points = np.array([[kp.pt[0], kp.pt[1]] for kp in keypoints])
input_labels = np.ones(len(input_points))  # 1 = foreground points

# Load SAM model
sam = sam_model_registry["vit_h"](checkpoint="/Users/dcline/Dropbox/data/SAM/sam_vit_h_4b8939.pth")
predictor = SamPredictor(sam)
predictor.set_image(img)

# Predict mask
masks, scores, logits = predictor.predict(
    point_coords=input_points,
    point_labels=input_labels,
    multimask_output=False
)

# Mask application
mask = masks[0]  # Single mask
result = np.where(mask[..., None], img, 255)  # white background outside mask

# Save
cv2.imwrite('/Users/dcline/Dropbox/data/STT/STT25-1_gel_small_clean.png', result)