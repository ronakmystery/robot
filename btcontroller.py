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

# --- State ---
height = 0   # baseline height

while True:
    pygame.event.pump()

    # Sticks
    ljsx = joystick.get_axis(0)   # left stick X (lateral)
    ljsy = joystick.get_axis(1)   # left stick Y (forward/back)

    rjsx = joystick.get_axis(2)   # right stick X (turn)
    rjsy = joystick.get_axis(3)   # right stick Y (unused)

    # Right trigger (RT)
    rt = joystick.get_axis(4)     # -1 → released, +1 → pressed

    # Face buttons
    a = joystick.get_button(4)  # A → raise
    y = joystick.get_button(0)  # Y → lower

    # Adjust height
    if a:
        height += 10
    if y:
        height -= 10

    # Clamp height range
    height = max(-100, min(100, height))

    # Walking from left stick Y
    mode = "stop"
    backwards = False
    walk_type = "flat"

    if ljsy < -0.5:  # push stick up
        mode = "walk"
        backwards = False
    elif ljsy > 0.5: # push stick down
        mode = "walk"
        backwards = True
    
    pitch = int(-rjsy * 100) 
    roll=int(rjsx *40)

    lateral = int(ljsx * 100)
    if backwards:
        lateral = -lateral


    ljsb= joystick.get_button(13) 

    pause_button= joystick.get_button(10)
    start_button= joystick.get_button(11)

    # --- Send packet ---
    data = {
        "mode": mode,
        "walk_type": walk_type,
        "backwards": backwards,
        "lateral": lateral,
        "height": height,
        "pitch": pitch,
        "roll": roll,   
        "speed": int((rt + 1) / 2 *50),  
        "pause": pause_button,
        "start": start_button,
    }
    print(data)

    try:
        requests.post(ROBOT_API, json=data, timeout=0.1)
    except:
        pass

    time.sleep(0.01)
