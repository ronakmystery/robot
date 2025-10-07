import pygame, time, json, socket, cv2, os, requests, numpy as np

# --- Controller setup ---
pygame.init()
pygame.joystick.init()
if pygame.joystick.get_count() == 0:
    print("❌ No controller found!")
    exit()
js = pygame.joystick.Joystick(0)
js.init()
print(f"🎮 Controller: {js.get_name()}")

# --- UDP setup ---
UDP_IP = "10.46.74.45"     # Robot IP
UDP_PORT = 5005
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

# --- MJPEG stream setup ---
STREAM_URL = f"http://{UDP_IP}:8000/stream"
print(f"📡 Connecting to {STREAM_URL} ...")
stream = requests.get(STREAM_URL, stream=True)
stream_iter = stream.iter_content(chunk_size=1024)
bytes_buffer = b""

def get_stream_frame():
    """Continuously reads MJPEG frames without re-consuming the stream."""
    global bytes_buffer
    while True:
        try:
            chunk = next(stream_iter)
            bytes_buffer += chunk
            a = bytes_buffer.find(b'\xff\xd8')  # JPEG start
            b = bytes_buffer.find(b'\xff\xd9')  # JPEG end
            if a != -1 and b != -1:
                jpg = bytes_buffer[a:b+2]
                bytes_buffer = bytes_buffer[b+2:]
                frame = cv2.imdecode(np.frombuffer(jpg, dtype=np.uint8), cv2.IMREAD_COLOR)
                if frame is not None:
                    frame = cv2.flip(frame, -1)  # match browser rotation
                return frame
        except StopIteration:
            return None

# --- Dataset base path ---
save_root = "dataset"
os.makedirs(save_root, exist_ok=True)

# --- State ---
height = 0
moves = []
recording = False
session_path = None
save_file = None

def start_new_session():
    """Create a new folder each time recording starts."""
    global session_path, save_file, moves
    session_name = time.strftime("session_%Y%m%d_%H%M%S")
    session_path = os.path.join(save_root, session_name)
    os.makedirs(f"{session_path}/frames", exist_ok=True)
    save_file = f"{session_path}/moves.json"
    moves = []
    print(f"📂 New session: {session_path}")

def save_moves():
    """Save moves JSON in the current session folder."""
    if not moves or not save_file:
        return
    with open(save_file, "w") as f:
        json.dump(moves, f, indent=2)
    print(f"💾 Saved {len(moves)} moves to {save_file}")

print("⚡ Press BACK (button 6) to toggle recording, START (button 7) to replay")

while True:
    pygame.event.pump()
    frame = get_stream_frame()
    if frame is None:
        continue

    # --- Controller inputs ---
    ljsx = js.get_axis(0)
    rjsx = js.get_axis(2)
    rjsy = js.get_axis(3)
    rt   = js.get_axis(5)
    lt   = js.get_axis(4)

    rt_norm = (rt + 1) / 2
    lt_norm = (lt + 1) / 2

    drive = rt_norm - lt_norm
    mode = "walk" if abs(drive) > 0.05 else "stop"
    backwards = drive < 0
    speed = int(abs(drive) * 40)

    lateral = int(ljsx * 200)
    if backwards:
        lateral = -lateral

    pitch = int(-rjsy * 100)
    roll  = int(rjsx * 40)

    a = js.get_button(3)  # A raise
    y = js.get_button(0)  # Y lower
    if a: height += 1
    if y: height -= 1
    height = max(-100, min(100, height))

    left_bumper  = js.get_button(4)
    right_bumper = js.get_button(5)
    record_button = js.get_button(6)
    start_button  = js.get_button(7)

    data = {
        "mode": mode,
        "walk_type": "flat",
        "backwards": backwards,
        "lateral": lateral,
        "height": height,
        "pitch": pitch,
        "roll": roll,
        "speed": speed,
        "pause": bool(left_bumper),
        "start": bool(right_bumper),
    }

    # --- Recording toggle ---
    if record_button:
        recording = not recording
        if recording:
            start_new_session()
            print("🔴 Recording ON (new session started)")
        else:
            save_moves()
            print("⏹️ Recording OFF (session saved)")
        time.sleep(0.3)

    # --- Save frame + action ---
    if recording and session_path:
        timestamp = time.time()
        moves.append([timestamp, data.copy()])
        frame_path = f"{session_path}/frames/{timestamp:.3f}.jpg"
        resized = cv2.resize(frame, (224, 224))
        cv2.imwrite(frame_path, resized)

    # --- Send UDP packet ---
    sock.sendto(json.dumps(data).encode(), (UDP_IP, UDP_PORT))

    # --- Replay ---
    if start_button and moves:
        print("▶️ Replaying moves...")
        for t, move in moves:
            sock.sendto(json.dumps(move).encode(), (UDP_IP, UDP_PORT))
            time.sleep(0.01)
        print("✅ Replay finished")

    # --- Display feed ---
    cv2.imshow("Robot View", frame)
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

    time.sleep(0.01)

cv2.destroyAllWindows()
save_moves()
print("✅ All sessions saved.")
