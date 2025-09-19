import cv2, socket, json, time, signal, sys, math
import numpy as np

ROBOT_IP = "10.236.55.45"
ROBOT_PORT = 5005
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

# --- Choose target color ---
TARGET_COLOR = "red"   # "red", "green", "blue"

COLOR_RANGES = {
    "red":   [([0, 120, 70], [10, 255, 255]), ([170, 120, 70], [180, 255, 255])],
    "green": [([35, 100, 70], [85, 255, 255])],
    "blue":  [([90, 100, 70], [130, 255, 255])]
}

def send_action(action):
    sock.sendto(json.dumps(action).encode(), (ROBOT_IP, ROBOT_PORT))

# --- Safety handler ---
def shutdown_handler(sig, frame):
    print("\n🛑 Ctrl+C pressed → stopping robot...")
    stop_action = {"mode": "stop","walk_type":"flat","backwards":False,
                   "lateral":0,"height":0,"pitch":0,"roll":0,
                   "speed":0,"pause":False,"start":False}
    send_action(stop_action); time.sleep(0.5)
    stand_action = stop_action.copy(); stand_action["start"] = True
    send_action(stand_action)
    print("✅ Robot returned to stand pose"); sys.exit(0)

signal.signal(signal.SIGINT, shutdown_handler)

# --- Initial stand ---
init_action = {"mode":"stop","walk_type":"flat","backwards":False,
               "lateral":0,"height":0,"pitch":0,"roll":0,
               "speed":0,"pause":False,"start":True}
print("⚡ Sending initial stand pose...")
send_action(init_action); time.sleep(2)

# --- OpenCV optimizations ---
cv2.setUseOptimized(True)
cv2.setNumThreads(4)

# --- Camera stream ---
cap = cv2.VideoCapture("http://10.236.55.45:8000/stream")
cap.set(cv2.CAP_PROP_FRAME_WIDTH, 100)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 100)

# --- Smoothing memory ---
smooth_x, smooth_y = None, None

while True:
    ret, frame = cap.read()
    if not ret:
        continue

    frame = cv2.flip(frame, -1)
    small = cv2.resize(frame, (160, 120))
    hsv = cv2.cvtColor(small, cv2.COLOR_BGR2HSV)

    mask = None
    for lower, upper in COLOR_RANGES[TARGET_COLOR]:
        lower = np.array(lower); upper = np.array(upper)
        part = cv2.inRange(hsv, lower, upper)
        mask = part if mask is None else (mask | part)

    contours, _ = cv2.findContours(mask, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)

    # ✅ Defaults
    lateral, speed, roll, pitch, height = 0, 0, 0, 0, 0

    # Filter out tiny blobs
    MIN_AREA = 10
    contours = [c for c in contours if cv2.contourArea(c) > MIN_AREA]

    overlay = frame.copy()   # for blur

    if contours:
        # --- Target found ---
        c = max(contours, key=cv2.contourArea)
        (x, y, w, h) = cv2.boundingRect(c)
        obj_center_x = x + w//2
        obj_center_y = y + h//2
        frame_center_x = small.shape[1] // 2

        # Smooth centers
        alpha = 0.3
        if smooth_x is None:
            smooth_x, smooth_y = obj_center_x, obj_center_y
        smooth_x = int(alpha * obj_center_x + (1 - alpha) * smooth_x)
        smooth_y = int(alpha * obj_center_y + (1 - alpha) * smooth_y)
        obj_center_x, obj_center_y = smooth_x, smooth_y

        # Horizontal offset → lateral + roll
        offset_x = obj_center_x - frame_center_x
        lateral = int(offset_x * 1.0)
        roll = int(offset_x * 0.2)

        # Vertical offset → pitch mapping [-50 .. 50]
        frame_h = small.shape[0]
        norm_y = obj_center_y / frame_h
        pitch = int(np.interp(norm_y, [0, 1], [50, -50]))

        # --- Blur background except object ---
        blurred = cv2.GaussianBlur(frame, (31, 31), 0)
        mask_full = np.zeros(frame.shape[:2], dtype="uint8")
        cv2.rectangle(mask_full, (x*4, y*4), ((x+w)*4, (y+h)*4), 255, -1)  # upscale mask
        mask_inv = cv2.bitwise_not(mask_full)
        background = cv2.bitwise_and(blurred, blurred, mask=mask_inv)
        foreground = cv2.bitwise_and(frame, frame, mask=mask_full)
        frame = cv2.add(background, foreground)

        # Debug overlays
        cv2.rectangle(frame, (x*4, y*4), ((x+w)*4, (y+h)*4), (0,255,0), 2)
        # cv2.circle(frame, (obj_center_x*4, obj_center_y*4), 5, (255,0,0), -1)

    # --- Send action ---
    action = {
        "mode": "stop",
        "walk_type": "flat",
        "backwards": False,
        "lateral": -lateral,
        "height": height,
        "pitch": pitch,
        "roll": roll,
        "speed": 0,
        "pause": False,
        "start": False
    }
    # print("➡️ Sending:", action)
    send_action(action)

    # Debug display
    cv2.imshow("Tracking", frame)
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()
