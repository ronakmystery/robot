import pygame, time
from adafruit_motorkit import MotorKit

kit = MotorKit(address=0x60)

pygame.init()
pygame.joystick.init()

if pygame.joystick.get_count() == 0:
    exit("No controller found!")

js = pygame.joystick.Joystick(0)
js.init()
print("Controller connected")

try:
    while True:
        pygame.event.pump()
        ly = js.get_axis(1)
        throttle = -ly if abs(ly) > 0.1 else 0
        kit.motor1.throttle = throttle
        print(throttle)
        time.sleep(0.05)

except KeyboardInterrupt:
    kit.motor1.throttle = 0
    print("Stopped")
