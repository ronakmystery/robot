import pygame, time, json, socket

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

# --- State ---
height = 0
moves = []
recording = False
save_file = "moves.json"

def save_moves():
    if not moves:
        return
    with open(save_file, "w") as f:
        json.dump(moves, f)
    print(f"💾 Saved {len(moves)} moves to {save_file}")

while True:
    pygame.event.pump()

    # --- Read axes ---
    ljsx = js.get_axis(0)   # left stick X → turning / lateral
    rjsx = js.get_axis(2)   # right stick X → roll
    rjsy = js.get_axis(3)   # right stick Y → pitch
    rt   = js.get_axis(5)   # right trigger: -1 → +1
    lt   = js.get_axis(4)   # left trigger:  -1 → +1

    # Normalize triggers [-1,+1] → [0,1]
    rt_norm = (rt + 1) / 2
    lt_norm = (lt + 1) / 2

    # Compute drive direction and magnitude
    drive = rt_norm - lt_norm  # forward(+)/back(-)
    mode = "walk" if abs(drive) > 0.05 else "stop"
    backwards = drive < 0
    speed = int(abs(drive) * 40)  # scale 0–40

    # Lateral turning from left stick X
    lateral = int(ljsx * 200)
    if backwards:
        lateral = -lateral  # reverse steering when walking backward

    # --- Orientation ---
    pitch = int(-rjsy * 100)
    roll  = int(rjsx * 40)

    # --- Height control ---
    a = js.get_button(3)  # A raise
    y = js.get_button(0)  # Y lower
    if a: height += 1
    if y: height -= 1
    height = max(-100, min(100, height))

    # --- Buttons ---
    left_bumper  = js.get_button(4)
    right_bumper = js.get_button(5)
    record_button = js.get_button(6)
    start_button  = js.get_button(7)

    # --- Packet to send ---
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
            moves.clear()
            print("🔴 Recording ON (cleared old moves)")
        else:
            save_moves()
            print("⏹️ Recording OFF")
        time.sleep(0.3)

    # --- Store moves if recording ---
    if recording:
        moves.append((time.time(), data.copy()))

    # --- Send packet ---
    sock.sendto(json.dumps(data).encode(), (UDP_IP, UDP_PORT))

    # --- Replay sequence ---
    if start_button and moves:
        print("▶️ Replaying moves...")
        for t, move in moves:
            time.sleep(0.01)
            sock.sendto(json.dumps(move).encode(), (UDP_IP, UDP_PORT))
        print("✅ Replay finished")

    time.sleep(0.01)  # ~100 Hz loop
