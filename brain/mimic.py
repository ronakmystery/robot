import cv2, mediapipe as mp, socket, time

# ---- UDP ----
UDP_IP, UDP_PORT = "192.168.1.158", 5005   # robot IP
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

# ---- Video Stream ----
URL = "http://192.168.1.158:8000/stream"   # Pi stream URL
cap = cv2.VideoCapture(URL)

#laptop
# cap = cv2.VideoCapture(0) 

ANGLE_MIN, ANGLE_MAX = 0, 180
SEND_INTERVAL = 0.01

def map_to_angle(val, invert=False):
    val = max(0.0, min(1.0, val))
    if invert: val = 1.0 - val
    return int(ANGLE_MIN + val * (ANGLE_MAX - ANGLE_MIN))

# ---- Mediapipe Hand Tracking ----
mp_hands = mp.solutions.hands
hands = mp_hands.Hands(max_num_hands=1,
                       min_detection_confidence=0.6,
                       min_tracking_confidence=0.6)

last_send = 0

while True:
    ok, frame = cap.read()
    if not ok:
        print("⚠️ Could not read frame from robot camera")
        break

    h, w = frame.shape[:2]
    rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    res = hands.process(rgb)

    if res.multi_hand_landmarks:
        lm = res.multi_hand_landmarks[0].landmark

        # Index finger joints
        mcp = lm[mp_hands.HandLandmark.INDEX_FINGER_MCP]
        pip = lm[mp_hands.HandLandmark.INDEX_FINGER_PIP]
        tip = lm[mp_hands.HandLandmark.INDEX_FINGER_TIP]

        # Servo 0: hip swing (X)
        ang0 = map_to_angle(mcp.x,invert=True)

        # Servo 1: thigh lift (Y)
        ang1 = map_to_angle(mcp.y, invert=True)

        # Servo 2: knee bend (distance)
        dist = ((tip.x - mcp.x)**2 + (tip.y - mcp.y)**2) ** 0.5
        ang2 = map_to_angle(dist *4.0,invert=True)

        # Send angles via UDP
        now = time.time()
        if now - last_send > SEND_INTERVAL:
            msg = f"4,{ang0},5,{ang1},6,{ang2}".encode()
            sock.sendto(msg, (UDP_IP, UDP_PORT))
            last_send = now

        # Draw debug
        for p in [mcp, pip, tip]:
            x, y = int(p.x*w), int(p.y*h)
            cv2.circle(frame, (x,y), 6, (0,255,0), -1)
        cv2.putText(frame, f"{ang0},{ang1},{ang2}", (10,30),
                    cv2.FONT_HERSHEY_SIMPLEX, 1, (0,255,0), 2)

    cv2.imshow("Robot Camera + Finger Tracking", frame)
    if cv2.waitKey(1) & 0xFF == 27: break

cap.release()
cv2.destroyAllWindows()