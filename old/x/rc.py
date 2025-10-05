# controller_4legs.py
import socket, time, pygame

UDP_IP, UDP_PORT = "192.168.1.158", 5005
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

pygame.init()
pygame.joystick.init()
js = pygame.joystick.Joystick(0); js.init()

# ---- Helpers ----
DEADZONE = 0.08
def dead(v): return 0.0 if abs(v) < DEADZONE else v
def clamp180(a): return max(0, min(180, a))

def axis_to_angle(v, invert=False):
    if invert: v = -v
    v = max(-1.0, min(1.0, v))
    return clamp180(int(round((v + 1) * 90)))  # -1..1 → 0..180

def trig_to_angle(v, invert=False):
    # Trigger: 1.0 (rest) → -1.0 (pressed)
    t = (v + 1) * 0.5
    ang = 180 - int(round(t * 180))
    if invert: ang = 180 - ang
    return clamp180(ang)

# ── FOUR LEGS ─────────────────────────────────────────────
# RF: 0 roll, 1 pitch, 2 knee
# LF: 4 roll, 5 pitch, 6 knee
# RB: 8 roll, 9 pitch, 10 knee
# LB: 12 roll, 13 pitch, 14 knee

# Keep consistent with your current choice (all True). Adjust if needed.
ROLL_RF_INV = True; PITCH_RF_INV = True; KNEE_RF_INV = True
ROLL_LF_INV = True; PITCH_LF_INV = True; KNEE_LF_INV = True
ROLL_RB_INV = True; PITCH_RB_INV = True; KNEE_RB_INV = True
ROLL_LB_INV = True; PITCH_LB_INV = True; KNEE_LB_INV = True

while True:
    pygame.event.pump()

    # Right side (RF & RB) from right stick/trigger
    rx = dead(js.get_axis(2))   # right stick X
    ry = dead(js.get_axis(3))   # right stick Y
    rt = js.get_axis(5)         # right trigger

    ang0  = axis_to_angle(rx, invert=ROLL_RF_INV)   # RF roll (ch0)
    ang1  = axis_to_angle(ry, invert=PITCH_RF_INV)  # RF pitch (ch1)
    ang2  = trig_to_angle(rt, invert=KNEE_RF_INV)   # RF knee (ch2)

    ang8  = axis_to_angle(rx, invert=ROLL_RB_INV)   # RB roll (ch8)
    ang9  = axis_to_angle(ry, invert=PITCH_RB_INV)  # RB pitch (ch9)
    ang10 = trig_to_angle(rt, invert=KNEE_RB_INV)   # RB knee (ch10)

    # Left side (LF & LB) from left stick/trigger
    lx = dead(js.get_axis(0))   # left stick X
    ly = dead(js.get_axis(1))   # left stick Y
    lt = js.get_axis(4)         # left trigger

    ang4  = axis_to_angle(lx, invert=ROLL_LF_INV)   # LF roll (ch4)
    ang5  = axis_to_angle(ly, invert=PITCH_LF_INV)  # LF pitch (ch5)
    ang6  = trig_to_angle(lt, invert=KNEE_LF_INV)   # LF knee (ch6)

    ang12 = axis_to_angle(lx, invert=ROLL_LB_INV)   # LB roll (ch12)
    ang13 = axis_to_angle(ly, invert=PITCH_LB_INV)  # LB pitch (ch13)
    ang14 = trig_to_angle(lt, invert=KNEE_LB_INV)   # LB knee (ch14)

    # Send all 12 channels
    msg = (
        f"0,{ang0},1,{ang1},2,{ang2},"
        f"4,{ang4},5,{ang5},6,{ang6},"
        f"8,{ang8},9,{ang9},10,{ang10},"
        f"12,{ang12},13,{ang13},14,{ang14}"
    ).encode()

    sock.sendto(msg, (UDP_IP, UDP_PORT))
    time.sleep(0.02)
