import smbus
import time
import math

# I2C address for MPU-9255 / GY-510
ADDR = 0x68
PWR_MGMT_1 = 0x6B
ACCEL_XOUT_H = 0x3B
GYRO_XOUT_H = 0x43

bus = smbus.SMBus(1)

# Wake up the MPU
bus.write_byte_data(ADDR, PWR_MGMT_1, 0)

def read_word(reg):
    high = bus.read_byte_data(ADDR, reg)
    low = bus.read_byte_data(ADDR, reg+1)
    val = (high << 8) + low
    if val >= 0x8000:
        val = -((65535 - val) + 1)
    return val

def get_accel_gyro():
    ax = read_word(ACCEL_XOUT_H) / 16384.0  # g
    ay = read_word(ACCEL_XOUT_H+2) / 16384.0
    az = read_word(ACCEL_XOUT_H+4) / 16384.0
    gx = read_word(GYRO_XOUT_H) / 131.0     # deg/s
    gy = read_word(GYRO_XOUT_H+2) / 131.0
    gz = read_word(GYRO_XOUT_H+4) / 131.0
    return ax, ay, az, gx, gy, gz

def get_roll_pitch(ax, ay, az):
    roll  = math.degrees(math.atan2(ay, az))
    pitch = math.degrees(math.atan2(-ax, math.sqrt(ay*ay + az*az)))
    return roll, pitch

print("Press Ctrl+C to stop")
while True:
    ax, ay, az, gx, gy, gz = get_accel_gyro()
    roll, pitch = get_roll_pitch(ax, ay, az)
    print(f"Roll: {roll:6.2f}°, Pitch: {pitch:6.2f}°, "
          f"GyroX: {gx:7.2f}, GyroY: {gy:7.2f}, GyroZ: {gz:7.2f}")
    time.sleep(0.1)  # ~20Hz


