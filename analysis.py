import numpy as np
from constants import SimulationParams


def impact_velocity(data, ground_y=0.0):
    """Find the velocity at the moment of ground impact."""
    if len(data) == 0:
        return 0.0, 0.0
    # Find the first index where y <= ground_y
    hits = np.where(data[:, 2] <= ground_y)[0]
    if len(hits) > 0:
        idx = hits[0]
    else:
        idx = -1
    return data[idx, 3], data[idx, 4]


def final_speed(data, ground_y=0.0):
    vx, vy = impact_velocity(data, ground_y)
    return np.sqrt(vx**2 + vy**2)


def safe_landing(data, params: SimulationParams | None = None, ground_y=0.0):
    if len(data) == 0:
        return False
    params = params or SimulationParams()
    return final_speed(data, ground_y=ground_y) <= params.v_safe
