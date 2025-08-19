from init import *

print("🔻 Shutting down, releasing servos...")
for servo in servos:
    pwm.setServoPulse(servo, 0)