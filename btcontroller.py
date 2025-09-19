import pygame, time, requests, json

# Init controller
pygame.init()
pygame.joystick.init()

if pygame.joystick.get_count() == 0:
    print("No controller found!")
    exit()

joystick = pygame.joystick.Joystick(0)
joystick.init()
print(f"Connected to {joystick.get_name()}")

ip="10.236.55.45"
ROBOT_API = f"http://{ip}:5000/api/walk"

# --- State ---
height = 0
moves = []         # store sent packets
recording = False  # toggle recording



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
        height += 10
    if y:
        height -= 10

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

    left_bumper = joystick.get_button(4)
    right_bumper = joystick.get_button(5)
    # Buttons
    record_button = joystick.get_button(6)
    start_button = joystick.get_button(7)

    data = {
        "mode": mode,
        "walk_type": walk_type,
        "backwards": backwards,
        "lateral": lateral,
        "height": height,
        "pitch": pitch,
        "roll": roll,
        "speed": int((rt + 1) / 2 * 40),
        "pause": left_bumper,
        "start": right_bumper,
    }

    # --- Recording toggle ---
    if record_button:
        recording = not recording
        if recording:
            moves.clear()   # ✅ clear old moves when starting new record
            print("🔴 Recording ON (cleared old moves)")
        else:
            save_moves()
            print("⏹️ Recording OFF")
        time.sleep(0.3)  # debounce




    # Store moves if recording
    if recording:
        moves.append((time.time(), data.copy()))
    

    # --- Send to robot ---
    try:
        requests.post(ROBOT_API, json=data, timeout=0.1)
    except:
        pass

    # --- Replay if START pressed ---
    if start_button and moves:
        print("▶️ Replaying moves...")
        for t, move in moves:
            time.sleep(.01)  # preserve timing
            try:
                requests.post(ROBOT_API, json=move, timeout=0.1)
            except:
                pass
        print("✅ Replay finished")

    time.sleep(0.01)
