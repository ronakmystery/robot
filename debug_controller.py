import pygame, time, sys

pygame.init()
pygame.joystick.init()

if pygame.joystick.get_count() == 0:
    print("No controller found!")
    exit()

joystick = pygame.joystick.Joystick(0)
joystick.init()
print(f"Connected to {joystick.get_name()}")

last_state = None
while True:
    pygame.event.get()

    axes = tuple(round(joystick.get_axis(i), 2) for i in range(joystick.get_numaxes()))
    buttons = tuple(joystick.get_button(i) for i in range(joystick.get_numbuttons()))
    hats = tuple(joystick.get_hat(i) for i in range(joystick.get_numhats()))
    state = (axes, buttons, hats)

    # ✅ Only redraw when something changes
    if state != last_state:
        sys.stdout.write("\033c")  # fast clear
        print("Axes:", axes)
        print("Buttons:", buttons)
        print("Hats:", hats)
        print("-" * 40)
        last_state = state

    time.sleep(0.1)  # 50 fps refresh
