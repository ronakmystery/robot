from threading import Thread, Lock
import time
import json
import os
import atexit

from flask import Flask, render_template, jsonify, request, send_file

import smbus
import math


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



def angle_to_pulse(angle):
    return int(500 + (angle / 180.0) * 2000)

def set_servo_angle(channel, angle):
    angle = max(0, min(180, angle))
    pulse = angle_to_pulse(angle)
    with servo_lock:
        pwm.setServoPulse(channel, pulse)
        servo_angles[channel] = angle



load_poses()
servos=[15,14,13,12,7,6,5,4]


pose=poses["x"]
for servo in pose:
    set_servo_angle(int(servo), int(pose[servo]))
time.sleep(1)



def apply_pose( pose,  batch_size=2):

    ch_items = list(pose.items())

    for i in range(0, len(ch_items), batch_size):
        batch = ch_items[i:i+batch_size]
        threads = []

        for ch_str, angle in batch:
            ch = int(ch_str)
            t = Thread(target=set_servo_angle, args=(ch, angle))
            t.start()
            threads.append(t)

        for t in threads:
            t.join()



def move_two_servos(ch1, angle1, ch2, angle2):
    def move(ch, angle):
        set_servo_angle(ch, angle)

    t1 = Thread(target=move, args=(ch1, angle1))
    t2 = Thread(target=move, args=(ch2, angle2))

    t1.start()
    t2.start()

    t1.join()
    t2.join()


clockwise = True  # direction of rotation
# Simulate circular motion
sleep=.1
for i in range(300):  # number of steps
    t=i/20
    if clockwise:
        t = -t

    if i>100:
        sleep=.01

    if i>200:
        sleep=.001

    r = 50  # radius (max deflection from center)
    center = 90  # center angle

    x = center + r * math.cos(t)  # servo 1
    y = center + r * math.sin(t)  # servo 2


    print(x, y)

    move_two_servos(12, int(x), 7, int(y))
    time.sleep(sleep)



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




# # --- Start Server ---
# if __name__ == "__main__":
#     app.run(host="0.0.0.0", port=5000, debug=False)


# --- Shutdown handler ---
def shutdown():
    print("🔻 Shutting down, releasing servos...")
    for ch in servo_angles:
        pwm.setServoPulse(ch, 0)
        time.sleep(.1)

atexit.register(shutdown)