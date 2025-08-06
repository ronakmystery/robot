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
    0: 75,  4: 96,  8: 112, 12: 90,  # A
    1: 99, 5: 102, 9: 88, 13: 84,   # B
    2: 84,  6: 96, 10: 107, 14: 75   # C
}

SERVO_ANGLES_FILE = "servo_angles.json"
def load_servo_angles():
    global servo_angles
    if os.path.exists(SERVO_ANGLES_FILE):
        with open(SERVO_ANGLES_FILE, "r") as f:
            try:
                servo_angles = json.load(f)
                # Convert all keys to int (JSON keys are always strings)
                servo_angles = {int(k): v for k, v in servo_angles.items()}
                print("✅ Servo angles loaded:", servo_angles)
            except json.JSONDecodeError:
                print("⚠️ Failed to parse servo_angles.json. Using defaults.")
    else:
        print("📂 servo_angles.json not found. Starting fresh.")
load_servo_angles()

def save_servo_angles():
    with open(SERVO_ANGLES_FILE, "w") as f:
        json.dump(servo_angles, f)
        print("✅ Servo angles saved:", servo_angles.keys())


def smooth_servo(servo=0,start=90, end=90, steps=40, delay=0.01):
    for i in range(steps + 1):
        angle = start + (end - start) * i / steps
        set_servo_angle(servo, angle)
        servo_angles[servo] = angle 
        time.sleep(delay)
