import socket, time, pygame

UDP_IP, UDP_PORT = "192.168.1.158", 5005
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

pygame.init()
pygame.joystick.init()
js = pygame.joystick.Joystick(0); js.init()

def axis_to_angle(v, invert=False):
    if invert: v = -v
    return int(round((v + 1) / 2 * 180))  # maps -1..1 → 0..180

while True:
    pygame.event.pump()
    lx = js.get_axis(0)  # Left stick X
    ly = js.get_axis(1)  # Left stick Y
    lt = js.get_axis(4)  # Left Trigger: 1 (idle) → -1 (pressed)

    lt_mapped = (lt + 1) / 2  # now 0 (idle) → 1 (pressed)
    ang0 = axis_to_angle(lx)
    ang1 = axis_to_angle(ly, invert=True)
    ang2 = int(round(lt_mapped * 180))  # knee angle

    msg = f"4,{ang0},5,{ang1},6,{ang2}".encode()
    sock.sendto(msg, (UDP_IP, UDP_PORT))
    print(msg)

    time.sleep(0.02)
