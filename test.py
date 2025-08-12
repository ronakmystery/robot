from threading import Thread
from init import *
import math, time

def circle_leg(leg_key="front_left",
               radius_b=15, radius_c=15,
               freq_hz=0.6,
               duration=5.0,
               start_speed=0.1,  # was dynamic_speed initializer
               sway_a=0,
               phase=0.0):

    a, b, c = all_legs[leg_key]
    cb, cc, ca = servo_angles[b], servo_angles[c], servo_angles[a]

    two_pi_f = 2 * math.pi * freq_hz
    start = time.time()
    dyn = start_speed  # keep as float; convert only when calling move_leg

    while time.time() - start < duration:
        t = time.time() - start
        theta = two_pi_f * t + phase

        # ramp and clamp
        dyn = min(dyn + 0.02, 20.0)
        steps_i = max(1, int(round(dyn)))  # <-- ensure integer

        b_target = cb + radius_b * math.cos(theta)
        c_target = cc + radius_c * math.sin(theta)
        a_target = ca + (sway_a * math.sin(theta)) if sway_a else ca

        move_leg(a, a_target, b, b_target, c, c_target, speed=steps_i)


threads = []

rb_front, rc_front = 20, 30
rb_back,  rc_back  = -20, -30

phases = {
    "front_left":  0.0,
    "front_right": math.pi/2,
    "back_right":  math.pi,
    "back_left":   3*math.pi/2,
}

for leg in ["front_left", "front_right", "back_right", "back_left"]:
    rb = rb_front if "front" in leg else rb_back
    rc = rc_front if "front" in leg else rc_back
    t = Thread(target=circle_leg, kwargs={
        "leg_key": leg,
        "radius_b": rb,
        "radius_c": rc,
        "freq_hz": 0.5,
        "duration":3,
        "start_speed": 0.1,
        "sway_a": 0,
        "phase": phases[leg],
    })
    threads.append(t)
    t.start()

for t in threads:
    t.join()



rb_front, rc_front = 40, 50
rb_back,  rc_back  = -40, -50

for leg in ["front_left", "front_right", "back_right", "back_left"]:
    rb = rb_front if "front" in leg else rb_back
    rc = rc_front if "front" in leg else rc_back
    t = Thread(target=circle_leg, kwargs={
        "leg_key": leg,
        "radius_b": rb,
        "radius_c": rc,
        "freq_hz": 3,
        "duration":3.0,
        "start_speed": 0.1,
        "sway_a": 0,
        "phase": phases[leg],
    })
    threads.append(t)
    t.start()

for t in threads:
    t.join()
