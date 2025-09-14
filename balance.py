from sensors.imu import get_roll_pitch_angles, reset_imu
import threading, time
from servos import *
from poses import *

time.sleep(1)
baseline = pose_default.copy()
balance_offset = {ch: 0.0 for ch in baseline}

recovering = False

def balance_loop():
    global baseline, balance_offset, recovering
    while True:
        roll, pitch = get_roll_pitch_angles()

        print(f"Roll: {roll:.1f}, Pitch: {pitch:.1f}")
        pitch=-pitch


        # # --- Flip over: recover then protect ---
        # if abs(roll) > 90:

            
        #     baseline = protect       # then protect crouch
        #     balance_offset = {ch: 0.0 for ch in baseline}
        #     set_targets(baseline)
        #     time.sleep(1)

        #     baseline = recover1      # first flip pose
        #     balance_offset = {ch: 0.0 for ch in baseline}
        #     set_targets(baseline)
        #     time.sleep(1)          # short hold for flip

        #     baseline = recover2      # second flip pose
        #     balance_offset = {ch: 0.0 for ch in baseline}
        #     set_targets(baseline)
        #     time.sleep(1)          # short hold for flip

        #     baseline = protect       # then protect crouch
        #     balance_offset = {ch: 0.0 for ch in baseline}
        #     set_targets(baseline)

        #     reset_imu()

        #     recovering = True

        # --- Normal protect trigger ---
        if abs(roll) > 40 or abs(pitch) > 40:
            if not recovering:
                print("⚠️ Over 40° → protect")
                baseline = pose_protect
                balance_offset = {ch: 0.0 for ch in baseline}
                recovering = True

        else:
            if recovering and abs(roll) < 5 and abs(pitch) < 5:
                print("✅ Stable → back to default")
                baseline = pose_default
                balance_offset = {ch: 0.0 for ch in baseline}
                recovering = False

            # Balance correction in stable mode
            scale = 4
            if abs(roll) > abs(pitch):
                balance_offset.update({
                    1: -roll * scale, 5: -roll * scale,
                    9:  roll * scale, 13: roll * scale,
                    2: -roll * scale, 6: -roll * scale,
                    10: roll * scale, 14: roll * scale,
                })
            else:
                balance_offset.update({
                    1:  pitch * scale, 5: -pitch * scale,
                    9: -pitch * scale, 13: pitch * scale,
                    2:  pitch * scale, 6: -pitch * scale,
                    10:-pitch * scale, 14: pitch * scale,
                })

        time.sleep(0.01)


def start_balance_thread():
    threading.Thread(target=balance_loop, daemon=True).start()


start_balance_thread()

# Main loop
while True:
    set_targets({
        ch: baseline[ch] + balance_offset.get(ch, 0)
        for ch in baseline
    })
    time.sleep(0.01)
