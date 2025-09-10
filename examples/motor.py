from adafruit_motorkit import MotorKit
import time

kit = MotorKit()

print("Motor 4 forward")
kit.motor1.throttle = 1.0
time.sleep(2)
kit.motor1.throttle = 0
