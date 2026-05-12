"""
Legacy standalone animation helper.

The project now embeds the animation inside the main Tkinter UI (`ui.py`).
This file is kept for reference / optional standalone use.
"""

from constants import SimulationParams


def animate(params: SimulationParams | None = None):
    # Import heavy deps only if someone explicitly runs this.
    import matplotlib.pyplot as plt
    from matplotlib.animation import FuncAnimation
    from matplotlib.patches import Circle, Rectangle, Arc

    from simulator import simulate

    params = params or SimulationParams()
    data = simulate(params)

    fig, ax = plt.subplots(figsize=(6, 6))

    ax.set_xlim(-30, 30)
    ax.set_ylim(0, params.h0)
    ax.set_xlabel("x (m)")
    ax.set_ylabel("height y (m)")

    # Fix distortion
    ax.set_aspect("equal", adjustable="box")

    head = Circle((0, params.h0), 2, color="black")
    body = Rectangle((-1.5, params.h0 - 8), 3, 6, color="black")


    line_left, = ax.plot([], [], linewidth=1)
    line_right, = ax.plot([], [], linewidth=1)

    ax.add_patch(head)
    ax.add_patch(body)
    ax.add_patch(canopy)

    canopy.set_visible(False)
    line_left.set_visible(False)
    line_right.set_visible(False)

    def update(frame):
        x = data[frame, 1]
        y = data[frame, 2]

        head.center = (x, y)
        body.set_xy((x - 1.5, y - 8))

        if y <= params.h_open:
            canopy.center = (x, y + 10)
            canopy.set_visible(True)

            line_left.set_data([x - 10, x - 1], [y + 6, y])
            line_right.set_data([x + 10, x + 1], [y + 6, y])

            line_left.set_visible(True)
            line_right.set_visible(True)
        else:
            canopy.set_visible(False)
            line_left.set_visible(False)
            line_right.set_visible(False)

        return head, body, canopy, line_left, line_right

    FuncAnimation(fig, update, frames=len(data), interval=20, blit=True)
    plt.show()


if __name__ == "__main__":
    animate()