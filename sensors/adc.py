from smbus2 import SMBus
import time

I2C_BUS = 1
ADS1115_ADDR = 0x48
REG_CONVERT = 0x00
REG_CONFIG  = 0x01

# Single-shot, A0, ±4.096V, 128 SPS
CONFIG = 0x8483  

def read_adc(channel=0):
    with SMBus(I2C_BUS) as bus:
        # select channel (A0=0x4000, A1=0x5000, etc.)
        mux = 0x4000 + (channel << 12)
        config = (CONFIG & 0x8FFF) | mux

        # start conversion
        bus.write_i2c_block_data(ADS1115_ADDR, REG_CONFIG,
                                 [(config >> 8) & 0xFF, config & 0xFF])

        time.sleep(0.01)  # wait for conversion

        # read result
        hi, lo = bus.read_i2c_block_data(ADS1115_ADDR, REG_CONVERT, 2)
        raw = (hi << 8) | lo
        if raw > 0x7FFF:
            raw -= 0x10000

    volts = raw * (4.096 / 32768.0)  # scale for ±4.096 V
    return volts

# if __name__ == "__main__":
#     while True:
#         v = read_adc(0)   # read channel A0
#         print(f"Voltage: {v:.3f} V")
#         time.sleep(0.1)
