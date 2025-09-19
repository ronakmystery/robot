import pygame, socket, time

PI_IP = "10.236.55.155"   # <-- your Pi’s IP
PI_PORT = 5007
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

pygame.init()
pygame.joystick.init()
if pygame.joystick.get_count() == 0:
    print("❌ No controller found!")
    exit()
js = pygame.joystick.Joystick(0)
js.init()
print(f"🎮 Controller: {js.get_name()}")

def clamp(val, vmin, vmax):
    return max(vmin, min(vmax, val))

def map_axis(val, in_min=-1, in_max=1, out_min=0, out_max=180):
    return int((val - in_min) * (out_max - out_min) / (in_max - in_min) + out_min)

while True:
    pygame.event.pump()

    # --- Inputs ---
    ly = js.get_axis(1)      # forward/back (no minus now)
    lx = js.get_axis(0)      # left/right steering
    rt = js.get_axis(5)      # RT: -1 → +1

    throttle = (rt + 1) / 2  # normalize 0–1

    # --- Arcade drive math ---
    left_val  = (ly + lx) * throttle
    right_val = (ly - lx) * throttle

    # Scale to signed -100..100
    left_speed  = int(clamp(left_val * 100, -100, 100))
    right_speed = int(clamp(right_val * 100, -100, 100))

    # --- Right stick Y for arm servo ---
    ry = js.get_axis(3)
    servo2 = map_axis(ry)

    # --- Right bumper for claw ---
    r_bumper = js.get_button(5)  # Xbox RB = 5
    claw = 100 if r_bumper else 180

    # UDP message: "left,right,claw,servo2"
    msg = f"{left_speed},{right_speed},{claw},{servo2}"
    sock.sendto(msg.encode(), (PI_IP, PI_PORT))
    print("➡️", msg)

    time.sleep(0.05)
