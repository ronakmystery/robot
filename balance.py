


from imu import *


from init import *




def apply_default_pose_to_offsets():
    for idx, (name, (a, b, c)) in enumerate(all_legs.items()):
        # roll: based on "left"/"right" in name
        roll_sign = 1 if "left" in name else -1

        # pitch: based on index (even = +, odd = -)
        pitch_sign = 1 if idx % 2 == 0 else -1

        back_raise=10 if "back" in name else 0

        offsets[a] += 0 * roll_sign       # A = shoulder
        offsets[b] += 70 * pitch_sign     # B = upper leg
        offsets[c] += 80 * pitch_sign - (back_raise*pitch_sign)     # C = lower leg

apply_default_pose_to_offsets()



A = {k: offsets[k] for k in (0, 4, 8, 12)}
B = {k: offsets[k] for k in (1, 5, 9, 13)}
C = {k: offsets[k] for k in (2, 6, 10, 14)}

# Each leg = (A, B, C)
all_legs_servos = {
    0: (0, 1, 2),    # front left
    1: (4, 5, 6),    # front right
    2: (8, 9, 10),   # back left
    3: (12, 13, 14)  # back right
}

def clamp(x, lo=-60, hi=60):
    return max(lo, min(x, hi))

def move_servo_threaded(servo, delta):
    base = offsets.get(servo)
    start = servo_angles.get(servo, base)
    end = base + delta
    smooth_servo(servo=servo, start=start, end=end, steps=10, delay=0)



while True:
    roll, pitch = get_roll_pitch_angles()

    roll = clamp(roll * 0.3)
    pitch = clamp(pitch * 0.15)

    threads = []

    for idx, leg in all_legs_servos.items():
        # Apply symmetry: back legs get inverted roll/pitch
        sym_roll = -roll if idx < 2 else roll
        sym_pitch = -pitch if idx % 2 == 0 else pitch

        a_servo, b_servo, c_servo = leg


        # A responds to roll, B & C respond to pitch
        t1 = Thread(target=move_servo_threaded, args=(a_servo, sym_roll))
        t2 = Thread(target=move_servo_threaded, args=(b_servo, sym_pitch))
        t3 = Thread(target=move_servo_threaded, args=(c_servo, -sym_pitch))

        for t in (t1, t2, t3):
            t.start()
            threads.append(t)

    for t in threads:
        t.join()


