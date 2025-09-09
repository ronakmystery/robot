from adc import read_adc
import time
import RPi.GPIO as GPIO

GPIO.setmode(GPIO.BCM)
GPIO.setup(21, GPIO.OUT)


from driver_servo import spin_servo
if __name__ == "__main__":
    while True:
        v = read_adc(0)   # read channel A0
        print(f"Voltage: {v:.3f} V")

        if v<.5:
            spin_servo(0, 1.0)   
            
            GPIO.output(21, 1)  # ON
        else:
            spin_servo(0, 0.0)
            GPIO.output(21, 0)  # OFF
        time.sleep(0.1)
