import socket, threading, time
from init import set_servo_angle, servo_angles

UDP_IP   = "0.0.0.0"
UDP_PORT = 5005

# Desired targets for servos 0,1,2
TARGETS  = {4: 90, 5: 90, 6: 90}

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.bind((UDP_IP, UDP_PORT))

def servo_worker(ch, speed=5, hz=60):
    """Continuously ease servo toward its target."""
    period = 1.0 / hz
    while True:
        cur = servo_angles.get(ch, 90)
        tgt = TARGETS[ch]
        if cur != tgt:
            step = max(1, abs(tgt - cur) // speed)
            if cur < tgt:
                cur += step
            else:
                cur -= step
            set_servo_angle(ch, cur)
        time.sleep(period)

# Start one worker per servo
for ch in TARGETS:
    threading.Thread(target=servo_worker, args=(ch,), daemon=True).start()

print(f"UDP server listening on {UDP_IP}:{UDP_PORT}")

while True:
    data, addr = sock.recvfrom(64)
    try:
        parts = list(map(int, data.decode().split(",")))
        # Expected format: "0,ang0,1,ang1,2,ang2"
        for i in range(0, len(parts), 2):
            ch, ang = parts[i], parts[i+1]
            if ch in TARGETS:
                TARGETS[ch] = ang
        print("Targets:", TARGETS)
    except Exception as e:
        print("Bad packet:", e)
