from smbus2 import SMBus
import time

I2C_BUS = 1
ADS1115_ADDR = 0x48  # change if ADDR strapped differently

# Registers
REG_CONVERT = 0x00
REG_CONFIG  = 0x01

# Bits / options
OS_SINGLE     = 0x8000
MODE_SINGLE   = 0x0100
DR_128SPS     = 0x0080
COMP_QUE_DIS  = 0x0003

# Single-ended MUX for A0..A3
MUX = {0: 0x4000, 1: 0x5000, 2: 0x6000, 3: 0x7000}

# PGA full-scale codes (±FS) and their FS volts (per datasheet)
PGA_CODES = {
    6.144: 0x0000,  # ±6.144 V  (only safe if VDD=5V and input <= VDD)
    4.096: 0x0200,  # ±4.096 V
    2.048: 0x0400,  # ±2.048 V
    1.024: 0x0600,  # ±1.024 V
    0.512: 0x0800,  # ±0.512 V
    0.256: 0x0A00,  # ±0.256 V
}

# === set this to your ADS supply ===
VDD_VOLTS = 3.3   # 3.3 if powered from Pi 3V3, 5.0 if from 5V

def read_adc(channel=0, fs_volts=4.096, vdd=VDD_VOLTS, sps_delay=0.008):
    """
    Single-ended read on channel 0..3
    fs_volts: choose one of PGA_CODES keys (6.144, 4.096, 2.048, 1.024, 0.512, 0.256)
    vdd: ADS1115 supply voltage (limits real measurable range)
    """
    if channel not in MUX:
        raise ValueError("channel must be 0..3")
    if fs_volts not in PGA_CODES:
        raise ValueError(f"fs_volts must be one of {list(PGA_CODES.keys())}")

    config = (
        OS_SINGLE |
        MUX[channel] |
        PGA_CODES[fs_volts] |
        MODE_SINGLE |
        DR_128SPS |
        COMP_QUE_DIS
    )

    with SMBus(I2C_BUS) as bus:
        # start single conversion
        bus.write_i2c_block_data(ADS1115_ADDR, REG_CONFIG,
                                 [(config >> 8) & 0xFF, config & 0xFF])

        time.sleep(sps_delay)  # wait for conversion (8ms @128SPS)

        # read result
        hi, lo = bus.read_i2c_block_data(ADS1115_ADDR, REG_CONVERT, 2)
        raw = (hi << 8) | lo
        if raw > 0x7FFF:
            raw -= 0x10000

    # convert to volts using selected full-scale
    volts = raw * (fs_volts / 32768.0)

    # hard physical limit: inputs cannot exceed VDD
    # when powered at 3.3V, you’ll never see > ~VDD regardless of PGA
    if volts > vdd:
        volts = vdd
    if volts < -vdd:
        volts = -vdd

    # optional gentle warning if we’re near PGA clip
    if abs(raw) > 0.9 * 32768:
        # print("Warning: near ADC full-scale; consider higher FS (lower gain).")
        pass

    return raw, volts

if __name__ == "__main__":
    # Example 1: 3.3V supply, want full 0..3.3V range → use fs_volts=4.096 (safe headroom)
    while True:
        raw, v = read_adc(channel=0, fs_volts=4.096, vdd=3.3)
        print(f"A0  raw={raw:6d}  V={v:0.4f}")
        time.sleep(0.1)
