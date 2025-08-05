# Utility script to run SAM on images and save the bounding box to a CSV file

from pathlib import Path

import cv2
import numpy as np
from ultralytics import SAM, FastSAM

# Load the SAM model
model_sam21l = SAM(model="sam2.1_l.pt")
model_sam21t = SAM(model="sam2.1_t.pt")
model_saml = SAM(model="sam_l.pt")
model_sam2t = SAM(model="sam2_t.pt")
model_samm = SAM(model="mobile_sam.pt")
model_fast = FastSAM(model="FastSAM-x.pt")

display = False # Set to True to display the images - usefull for debugging
sift = cv2.SIFT_create()

# image_path = Path("/Users/dcline/Dropbox/data/UAV/crops/BirdSelect/")
# image_path = Path("/Users/dcline/Dropbox/data/UAV/crops/BirdHard/")
image_path = Path("/Users/dcline/aidata/datasets/Baseline/crops/Bird")
out_path = Path("/Users/dcline/aidata/datasets/Baseline/crops/BirdOut")
# out_path = Path("/Users/dcline/Dropbox/data/UAV/crops/BirdHardOut/")
out_path.mkdir(exist_ok=True)

out_csv = out_path / "birdbox.csv"

# The padding for the bounding box
padding = 10

with out_csv.open("w") as f:
    f.write("id,image,x,y,width,height\n")
    for im in image_path.glob("*.jpg"):
        image = cv2.imread(im.as_posix())
        db_id = int(im.stem)

        # Get the mean color of the image and skip if there is too much color variation as the segmentation may not be accurate
        mean_color = np.mean(image, axis=(0, 1))
        std_color = np.mean(np.std(image, axis=(0, 1)))

        if std_color > 30:
            continue

        # Skip if the image is too small
        if image.shape[0] < 100 or image.shape[1] < 100:
            continue

        # Threshold in HSV color space
        hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
        # # Calculate the mean and standard deviation of the saturation channel
        sat = hsv[:, :, 1]
        val = hsv[:, :, 2]
        hue = hsv[:, :, 0]
        block_size = 13
        # Threshold the saliency map using gradient thresholding
        binary_mask = cv2.adaptiveThreshold(
            sat.astype(np.uint8),
            255,  # Max pixel value
            cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
            cv2.THRESH_BINARY,
            block_size,  # Block size (size of the local neighborhood)
            9  # Constant subtracted from the mean
        )

        # Set the mask to 0 if the saturation is below a threshold
        binary_mask[sat < 40] = 0

        # Invert the mask
        binary_mask = 255 - binary_mask

        contours, _ = cv2.findContours(binary_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        # Remove all small contours
        for contour in contours:
            area = cv2.contourArea(contour)
            if area < 300:
                cv2.drawContours(binary_mask, [contour], -1, 0, -1)

        # Remove contours close in hue to the background
        for contour in contours:
            x, y, w, h = cv2.boundingRect(contour)
            roi = hue[y:y+h, x:x+w]
            mean_hue = np.mean(roi)
            if mean_hue < 60 or mean_hue > 100:
                cv2.drawContours(binary_mask, [contour], -1, 0, -1)

        # Remove contours too close to the edge
        for contour in contours:
            x, y, w, h = cv2.boundingRect(contour)
            if x < 10 or y < 10 or x + w > image.shape[1] - 10 or y + h > image.shape[0] - 10:
                cv2.drawContours(binary_mask, [contour], -1, 0, -1)

        # Invert the mask
        output_mask = 255 - binary_mask

        # Create a new image setting the masked region to black
        image_masked = image.copy()
        image_masked[output_mask == 255] = 0
        keypoints, _ = sift.detectAndCompute(image_masked, None)

        # Filter keypoints based on the binary mask
        filtered_keypoints = []

        for kp in keypoints:
            x, y = int(kp.pt[0]), int(kp.pt[1])  # Keypoint coordinates
            if binary_mask[y, x] > 0:  # Check if the keypoint is in the mask region
                filtered_keypoints.append(kp)

        # Convert cv2 keypoints to numpy array
        keypoints = np.array([[int(kp.pt[0]),int(kp.pt[1])] for kp in filtered_keypoints])

        # Display keypoints on the image at the chosen indices
        image_kp = image.copy()
        for kp in keypoints:
            cv2.circle(image_kp, kp, 2, (0, 0, 255), -1)

        if len(keypoints) == 0:
            print("No keypoints detected.")
            continue

        # Gaussian blur the image
        image_blur = cv2.GaussianBlur(image, (9, 9), 0)

        # Run SAM segmentation
        results1 = model_sam2t.predict(image_blur, points=keypoints, labels=[1] * len(keypoints), device="cpu")
        results2 = model_sam21l.predict(image_blur, points=keypoints, labels=[1] * len(keypoints), device="cpu")
        results = results1

        # Get the largest bounding box that has at least 10% coverage in the masked region
        bbox_best = None
        largest = 0
        for result in results:
            bboxes = result.boxes.xywh
            for bbox in bboxes:
                bbox = bbox.tolist()
                x, y, w, h = bbox
                w = int(w)
                h = int(h)
                x = int(x)
                y = int(y)

                image_crop = image[y:y+h, x:x+w] # Crop the image
                mask_crop = output_mask[y:y+h, x:x+w] # Crop the mask
                mask_area = np.sum(mask_crop) / 255
                bbox_area = w * h
                coverage = mask_area / bbox_area
                print(f"{im} {x},{y},{w}x{h} {mask_area} {bbox_area} {coverage}")

                # If the width or height is within 1 pixel of the image size skip
                # this is either a well cropped image or the background segment
                if w >= image.shape[1] - 1 or h >= image.shape[0] - 1 or coverage < 0.3:
                    print(f'Skipping {w}x{h} bbox')
                    continue

                x = int(x) - w // 2
                y = int(y) - h // 2
                if w * h > largest and w > 10 and h > 10:
                    largest = w * h
                    bbox_best = (x, y, w, h)
                    # add padding to the bounding box
                    bbox_best = (bbox_best[0] - padding, bbox_best[1] - padding, bbox_best[2] + 2 * padding, bbox_best[3] + 2 * padding)
                    # clip the bounding box to the image size
                    bbox_best = (max(0, bbox_best[0]), max(0, bbox_best[1]), min(image.shape[1], bbox_best[2]), min(image.shape[0], bbox_best[3]))

        if bbox_best:
            x = int(bbox_best[0])
            y = int(bbox_best[1])
            w = int(bbox_best[2])
            h = int(bbox_best[3])
            cv2.rectangle(image, (x, y), (x + w, y + h), (0, 255, 0), 1)
            title = f"image_box {im.stem} {x},{y},{w}x{h} {image.shape[0]}x{image.shape[1]}"
        else:
            title = f"image_kp {im.stem} {image.shape[0]}x{image.shape[1]}"

        im_show = np.concatenate((cv2.cvtColor(output_mask, cv2.COLOR_GRAY2BGR), image, image_kp,), axis=1)
        if display:
            cv2.imshow(title, im_show)
            cv2.waitKey(0)

        out_file = out_path / im.name

        if bbox_best:
            cv2.imwrite(out_file.as_posix(), im_show)
            f.write(f"{db_id},{im},{x},{y},{w},{h}\n")