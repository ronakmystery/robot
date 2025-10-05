from adc import read_adc
import time, threading
import RPi.GPIO as GPIO
from driver_servo import spin_servo

PIN = 21
GPIO.setmode(GPIO.BCM)
GPIO.setup(PIN, GPIO.OUT)

p = GPIO.PWM(PIN, 100)
p.start(0)

running = False
pulse_thread = None

def pulse():
    while running:
        n=5
        for dc in range(0, 101, n):
            if not running: break
            p.ChangeDutyCycle(dc)
            time.sleep(0.01)
        for dc in range(100, -1, -n):
            if not running: break
            p.ChangeDutyCycle(dc)
            time.sleep(0.01)

try:
    while True:
        v = read_adc(0)
        print(f"Voltage: {v:.3f} V")

        if v < 0.5:
            spin_servo(0, 1.0)
            if not running:
                running = True
                pulse_thread = threading.Thread(target=pulse, daemon=True)
                pulse_thread.start()
        else:
            spin_servo(0, 0.0)
            running = False
            p.ChangeDutyCycle(0)

        time.sleep(0.1)

except KeyboardInterrupt:
    pass
finally:
    running = False
    if pulse_thread: pulse_thread.join()
    p.stop()
    GPIO.cleanup()