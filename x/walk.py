from threading import Thread
from init import *
import time

zero_pose()
default_pose()

def leg_pattern():
    time.sleep(1)
    smooth_servo(0, servo_angles[0], servo_angles[0] + 15, 10, 0.01)
    smooth_servo(5, servo_angles[5], servo_angles[5] - 20, 10, 0.01)
    smooth_servo(6, servo_angles[6], servo_angles[6] + 20, 10, 0.01)

    time.sleep(1)
    smooth_servo(0, servo_angles[0], servo_angles[0] + 20, 10, 0.01)
    smooth_servo(2, servo_angles[2], servo_angles[2] - 20, 10, 0.01)
    smooth_servo(4, servo_angles[4], servo_angles[4] - 15, 10, 0.01)


while True:
    leg_pattern()
    t = Thread(target=leg_pattern)
    t.start()
    t.join()
    time.sleep(1)