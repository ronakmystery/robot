from v2.servos import *

from v2.poses import *

current_pose = pose_default.copy()
set_targets(current_pose)

import math, time

def circle_x(t, amp=40, freq=1.0, phase=0):
    return amp * math.cos(2 * math.pi * freq * t + phase)

def circle_y(t, amp=40, freq=1.0, phase=0):
    return amp * math.sin(2 * math.pi * freq * t + phase)


# Each leg: (hip_channel, knee_channel, invert_y?)
LEG_MAP = [
    (0,1,  2,  +1),   # front-left
    (4,5,  6,  +1),   # front-right
    (8,9, 10, -1),    # back-left
    (12,13,14, -1),    # back-right
]

def update_legs(x, y, backwards=False):
    cmds = {}
    for a,b, c, ysign in LEG_MAP:
        # flip x if walking backwards
        x_val = x if backwards else -x
        y_val = ysign * y
        # cmds[a]  = current_pose[a]  -60
        cmds[b]  = current_pose[b]  + x_val
        cmds[c] = current_pose[c] + y_val
    set_targets(cmds)



def walking_speed(mode="default"):
    profiles = {
        # Indoors
        "carpet_fast":   (40, 3),    # big stride, fast steps
        "carpet_slow":   (30, 2),    # slower, stable on carpet
        "hard_fast":     (25, 3),    # low amp, high freq (avoid slip)
        "hard_slow":     (15, 1.5),  # cautious on slick floor

        # Outdoors / rough terrain
        "grass":         (35, 2),    # medium stride, medium speed
        "rocky":         (20, 1),    # careful, short slow steps
        "sand":          (45, 1.5),  # wide stride, slower so feet dig in

        # Special styles
        "precision":     (10, 1),    # small, careful steps
        "creep":         (15, 0.5),  # very slow, minimal motion
        "bound":         (50, 2.5),  # exaggerated stride, almost “jumping”
        "trot":          (35, 2.5),  # diagonal pairs, rhythmic
        "run":           (45, 3.5),  # max stride + speed (servo stress)

        # Default fallback
        "default":       (20, 2)
    }
    return profiles.get(mode, profiles["default"])



t0 = time.time()
while True:
    t = time.time() - t0

    amp, freq = walking_speed("precision")

    x = circle_x(t, amp=amp, freq=freq)
    y = circle_y(t, amp=amp, freq=freq)


    update_legs(x, y, backwards=False)

    time.sleep(0.01)
