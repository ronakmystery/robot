from driver_servo import *
import time

try:
    while True:
        spin_servo(0, 1.0)
        time.sleep(0.1)
except KeyboardInterrupt:
    spin_servo(0, 0.0)
