import smbus, time, math

# I2C address for MPU-9255 / MPU-6050 family
ADDR = 0x68
PWR_MGMT_1   = 0x6B
ACCEL_XOUT_H = 0x3B
GYRO_XOUT_H  = 0x43
WHO_AM_I     = 0x75

bus = smbus.SMBus(1)

def init_imu():
    try:
        bus.write_byte_data(ADDR, PWR_MGMT_1, 0)  # Wake up
        time.sleep(0.1)
        whoami = bus.read_byte_data(ADDR, WHO_AM_I)
        print(f"✅ IMU init OK, WHO_AM_I=0x{whoami:02X}")
    except OSError:
        print("❌ IMU not responding. Check wiring/power.")

def read_word(reg, retries=3, delay=0.01):
    for i in range(retries):
        try:
            high = bus.read_byte_data(ADDR, reg)
            low  = bus.read_byte_data(ADDR, reg+1)
            val = (high << 8) | low
            return val-65536 if val & 0x8000 else val
        except OSError as e:
            if i == retries - 1:
                raise
            time.sleep(delay)

def get_accel_gyro():
    ax = read_word(ACCEL_XOUT_H)   / 16384.0
    ay = read_word(ACCEL_XOUT_H+2) / 16384.0
    az = read_word(ACCEL_XOUT_H+4) / 16384.0
    gx = read_word(GYRO_XOUT_H)    / 131.0
    gy = read_word(GYRO_XOUT_H+2)  / 131.0
    gz = read_word(GYRO_XOUT_H+4)  / 131.0
    return ax, ay, az, gx, gy, gz

def accel_to_angle(ax, ay, az, flipped=False):
    if flipped:
        ax, ay, az = -ax, -ay, -az
    roll  = math.degrees(math.atan2(ay, az))
    pitch = math.degrees(math.atan2(-ax, math.sqrt(ay*ay + az*az)))
    return roll, pitch

def get_roll_pitch_angles(alpha=0.98):
    global roll, pitch, last_time
    try:
        ax, ay, az, gx, gy, gz = get_accel_gyro()
    except OSError:
        print("⚠️ IMU read failed → keeping last roll/pitch")
        return roll, pitch

    accel_roll, accel_pitch = accel_to_angle(ax, ay, az, flipped=True)
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

def reset_imu():
    global roll, pitch, last_time
    roll, pitch = 0.0, 0.0
    last_time = time.time()
    print("🔄 IMU reset: roll and pitch set to 0")

# Initialize filter
roll, pitch = 0.0, 0.0
last_time = time.time()

# Init hardware
init_imu()
