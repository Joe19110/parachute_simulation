"""
Legacy standalone plotting helper.

The project now embeds plots inside the main Tkinter UI (`ui.py`).
This file is kept for reference / optional standalone use.
"""

from constants import SimulationParams


def show_plots(params: SimulationParams | None = None):
    import matplotlib.pyplot as plt
    import numpy as np

    from simulator import simulate

    params = params or SimulationParams()
    data = simulate(params)

    time = data[:, 0]
    height = data[:, 2]
    speed = np.sqrt(data[:, 3] ** 2 + data[:, 4] ** 2)

    plt.figure()
    plt.plot(time, speed, label="Speed")
    plt.axhline(params.v_safe, color="green", linestyle="--", label="Safe limit")
    plt.xlabel("Time (s)")
    plt.ylabel("Speed (m/s)")
    plt.legend()
    plt.tight_layout()

    plt.figure()
    plt.plot(time, height, label="Height")
    plt.axhline(params.h_open, color="orange", linestyle="--", label="Deploy height")
    plt.xlabel("Time (s)")
    plt.ylabel("Height (m)")
    plt.legend()
    plt.tight_layout()

    plt.show()


if __name__ == "__main__":
    show_plots()
