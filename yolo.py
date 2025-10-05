import torch
import cv2
import numpy as np

# Load pretrained YOLOv5s model (COCO 80 classes, includes teddy bear)
model = torch.hub.load('ultralytics/yolov5', 'yolov5s', pretrained=True)

# Class name we want
TARGET_CLASS = "teddy bear"

# Open webcam
cap = cv2.VideoCapture(0)

while True:
    ret, frame = cap.read()
    if not ret:
        break

    # Run inference
    results = model(frame)

    # Convert detections to pandas DataFrame
    detections = results.pandas().xyxy[0]

    # Filter for teddy bear class
    bears = detections[detections["name"] == TARGET_CLASS]

    # Draw teddy bear detections
    for i, row in bears.iterrows():
        x1, y1, x2, y2, conf = int(row["xmin"]), int(row["ymin"]), int(row["xmax"]), int(row["ymax"]), row["confidence"]
        cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
        cv2.putText(frame, f"TeddyBear {conf:.2f}", (x1, y1-5),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0,255,0), 2)

    # Show result
    cv2.imshow("YOLOv5 TeddyBear Detection", frame)

    # Print teddy bear rows
    if len(bears) > 0:
        print(bears)

    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()
