import smbus, time, math

# I2C address for MPU-9255 / MPU-6050 family
ADDR = 0x68
PWR_MGMT_1   = 0x6B
ACCEL_XOUT_H = 0x3B
GYRO_XOUT_H  = 0x43

bus = smbus.SMBus(1)
bus.write_byte_data(ADDR, PWR_MGMT_1, 0)  # Wake up

def read_word(reg, retries=3, delay=0.01):
    for _ in range(retries):
        try:
            high = bus.read_byte_data(ADDR, reg)
            low  = bus.read_byte_data(ADDR, reg+1)
            val = (high << 8) | low
            return val-65536 if val & 0x8000 else val
        except OSError:
            time.sleep(delay)
    raise

def get_accel_gyro():
    ax = read_word(ACCEL_XOUT_H)   / 16384.0
    ay = read_word(ACCEL_XOUT_H+2) / 16384.0
    az = read_word(ACCEL_XOUT_H+4) / 16384.0
    gx = read_word(GYRO_XOUT_H)    / 131.0
    gy = read_word(GYRO_XOUT_H+2)  / 131.0
    gz = read_word(GYRO_XOUT_H+4)  / 131.0
    return ax, ay, az, gx, gy, gz

def accel_to_angle(ax, ay, az):
    roll  = math.degrees(math.atan2(ay, az))
    pitch = math.degrees(math.atan2(-ax, math.sqrt(ay*ay + az*az)))
    return roll, pitch



def get_roll_pitch_angles(alpha=0.98):
    ax, ay, az, gx, gy, gz = get_accel_gyro()
    accel_roll, accel_pitch = accel_to_angle(ax, ay, az)

    global roll, pitch, last_time
    now = time.time()
    dt = now - last_time
    last_time = now

    # Gyro integration
    gyro_roll  = roll  + gx * dt
    gyro_pitch = pitch + gy * dt

    # Complementary filter
    roll  = alpha * gyro_roll  + (1 - alpha) * accel_roll
    pitch = alpha * gyro_pitch + (1 - alpha) * accel_pitch

    if abs(roll) < 1: roll = 0.0
    if abs(pitch) < 1: pitch = 0.0
    return roll, pitch


# Initialize filter
roll, pitch = 0.0, 0.0
last_time = time.time()
   