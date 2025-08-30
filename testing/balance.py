from sensors.imu import get_roll_pitch_angles
import threading, time
from servos import *


# Shared output: balance offsets per servo

# Optional: baseline, in case you want it inside here later
baseline = {
    0: 120, 1: 90,  2: 60,
    4:  60, 5: 90,  6: 120,
    8: 120, 9: 90, 10: 60,
    12: 60, 13: 90, 14: 120,
}

balance_offset = {ch: 0.0 for ch in baseline}
stand = {
    0: 120, 1: 90,  2: 60,
    4: 60,  5: 90,  6: 120,
    8: 120, 9: 90, 10: 60,
    12:60, 13: 90, 14: 120,
}

crouch = {
        0: 180, 1: 0,  2: 0,
        4: 0,   5: 180,6: 180,
        8: 180, 9: 0,  10: 0,
        12: 0,  13: 180,14: 180,
    }


def balance_loop():
    global baseline
    global balance_offset
    recover=False
    while True:
        roll, pitch = get_roll_pitch_angles()
        print(roll, pitch)

        if abs(roll) > 40 or abs(pitch) > 40:
            baseline=crouch
            balance_offset = {ch: 0.0 for ch in baseline}
            recover=True
        else:
            if recover:
                if abs(roll) < 5 and abs(pitch) < 5:
                    baseline=stand
                    balance_offset = {ch: 0.0 for ch in baseline}
                    recover=False
            if abs(roll) > abs(pitch):
                scale=4
                balance_offset.update({
                    1: -roll*scale,
                    5: -roll*scale,
                    9:  roll*scale,
                    13: roll*scale,

                    2: -roll*scale,
                    6: -roll*scale,
                    10: roll*scale,
                    14: roll*scale
                })
            else:
                scale=4
                balance_offset.update({

                    1:  pitch*scale,
                    5:  -pitch*scale,
                    9:  -pitch*scale,
                    13: pitch*scale,

                    2:  pitch*scale,
                    6:  -pitch*scale,
                    10:-pitch*scale,
                    14: pitch*scale
            })

        time.sleep(0.01)

# Start it in background
def start_balance_thread():
    threading.Thread(target=balance_loop, daemon=True).start()



start_balance_thread()
# Main control loop
while True:
    set_targets({
        ch: baseline[ch] + balance_offset.get(ch, 0)
        for ch in baseline
    })
    time.sleep(0.01)


    