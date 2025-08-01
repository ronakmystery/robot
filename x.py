from threading import Thread, Lock
import time
import json
import os
import atexit

from flask import Flask, render_template, jsonify, request, send_file

import smbus
import math
import random

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


app = Flask(__name__)

POSES_FILE = "poses.json"

# --- Global state ---
poses = {}
servo_angles = {}
servo_lock = Lock()


def load_poses():
    global poses
    if os.path.exists(POSES_FILE):
        with open(POSES_FILE, "r") as f:
            try:
                poses = json.load(f)
                print("✅ Poses loaded:", poses.keys())
            except json.JSONDecodeError:
                print("⚠️ Failed to load poses.json. Using built-in default.")
load_poses()


def angle_to_pulse(angle):
    return int(500 + (angle / 180.0) * 2000)

def set_servo_angle(channel, angle):
    angle = max(0, min(180, angle))
    pulse = angle_to_pulse(angle)
    with servo_lock:
        pwm.setServoPulse(channel, pulse)
        servo_angles[channel] = angle



servos=[15,14,13,12,7,6,5,4]

def move_two_servos(ch1, angle1, ch2, angle2):

    t1 = Thread(target=set_servo_angle, args=(ch1, angle1))
    t2 = Thread(target=set_servo_angle, args=(ch2, angle2))

    t1.start()
    t2.start()

    t1.join()
    t2.join()


legs={
    "front_left": [12, 7,1],
    "front_right": [13, 6,1],
    "back_left": [15, 5,-1],
    "back_right": [14, 4,-1]
}



def pose_to_angles(pose):
    for leg in legs.values():
        a, b, _ = leg
        angle_a = pose.get(str(a))
        angle_b = pose.get(str(b))
        if angle_a is not None and angle_b is not None:
            move_two_servos(a, angle_a, b, angle_b)
        time.sleep(0.1)  # Small delay to ensure servos are set


def default_pose():
    pose_to_angles(poses["x"])
default_pose()  # Set initial pose
time.sleep(1)  # Allow time for servos to reach position



def steps_for_degrees(degrees, step_resolution):
    radians = math.radians(degrees)  # convert degrees to radians
    return int(radians * step_resolution)

# === EASING FUNCTIONS ===

def linear(t):
    return t

def ease_out_cubic(t):
    return 1 - (1 - t) ** 3

# === PATH FUNCTIONS ===

def path_circle(t, r, center, c):
    t *= c
    x = center + r * math.cos(t)
    y = center + r * math.sin(t)
    return int(x), int(y)

def path_semi_lift(t, r, center, c):
    t *= c
    x = center + r * math.cos(t)
    y = center
    if t % (2 * math.pi) < math.pi:  # lift on forward swing
        y += r * 0.5 * math.sin(t)
    return int(x), int(y)

# === LEG MOVEMENT FUNCTION ===

def clockwise_leg(leg, step_res=30, radius=50, center=90, path_fn=linear, ease_fn=linear, phase=0.0):
    a, b, c = leg
    steps = steps_for_degrees(360, step_res)
    for i in range(steps):
        prog = i / steps
        theta = 2 * math.pi * prog + 2 * math.pi * phase 
        theta=-theta  # Reverse direction for clockwise 
        x, y = path_fn(theta, radius, center, c)
        move_two_servos(a, x, b, y)


# === GAIT CONTROLLER ===
def gait_mode(rad=30,path=path_circle, ease=ease_out_cubic,steps=30):


    threads = []
    for idx, leg in enumerate(legs.values()):
        phase = (idx % 2) * 0.5
        t = Thread(target=clockwise_leg,
                   args=(leg, steps, rad, 90, path, ease))
        t.start()
        threads.append(t)
    
    return threads





# for _ in range(4):  # Walk 3 times
#     threads = gait_mode(rad=10, path=path_circle, ease=linear, steps=10)
#     for t in threads:
#         t.join()



@app.route('/api/walk', methods=["POST"])
def trigger_walk():
    default_pose()  # Ensure we start from a known pose
    time.sleep(1)
    for _ in range(2):  # Walk 3 times
        threads = gait_mode(rad=20, path=path_circle, ease=linear, steps=40)
        for t in threads:
            t.join()
    pose_to_angles(poses["sit"])  # Ensure we return to a known pose after walking


@app.route('/api/run', methods=["POST"])
def trigger_run():
    default_pose()  # Ensure we start from a known pose
    time.sleep(1)
    for _ in range(2):  # Run 3 times
        threads = gait_mode(rad=20, path=path_circle, ease=linear, steps=20)
        for t in threads:
            t.join()

    default_pose()  # Return to default pose after running
    pose_to_angles(poses["stretch"])  # Ensure we return to a known pose after running


# --- API Routes ---
@app.route('/api/angle/<int:channel>/<int:angle>', methods=["POST"])
def set_angle_for_servo(channel, angle):
    set_servo_angle(channel, angle)
    return jsonify({"channel": channel, "angle": angle})

@app.route('/api/state')
def get_state():
    return jsonify(servo_angles)

@app.route('/')
def index():
    return render_template('index.html')




# --- Start Server ---
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=False)


# --- Shutdown handler ---
def shutdown():
    print("🔻 Shutting down, releasing servos...")
    for ch in servo_angles:
        pwm.setServoPulse(ch, 0)
        time.sleep(.25)

atexit.register(shutdown)