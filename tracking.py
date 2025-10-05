import cv2, socket, json, time, signal, sys
import numpy as np

ROBOT_IP = "10.46.74.45"
ROBOT_PORT = 5005
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

# --- UDP sender ---
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

# --- Camera stream ---
cap = cv2.VideoCapture(f"http://{ROBOT_IP}:8000/stream")
cap.set(cv2.CAP_PROP_FRAME_WIDTH, 320)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 240)

smooth_x, smooth_y = None, None

# --- Distance control params ---
TARGET_SIZE   = 100    # ideal red ball size (height/diameter)
DIST_GAIN     = 0.8
MIN_SPEED     = 20
MAX_SPEED     = 30
DEADZONE      = 10

# --- Red color HSV ranges ---
# Red wraps around the hue boundary, so we combine two ranges
RED_RANGES = [
    ([0, 120, 70], [10, 255, 255]),      # lower reds
    ([170, 120, 70], [180, 255, 255])    # upper reds
]

print("🎥 Tracking red ball — press 'q' to quit")

while True:
    ret, frame = cap.read()
    if not ret:
        continue

    frame = cv2.flip(frame, -1)
    h_img, w_img, _ = frame.shape
    hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)

    # Build red mask
    mask = None
    for lower, upper in RED_RANGES:
        lower = np.array(lower)
        upper = np.array(upper)
        part = cv2.inRange(hsv, lower, upper)
        mask = part if mask is None else (mask | part)

    # Clean up mask
    mask = cv2.GaussianBlur(mask, (7,7), 0)
    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    lateral, speed, roll, pitch, height = 0, 0, 0, 0, 0
    backwards = False

    if contours:
        c = max(contours, key=cv2.contourArea)
        (x, y, w, h) = cv2.boundingRect(c)

        obj_center_x = x + w // 2
        obj_center_y = y + h // 2
        frame_center_x = w_img // 2

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

        # Pitch from vertical
        norm_y = obj_center_y / h_img
        pitch = int(np.interp(norm_y, [0, 1], [50, -50]))

        # Distance control (based on ball size)
        error = TARGET_SIZE - h
        if abs(error) > DEADZONE:
            raw_speed = abs(error) * DIST_GAIN
            raw_speed = np.clip(raw_speed, MIN_SPEED, MAX_SPEED)
            speed = int(raw_speed)
            backwards = (error < 0)
        else:
            speed = 0
            backwards = False

        # Draw box
        cv2.rectangle(frame, (x, y), (x+w, y+h), (0,255,0), 2)
        cv2.putText(frame, f"speed={speed} back={backwards}", (10,20),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0,255,0), 1)

    # --- Mode ---
    mode = "walk" if speed != 0 else "stop"

    action = {
        "mode": mode,
        "walk_type": "flat",
        "backwards": backwards,
        "lateral": 0,
        "height": height,
        "pitch": pitch,
        "roll": roll/2,
        "speed": speed,
        "pause": False,
        "start": False
    }
    send_action(action)

    cv2.imshow("Red Ball Tracking", frame)
    cv2.imshow("Mask", mask)
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()
