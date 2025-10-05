# controller.py
import pygame, socket, time

PI_IP = "10.171.53.160"
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

def nudge_axis(val, max_step=20, deadzone=0.2):
    if abs(val) < deadzone:
        return 0
    return int(val * max_step)

while True:
    pygame.event.pump()

    # --- Tank drive with D-Pad + RT throttle ---
    hat_x, hat_y = js.get_hat(0)
    rt = js.get_axis(5)
    throttle = (rt + 1) / 2
    base_speed = 100
    speed_val = int(base_speed * throttle)

    left_speed, right_speed = 0, 0
    if hat_y == -1:
        left_speed, right_speed = speed_val, speed_val
    elif hat_y == 1:
        left_speed, right_speed = -speed_val, -speed_val
    elif hat_x == -1:
        left_speed, right_speed = -speed_val, speed_val
    elif hat_x == 1:
        left_speed, right_speed = speed_val, -speed_val

    # --- Joysticks give scaled nudges ---
    servo1 = nudge_axis(js.get_axis(2))   # left stick X
    servo2 = nudge_axis(-js.get_axis(0))  # left stick Y
    servo3 = nudge_axis(-js.get_axis(1))  # right stick X
    servo4 = nudge_axis(js.get_axis(3))   # right stick Y

    msg = f"{left_speed},{right_speed},{servo1},{servo2},{servo3},{servo4}"
    sock.sendto(msg.encode(), (PI_IP, PI_PORT))
    print("➡️", msg)

    time.sleep(0.05)  # ~20 updates/sec
