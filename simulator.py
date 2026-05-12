import numpy as np
from constants import SimulationParams
from physics import acceleration


def simulate(params: SimulationParams | None = None):
    """Run a 2D parachute simulation and return history as ndarray.

    Columns: time, x, y, vx, vy.
    """
    params = params or SimulationParams()

    t = 0.0
    x, y = params.x0, params.h0
    vx, vy = params.vx0, params.vy0

    history = []

    while y > 0 and t < params.t_max:
        ax, ay = acceleration(vx, vy, y, params)

        vx += ax * params.dt
        vy += ay * params.dt

        x += vx * params.dt
        # y is altitude (positive upward). Gravity is negative, so vy becomes negative while falling.
        y += vy * params.dt

        history.append([t, x, y, vx, vy])
        t += params.dt

    return np.array(history)
