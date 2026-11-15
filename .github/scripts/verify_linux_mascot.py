"""Verify the released mascot shows the desktop through its empty areas."""

import os
import time

from PIL import ImageGrab


BACKDROP = (38, 52, 73)  # Matches xsetroot in the Ubuntu build job.
REMINDER_BLUE = (2, 132, 199)
WIDTH, HEIGHT = 340, 450


def main():
    deadline = time.monotonic() + 15
    while time.monotonic() < deadline:
        desktop = ImageGrab.grab(xdisplay=os.environ["DISPLAY"]).convert("RGB")
        left = (desktop.width - WIDTH) // 2
        top = (desktop.height - HEIGHT) // 2
        overlay = desktop.crop((left, top, left + WIDTH, top + HEIGHT))

        # The controls use this fill and only appear after the walk and drink.
        colors = {color: count for count, color in overlay.getcolors(WIDTH * HEIGHT)}
        if colors.get(REMINDER_BLUE, 0) > 100:
            margin = 16
            desktop.crop((left - margin, top - margin, left + WIDTH + margin,
                          top + HEIGHT + margin)).save("ubuntu-mascot.png")
            corners = ((0, 0), (WIDTH - 1, 0), (0, HEIGHT - 1), (WIDTH - 1, HEIGHT - 1))
            assert all(overlay.getpixel(point) == BACKDROP for point in corners), (
                "Mascot overlay corners obscure the desktop"
            )
            assert colors.get(BACKDROP, 0) > WIDTH * HEIGHT // 2, (
                "The desktop is not visible around the mascot"
            )
            return
        time.sleep(0.1)
    raise AssertionError("Mascot controls did not appear on the Ubuntu desktop")


if __name__ == "__main__":
    main()
