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
        ticks = int(pulse_us * 4096 / 20000)  
        self.setPWM(channel, 0, ticks)


pwm = PCA9685()
time.sleep(1) 
pwm.setPWMFreq(50)


def angle_to_pulse(angle):
    return int(500 + (angle / 180.0) * 2000)


def set_servo_angle(channel, angle):
    angle = max(0, min(180, angle))
    pulse = angle_to_pulse(angle)
    pwm.setServoPulse(channel, pulse)


def release_servo(channel):
    pwm.setPWM(channel, 0, 0)

def spin_servo(channel, speed):
    pulse = int(1500 + speed * 500)  
    pwm.setServoPulse(channel, pulse)
