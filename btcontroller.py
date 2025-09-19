import pygame, time, json, socket

# --- Controller setup ---
pygame.init()
pygame.joystick.init()
if pygame.joystick.get_count() == 0:
    print("No controller found!")
    exit()
joystick = pygame.joystick.Joystick(0)
joystick.init()
print(f"🎮 Connected to {joystick.get_name()}")

# --- UDP Setup ---
UDP_IP = "10.236.55.45"   # Robot IP
UDP_PORT = 5005
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

# --- State ---
height = 0
moves = []          # store sent packets
recording = False   # toggle recording
save_file = "moves.json"

def save_moves():
    if not moves:
        return
    with open(save_file, "w") as f:
        json.dump(moves, f)
    print(f"💾 Saved {len(moves)} moves to {save_file}")

while True:
    pygame.event.pump()

    # Sticks
    ljsx = joystick.get_axis(0)
    ljsy = joystick.get_axis(1)
    rjsx = joystick.get_axis(2)
    rjsy = joystick.get_axis(3)

    # Right trigger (RT)
    rt = joystick.get_axis(5)

    # Face buttons
    a = joystick.get_button(3)  # A → raise
    y = joystick.get_button(0)  # Y → lower

    # Adjust height
    if a:
        height += 1
    if y:
        height -= 1
    height = max(-100, min(100, height))

    # Walking logic
    mode = "stop"
    backwards = False
    walk_type = "flat"

    if ljsy < -0.5:
        mode = "walk"
        backwards = False
    elif ljsy > 0.5:
        mode = "walk"
        backwards = True

    pitch = int(-rjsy * 100)
    roll  = int(rjsx * 40)
    lateral = int(ljsx * 200)
    if backwards:
        lateral = -lateral

    left_bumper  = joystick.get_button(4)  # LB → pause
    right_bumper = joystick.get_button(5)  # RB → start
    record_button = joystick.get_button(6) # Back → toggle record
    start_button  = joystick.get_button(7) # Start → replay

    # Packet to send
    data = {
        "mode": mode,
        "walk_type": walk_type,
        "backwards": backwards,
        "lateral": lateral,
        "height": height,
        "pitch": pitch,
        "roll": roll,
        "speed": int((rt + 1) / 2 * 40),
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
        time.sleep(0.3)  # debounce

    # Store moves if recording
    if recording:
        moves.append((time.time(), data.copy()))

    # --- Send to robot via UDP ---
    sock.sendto(json.dumps(data).encode(), (UDP_IP, UDP_PORT))

    # --- Replay if START pressed ---
    if start_button and moves:
        print("▶️ Replaying moves...")
        for t, move in moves:
            time.sleep(0.01)  # preserve timing
            sock.sendto(json.dumps(move).encode(), (UDP_IP, UDP_PORT))
        print("✅ Replay finished")

    time.sleep(0.01)  # ~100 Hz loop
