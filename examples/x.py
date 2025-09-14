#!/usr/bin/python3
import pygame
import requests
import time
import sys

# ---------------- Config ----------------
PI_IP = "http://10.236.55.155:8080/cmd"
UPDATE_RATE = 0.05   # 20Hz


def send_cmd(cmd: str):
    try:
        requests.get(PI_IP, params={"c": cmd}, timeout=0.2)
        print(f"➡️ Sent: {cmd}")
    except requests.exceptions.RequestException as e:
        print(f"⚠️ Failed to send '{cmd}': {e}")


def get_joystick():
    pygame.init()
    pygame.joystick.init()
    if pygame.joystick.get_count() == 0:
        print("❌ No controller found!")
        sys.exit(1)
    js = pygame.joystick.Joystick(0)
    js.init()
    print("🎮 Using:", js.get_name())
    return js


def main():
    js = get_joystick()
    last_lcmd = last_rcmd = None

    while True:
        pygame.event.pump()

        # D-Pad state
        hat_x, hat_y = js.get_hat(0)

        # Triggers (-1..1 → 0..1)
        lt = (js.get_axis(5) + 1) / 2
        rt = (js.get_axis(4) + 1) / 2

        # Scale factors (down to 30% max speed)
        left_factor = 1.0 - lt * 0.7
        right_factor = 1.0 - rt * 0.7

        lcmd = rcmd = None

        if hat_y == 1:  # DPad Up = backward (inverted)
            lcmd = f"lt{int(100 * left_factor)}b"
            rcmd = f"rt{int(100 * right_factor)}b"

        elif hat_y == -1:  # DPad Down = forward (inverted)
            lcmd = f"lt{int(100 * left_factor)}f"
            rcmd = f"rt{int(100 * right_factor)}f"

        elif hat_x == -1:  # Spin Left
            lcmd = f"lt{int(100 * left_factor)}b"
            rcmd = f"rt{int(100 * right_factor)}f"

        elif hat_x == 1:  # Spin Right
            lcmd = f"lt{int(100 * left_factor)}f"
            rcmd = f"rt{int(100 * right_factor)}b"

        # Send if changed
        if lcmd != last_lcmd:
            if lcmd: send_cmd(lcmd)
            last_lcmd = lcmd

        if rcmd != last_rcmd:
            if rcmd: send_cmd(rcmd)
            last_rcmd = rcmd

        # Neutral (no DPad press)
        if hat_x == 0 and hat_y == 0:
            send_cmd("x")
            last_lcmd = last_rcmd = None

        time.sleep(UPDATE_RATE)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n🛑 Exiting...")
        sys.exit(0)
