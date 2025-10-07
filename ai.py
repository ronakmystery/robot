import socket, json, torch, cv2, requests, numpy as np
from torch import nn

# ================================
# 1. Model definition (same as training)
# ================================
class VisionToAction(nn.Module):
    def __init__(self):
        super().__init__()
        self.cnn = nn.Sequential(
            nn.Conv2d(3, 16, 3, 2, 1), nn.BatchNorm2d(16), nn.ReLU(),
            nn.Conv2d(16, 32, 3, 2, 1), nn.BatchNorm2d(32), nn.ReLU(),
            nn.Conv2d(32, 64, 3, 2, 1), nn.BatchNorm2d(64), nn.ReLU(),
            nn.Flatten(),
        )
        self.fc = nn.Sequential(
            nn.Linear(64 * 16 * 16, 128), nn.ReLU(),
            nn.Linear(128, 6)
        )

    def forward(self, x):
        return self.fc(self.cnn(x))

# ================================
# 2. Model load
# ================================
model = VisionToAction()
model.load_state_dict(torch.load("robot_model.pth", map_location="cpu"))
model.eval()
print("✅ Loaded trained model: robot_model.pth")

# ================================
# 3. Network setup
# ================================
UDP_IP = "10.46.74.45"   # Robot IP
UDP_PORT = 5005
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

# ================================
# 4. MJPEG camera stream
# ================================
STREAM_URL = f"http://{UDP_IP}:8000/stream"
print(f"📡 Connecting to {STREAM_URL} ...")
stream = requests.get(STREAM_URL, stream=True)
stream_iter = stream.iter_content(chunk_size=1024)
bytes_buffer = b""

def get_stream_frame():
    global bytes_buffer
    while True:
        try:
            chunk = next(stream_iter)
            bytes_buffer += chunk
            a = bytes_buffer.find(b'\xff\xd8')
            b = bytes_buffer.find(b'\xff\xd9')
            if a != -1 and b != -1:
                jpg = bytes_buffer[a:b+2]
                bytes_buffer = bytes_buffer[b+2:]
                frame = cv2.imdecode(np.frombuffer(jpg, dtype=np.uint8), cv2.IMREAD_COLOR)
                if frame is not None:
                    frame = cv2.flip(frame, -1)
                return frame
        except StopIteration:
            return None

# ================================
# 5. Run loop
# ================================
device = "cuda" if torch.cuda.is_available() else "cpu"
model.to(device)
print(f"🤖 Running on {device}")

while True:
    frame = get_stream_frame()
    if frame is None:
        continue

    # preprocess
    img = cv2.resize(frame, (128, 128))
    img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    tensor = torch.tensor(img, dtype=torch.float32).permute(2,0,1).unsqueeze(0) / 255.0
    tensor = tensor.to(device)

    # predict
    with torch.no_grad():
        pred = model(tensor)[0].cpu().numpy()

    # unnormalize
    speed     = float(pred[0] * 40)
    lateral   = float(pred[1] * 200)
    pitch     = float(pred[2] * 100)
    roll      = float(pred[3] * 40)
    height    = float(pred[4] * 100)
    backwards = bool(pred[5] > 0.5)

    mode = "walk" if abs(speed) > 2 else "stop"

    data = {
        "mode": mode,
        "walk_type": "flat",
        "backwards": backwards,
        "lateral": int(lateral),
        "height": int(height),
        "pitch": int(pitch),
        "roll": int(roll),
        "speed": int(abs(speed)),
        "pause": False,
        "start": False
    }

    # send to robot
    sock.sendto(json.dumps(data).encode(), (UDP_IP, UDP_PORT))

    # visualize predictions
    cv2.putText(frame, f"spd={int(speed)} lat={int(lateral)} back={backwards}",
                (10, 20), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0,255,0), 1)
    cv2.imshow("AI Control", frame)

    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cv2.destroyAllWindows()
print("🧠 AI control stopped.")
