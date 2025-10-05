from v2.servos import *

print("🔻 Shutting down, releasing servos...")
for servo in servos:
    pwm.setServoPulse(servo, 0)