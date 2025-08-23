import socket, time, pygame

UDP_IP, UDP_PORT = "192.168.1.158", 5005
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

pygame.init()
pygame.joystick.init()
js = pygame.joystick.Joystick(0); js.init()

# --- symmetry config ---
ROLL_L_INVERT  = False   # ch0  left shoulder roll  (X)
PITCH_L_INVERT = True    # ch1  left hip pitch      (Y)
ROLL_R_INVERT  = True    # ch4  right shoulder roll (X) ← mirror of left
PITCH_R_INVERT = False   # ch5  right hip pitch     (Y) ← mirror of left

DEADZONE = 0.08
def dead(v): return 0.0 if abs(v) < DEADZONE else v

def axis_to_angle(v, invert=False):
    if invert: v = -v
    v = max(-1.0, min(1.0, v))
    return int(round((v + 1) * 0.5 * 180))  # -1..1 → 0..180

while True:
    pygame.event.pump()

    # Left leg (0,1,2)
    lx = dead(js.get_axis(0))
    ly = dead(js.get_axis(1))
    lt = js.get_axis(4)                    # 1→-1
    lt_m = (lt + 1) * 0.5                  # 0..1

    ang0 = axis_to_angle(lx, invert=ROLL_L_INVERT)
    ang1 = axis_to_angle(ly, invert=PITCH_L_INVERT)
    ang2 = 180 - int(round(lt_m * 180))    # knee bend on pull

    # Right leg (4,5,6) — mirrored feel
    rx = dead(js.get_axis(2))
    ry = dead(js.get_axis(3))
    rt = js.get_axis(5)                    # 1→-1
    rt_m = (rt + 1) * 0.5

    ang4 = axis_to_angle(rx, invert=ROLL_R_INVERT)
    ang5 = axis_to_angle(ry, invert=PITCH_R_INVERT)
    ang6 = 180 - int(round(rt_m * 180))    # knee bend on pull

    # send 0,1,2 (left) and 4,5,6 (right)
    msg = f"0,{ang0},1,{ang1},2,{ang2},4,{ang4},5,{ang5},6,{ang6}".encode()
    sock.sendto(msg, (UDP_IP, UDP_PORT))
    # print(msg)

    time.sleep(0.02)
