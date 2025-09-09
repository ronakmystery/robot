import RPi.GPIO as GPIO, time



GPIO.setmode(GPIO.BCM)
GPIO.setup(21, GPIO.OUT)




# #blink
# while True:
#     GPIO.output(21, 1)  # ON
#     time.sleep(1)
#     GPIO.output(21, 0)  # OFF
#     time.sleep(1)







#pulse
p = GPIO.PWM(21, 100); p.start(0)

while True:
    for dc in range(0,101,5): 
        p.ChangeDutyCycle(dc)
        time.sleep(0.05)
    for dc in range(100,-1,-5): 
        p.ChangeDutyCycle(dc)
        time.sleep(0.05)
