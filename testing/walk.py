from balance import *

import time

start_balance_thread()

current_pose = {
    0: 120, 1: 90,  2: 60,
    8: 120, 9: 90, 10: 60,
    4: 60,  5: 90,  6: 120,
    12:60, 13: 90, 14: 120,
}


balanced_servos = [0,1,2,4, 5, 6, 8, 9, 10, 12, 13, 14]

#servo groups
A=[0,4,8,12]
B=[1,5,9,13]
C=[2,6,10,14]

all_legs = {
    "front_left": (A[0], B[0], C[0]),
    "front_right": (A[1], B[1], C[1]),
    "back_left": (A[2], B[2], C[2]),
    "back_right": (A[3], B[3], C[3]),
}

leg_names = list(all_legs.keys())
current_leg = {"name": leg_names[0]}  # Mutable dict for safe sharing


def leg_selector_thread():
    i = 0
    while True:
        current_leg["name"] = leg_names[i % len(leg_names)]
        i += 1
        time.sleep(3)

threading.Thread(target=leg_selector_thread, daemon=True).start()



crouch = {
        0: 180, 1: 0,  2: 0,
        4: 0,   5: 180,6: 180,
        8: 180, 9: 0,  10: 0,
        12: 0,  13: 180,14: 180,
    }

while True:
    print("Current leg:", current_leg["name"])

    # Channels for the leg being raised
    disabled_ch = set(all_legs[current_leg["name"]])

    # Apply balance to all servos *except* the current leg
    target = {}
    for ch in current_pose:
        if ch not in disabled_ch:
            offset = balance_offset.get(ch, 0)
            target[ch] = current_pose[ch] + offset
        else:
            leg=all_legs[current_leg["name"]]
            set_targets({leg[1]: crouch[leg[1]]+30})

    set_targets(target)

    time.sleep(0.01)