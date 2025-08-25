import socket, time, pygame

UDP_IP, UDP_PORT = "192.168.1.158", 5005
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

pygame.init()
pygame.joystick.init()
js = pygame.joystick.Joystick(0); js.init()

# 012 = RIGHT-FRONT, 456 = LEFT-FRONT
# 8,9,10 = RIGHT-BACK, 12,13,14 = LEFT-BACK

# ---- Front (given) ----
ROLL_RF_INVERT   = True    # ch0  right-front shoulder roll (X)
PITCH_RF_INVERT  = True    # ch1  right-front hip pitch     (Y)
KNEE_RF_INVERT   = False   # ch2  right-front knee (RT)

ROLL_LF_INVERT   = False   # ch4  left-front shoulder roll  (X)
PITCH_LF_INVERT  = False   # ch5  left-front hip pitch      (Y)
KNEE_LF_INVERT   = False   # ch6  left-front knee (LT)

# ---- Back symmetry (mirror front; flip pitch for back legs) ----
ROLL_RB_INVERT   = ROLL_RF_INVERT     # ch8
PITCH_RB_INVERT  = PITCH_RF_INVERT  # ch9 (flip vs front for symmetric gait feel)
KNEE_RB_INVERT   = KNEE_RF_INVERT     # ch10

ROLL_LB_INVERT   = ROLL_LF_INVERT     # ch12
PITCH_LB_INVERT  = PITCH_LF_INVERT  # ch13
KNEE_LB_INVERT   = KNEE_LF_INVERT     # ch14

DEADZONE = 0.08
def dead(v): return 0.0 if abs(v) < DEADZONE else v

def clamp180(a):
    return 180 if a > 180 else 0 if a < 0 else a

def axis_to_angle(v, invert=False):
    if invert: v = -v
    v = max(-1.0, min(1.0, v))
    return clamp180(int(round((v + 1) * 0.5 * 180)))  # -1..1 → 0..180

def trig_to_angle(v, invert=False):
    # Triggers read 1.0 (rest) → -1.0 (pulled) on many XInput drivers.
    t = (v + 1) * 0.5                 # 0..1
    ang = 180 - int(round(t * 180))   # 0 (rest) → 180 (pulled)
    if invert: ang = 180 - ang
    return clamp180(ang)

while True:
    pygame.event.pump()

    # RIGHT stick/trigger → RIGHT legs (front & back)
    rx = dead(js.get_axis(2))    # right stick X
    ry = dead(js.get_axis(3))    # right stick Y
    rt = js.get_axis(5)          # right trigger: 1→-1

    ang0  = axis_to_angle(rx, invert=ROLL_RF_INVERT)   # ch0 RF roll
    ang1  = axis_to_angle(ry, invert=PITCH_RF_INVERT)  # ch1 RF pitch
    ang2  = trig_to_angle(rt, invert=KNEE_RF_INVERT)   # ch2 RF knee

    ang8  = axis_to_angle(rx, invert=ROLL_RB_INVERT)   # ch8 RB roll (mirror)
    ang9  = axis_to_angle(ry, invert=PITCH_RB_INVERT)  # ch9 RB pitch (flipped)
    ang10 = trig_to_angle(rt, invert=KNEE_RB_INVERT)   # ch10 RB knee

    # LEFT stick/trigger → LEFT legs (front & back)
    lx = dead(js.get_axis(0))    # left stick X
    ly = dead(js.get_axis(1))    # left stick Y
    lt = js.get_axis(4)          # left trigger: 1→-1

    ang4  = axis_to_angle(lx, invert=ROLL_LF_INVERT)   # ch4 LF roll
    ang5  = axis_to_angle(ly, invert=PITCH_LF_INVERT)  # ch5 LF pitch
    ang6  = trig_to_angle(lt, invert=KNEE_LF_INVERT)   # ch6 LF knee

    ang12 = axis_to_angle(lx, invert=ROLL_LB_INVERT)   # ch12 LB roll (mirror)
    ang13 = axis_to_angle(ly, invert=PITCH_LB_INVERT)  # ch13 LB pitch (flipped)
    ang14 = trig_to_angle(lt, invert=KNEE_LB_INVERT)   # ch14 LB knee

    # send all 12 channels
    msg = (
        f"0,{ang0},1,{ang1},2,{ang2},"
        f"4,{ang4},5,{ang5},6,{ang6},"
        f"8,{ang8},9,{ang9},10,{ang10},"
        f"12,{ang12},13,{ang13},15,{ang14}"
    ).encode()

    sock.sendto(msg, (UDP_IP, UDP_PORT))
    time.sleep(0.02)
