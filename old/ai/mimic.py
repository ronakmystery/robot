import cv2, requests, time
import mediapipe as mp


ip="10.46.74.45"
url = f"http://{ip}:8000/stream"
ROBOT_API = f"http://{ip}:5005/api/walk"

cap = cv2.VideoCapture(url)

last_send = 0
height = 0

# MediaPipe Hands
mp_hands = mp.solutions.hands
hands = mp_hands.Hands(static_image_mode=False,
                       max_num_hands=1,
                       min_detection_confidence=0.5,
                       min_tracking_confidence=0.5)

def is_fist(hand_landmarks):
    """Detect fist: finger tips below their PIP joints (folded)."""
    tips = [8, 12, 16, 20]  # index, middle, ring, pinky tips
    pips = [6, 10, 14, 18]  # PIP joints
    folded = 0
    for tip, pip in zip(tips, pips):
        if hand_landmarks.landmark[tip].y > hand_landmarks.landmark[pip].y:
            folded += 1
    return folded >= 3  # majority of fingers folded

def is_open_hand(hand_landmarks):
    """Detect open hand: all fingertips above their PIP joints."""
    tips = [8, 12, 16, 20]
    pips = [6, 10, 14, 18]
    extended = 0
    for tip, pip in zip(tips, pips):
        if hand_landmarks.landmark[tip].y < hand_landmarks.landmark[pip].y:
            extended += 1
    return extended >= 3  # majority extended

def is_point(hand_landmarks):
    """Index up, others down."""
    return (hand_landmarks.landmark[8].y < hand_landmarks.landmark[6].y and  # index up
            hand_landmarks.landmark[12].y > hand_landmarks.landmark[10].y and
            hand_landmarks.landmark[16].y > hand_landmarks.landmark[14].y and
            hand_landmarks.landmark[20].y > hand_landmarks.landmark[18].y)

def is_peace(hand_landmarks):
    """Index + middle up, ring+pinky down."""
    return (hand_landmarks.landmark[8].y < hand_landmarks.landmark[6].y and
            hand_landmarks.landmark[12].y < hand_landmarks.landmark[10].y and
            hand_landmarks.landmark[16].y > hand_landmarks.landmark[14].y and
            hand_landmarks.landmark[20].y > hand_landmarks.landmark[18].y)

def is_thumbs_up(hand_landmarks):
    """Thumb extended upwards."""
    return hand_landmarks.landmark[4].y < hand_landmarks.landmark[3].y  # tip above joint

def is_thumbs_down(hand_landmarks):
    """Thumb pointing down."""
    return hand_landmarks.landmark[4].y > hand_landmarks.landmark[3].y  # tip below joint


# --- Initial Stand Pose ---
init_command = {
    "mode": "stop", "walk_type": "flat", "backwards": False,
    "lateral": 0, "height": 0, "pitch": 0, "roll": 0,
    "speed": 20, "pause": 0, "start": 1
}
try:
    requests.post(ROBOT_API, json=init_command, timeout=0.5)
    print("✅ Sent initial stand pose")
except Exception as e:
    print(f"⚠️ Could not send init command: {e}")

time.sleep(1)

# --- Main Loop ---
while True:
    ret, frame = cap.read()
    if not ret:
        continue

    frame = cv2.rotate(frame, cv2.ROTATE_90_CLOCKWISE)
    rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    result = hands.process(rgb)

    command = {
        "mode": "stop", "walk_type": "flat", "backwards": False,
        "lateral": 0, "height": height, "pitch": 0, "roll": 0,
        "speed": 20, "pause": 0, "start": 0
    }

    if result.multi_hand_landmarks:
        handLms = result.multi_hand_landmarks[0]

        if is_open_hand(handLms):
            command["start"] = 1
            print("✋ Open hand → start=1")

        elif is_fist(handLms):
            command["pause"] = 1
            print("👊 Fist → pause=1")

        elif is_point(handLms):
            command["mode"] = "walk"
            print("☝ Point → walk forward")

        # elif is_peace(handLms):
        #     command["mode"] = "walk"
        #     command["backwards"] = True
        #     print("✌ Peace → walk backwards")

        elif is_thumbs_up(handLms):
            command["height"] = 50
            print("👍 Thumbs up → height=50")

        elif is_thumbs_down(handLms):
            command["height"] = -50
            print("👎 Thumbs down → height=-50")


    # 🔗 Send every 0.3s
    now = time.time()
    if now - last_send >= 0.5:
        try:
            requests.post(ROBOT_API, json=command, timeout=0.5)
            print("Sent:", command)
        except Exception as e:
            print(f"⚠️ Could not send command: {e}")
        last_send = now
