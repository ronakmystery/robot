import pygame, time

pygame.init()
pygame.joystick.init()

if pygame.joystick.get_count() == 0:
    print("No controller found!")
    exit()

joystick = pygame.joystick.Joystick(0)
joystick.init()
print(f"Connected to {joystick.get_name()}")

while True:
    pygame.event.pump()

    # Axes
    axes = [joystick.get_axis(i) for i in range(joystick.get_numaxes())]
    print("Axes:", ["{:.2f}".format(a) for a in axes])

    # Buttons
    buttons = [joystick.get_button(i) for i in range(joystick.get_numbuttons())]
    print("Buttons:", buttons)

    # Hats (D-pad)
    hats = [joystick.get_hat(i) for i in range(joystick.get_numhats())]
    print("Hats:", hats)

    print("-" * 40)
    time.sleep(.5)
