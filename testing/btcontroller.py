import pygame, time, requests

# Init controller
pygame.init()
pygame.joystick.init()

if pygame.joystick.get_count() == 0:
    print("No controller found!")
    exit()

joystick = pygame.joystick.Joystick(0)
joystick.init()
print(f"Connected to {joystick.get_name()}")

ROBOT_API = "http://localhost:5000/api/walk"

while True:
    pygame.event.pump()

    # Left stick X → lateral offset
    lx = joystick.get_axis(0)   # -1 left, +1 right
    lateral = int(-lx * 200)
    # Left stick Y → pitch (split into up/down like triggers)
    ly = joystick.get_axis(1)   # -1 up, +1 down
    pitch_up   = int(max(-ly, 0) * 200)   # pull back = nose up
    pitch_down = int(max(ly, 0) * 200)    # push forward = nose down

    # Triggers: separate
    lt = joystick.get_axis(5)  # left trigger
    rt = joystick.get_axis(4)  # right trigger

    # Normalize triggers to 0–1
    lt_val = (lt + 1) / 2
    rt_val = (rt + 1) / 2

    height_up   = int(rt_val * 200)   # RT raises right side
    height_down = int(lt_val * 200)   # LT lowers left side

    # Buttons
    btn_a = joystick.get_button(0)  # A
    btn_b = joystick.get_button(1)  # B
    btn_x = joystick.get_button(3)  # X
    btn_y = joystick.get_button(4)  # Y

    mode = "stop"
    backwards = False
    walk_type = "carpet_slow"  # default gait

    # Forward
    if btn_a or btn_x:
        mode = "walk"
        backwards = False
        walk_type = "carpet_slow" if btn_a else "carpet_fast"

    # Backward
    elif btn_b or btn_y:
        mode = "walk"
        backwards = True
        walk_type = "carpet_slow" if btn_b else "carpet_fast"

    data = {
        "mode": mode,
        "walk_type": walk_type,
        "backwards": backwards,
        "lateral": lateral,
        "height_up": height_up,
        "height_down": height_down,
        "pitch_up": pitch_up,
        "pitch_down": pitch_down
    }
    print(data)

    try:
        requests.post(ROBOT_API, json=data, timeout=0.05)
    except:
        pass

    time.sleep(0.05)
