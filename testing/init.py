import time
import smbus
import json
import os
from threading import Thread, Lock

class PCA9685:
    __MODE1 = 0x00
    __PRESCALE = 0xFE
    __LED0_ON_L = 0x06

    def __init__(self, address=0x40):
        self.bus = smbus.SMBus(1)
        self.address = address
        self.write(self.__MODE1, 0x00)

    def write(self, reg, value):
        self.bus.write_byte_data(self.address, reg, value)

    def read(self, reg):
        return self.bus.read_byte_data(self.address, reg)

    def setPWMFreq(self, freq):
        prescaleval = 25000000.0 / 4096.0 / freq - 1.0
        prescale = int(prescaleval + 0.5)
        oldmode = self.read(self.__MODE1)
        self.write(self.__MODE1, (oldmode & 0x7F) | 0x10)
        self.write(self.__PRESCALE, prescale)
        self.write(self.__MODE1, oldmode)
        time.sleep(0.005)
        self.write(self.__MODE1, oldmode | 0x80)

    def setPWM(self, channel, on, off):
        base = self.__LED0_ON_L + 4 * channel
        self.bus.write_byte_data(self.address, base + 0, on & 0xFF)
        self.bus.write_byte_data(self.address, base + 1, on >> 8)
        self.bus.write_byte_data(self.address, base + 2, off & 0xFF)
        self.bus.write_byte_data(self.address, base + 3, off >> 8)

    def setServoPulse(self, channel, pulse_us):
        ticks = int(pulse_us * 4096 / 20000)  # 20ms = 50Hz
        self.setPWM(channel, 0, ticks)


pwm = PCA9685()
time.sleep(1)  # Allow time for the PCA9685 to initialize
pwm.setPWMFreq(50)

servo_angles = {}
servo_lock = Lock()

def angle_to_pulse(angle):
    return int(500 + (angle / 180.0) * 2000)

def set_servo_angle(channel, angle):
    angle = max(0, min(180, angle))
    pulse = angle_to_pulse(angle)
    with servo_lock:
        pwm.setServoPulse(channel, pulse)
        servo_angles[channel] = angle

servos=[
    0, 1, 2, 
    4, 5, 6, 
    8, 9, 10,
    12, 13, 14
]

A=[0,4,8,12]
B=[1,5,9,13]
C=[2,6,10,14]

offsets = {
    0: 69,  4: 97,  8: 118, 12: 88,  # A
    1: 91, 5: 101, 9: 87, 13: 93,   # B
    2: 82,  6: 98, 10: 98, 14: 83   # C
}



def smooth_servo(servo=0,start=90, end=90, steps=40, delay=0.01):
    for i in range(steps + 1):
        angle = start + (end - start) * i / steps
        set_servo_angle(servo, angle)
        servo_angles[servo] = angle 
        time.sleep(delay)



all_legs = {
    "front_left": (A[0], B[0], C[0]),
    "front_right": (A[1], B[1], C[1]),
    "back_left": (A[2], B[2], C[2]),
    "back_right": (A[3], B[3], C[3]),
}

def move_leg(a, angle1, b, angle2, c, angle3,speed=40):
    t1= Thread(target=smooth_servo, kwargs={"servo": a, "start": servo_angles[a], "end": angle1,"steps": speed})
    t2 = Thread(target=smooth_servo, kwargs={"servo": b, "start": servo_angles[b], "end": angle2,"steps": speed})
    t3 = Thread(target=smooth_servo, kwargs={"servo": c, "start": servo_angles[c], "end": angle3,"steps": speed})

    t1.start()
    t2.start()
    t3.start()

    t1.join()
    t2.join()
    t3.join()

def move_all_legs(deg=0,speed=40):
    threads=[]
    for idx, leg in enumerate(all_legs.values()):
        symmetric_deg=deg
        if idx>=2:
            symmetric_deg=-deg
        for servo in leg:
            t = Thread(target=smooth_servo, kwargs={"servo": servo, "start": servo_angles.get(servo, offsets[servo]), "end": offsets[servo]+symmetric_deg, "steps": speed, "delay": 0.01})
            t.start()
            threads.append(t)
    for t in threads:
        t.join()


def zero_pose():
    move_all_legs(0)



def move_legs(legs=all_legs,d1=0, d2=0, d3=0,speed=20):
    threads=[]
    for idx, leg in enumerate(legs.values()):
        a, b, c = leg
        symmetric_deg = 1
        if idx == 1 or idx == 2:
            symmetric_deg = -1
        if idx >= 2:
            symmetric_deg *= -1
        t= Thread(target=move_leg, args=(a, servo_angles[a]+(d1*symmetric_deg), b, servo_angles[b]+(d2*symmetric_deg), c, servo_angles[c]+(d3*symmetric_deg)), kwargs={"speed": speed})
        t.start()
        threads.append(t)
    for t in threads:
        t.join()


front_legs= {
    "front_left": (A[0], B[0], C[0]),
    "front_right": (A[1], B[1], C[1]),
}
back_legs = {
    "back_left": (A[2], B[2], C[2]),
    "back_right": (A[3], B[3], C[3]),
}

left_legs = {
    "front_left": (A[0], B[0], C[0]),
    "back_left": (A[2], B[2], C[2]),
}

right_legs = {
    "front_right": (A[1], B[1], C[1]),
    "back_right": (A[3], B[3], C[3]),
}

def move_leg_groups(leg_combos):
    threads = []
    for legs, d1, d2, d3, speed in leg_combos:
        t = Thread(target=move_legs, kwargs={
            "legs": legs,
            "d1": d1,
            "d2": d2,
            "d3": d3,
            "speed": speed
        })
        t.start()
        threads.append(t)

    for t in threads:
        t.join()

def default_pose():
    move_leg_groups([
        (front_legs,  0, 40,  50, 10),  # front legs
        (back_legs,  0,  40,  50, 10),  # back legs
    ])

    
