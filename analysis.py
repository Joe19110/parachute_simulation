import numpy as np
from constants import SimulationParams


# ── Column indices for 3D data array ─────────────────────────────────────────
COL_T  = 0
COL_X  = 1
COL_Y  = 2
COL_Z  = 3
COL_VX = 4
COL_VY = 5
COL_VZ = 6


def _landing_index(data, ground_y=0.0):
    """Return the first index where altitude <= ground_y."""
    if len(data) == 0:
        return -1
    hits = np.where(data[:, COL_Y] <= ground_y)[0]
    return int(hits[0]) if len(hits) else -1


def impact_velocity(data, ground_y=0.0):
    """3D velocity (vx, vy, vz) at ground impact."""
    if len(data) == 0:
        return 0.0, 0.0, 0.0
    idx = _landing_index(data, ground_y)
    return float(data[idx, COL_VX]), float(data[idx, COL_VY]), float(data[idx, COL_VZ])


def final_speed(data, ground_y=0.0):
    """Magnitude of velocity at ground impact."""
    vx, vy, vz = impact_velocity(data, ground_y)
    return np.sqrt(vx**2 + vy**2 + vz**2)


def safe_landing(data, params: SimulationParams | None = None, ground_y=0.0):
    if len(data) == 0:
        return False
    params = params or SimulationParams()
    return final_speed(data, ground_y=ground_y) <= params.v_safe


def landing_position(data, ground_y=0.0):
    """Return (x, z) landing position."""
    if len(data) == 0:
        return 0.0, 0.0
    idx = _landing_index(data, ground_y)
    return float(data[idx, COL_X]), float(data[idx, COL_Z])


def flight_time(data, ground_y=0.0):
    """Total flight duration until ground impact."""
    if len(data) == 0:
        return 0.0
    idx = _landing_index(data, ground_y)
    return float(data[idx, COL_T])


def max_speed(data):
    """Maximum speed during the entire flight."""
    if len(data) == 0:
        return 0.0
    speeds = np.sqrt(data[:, COL_VX]**2 + data[:, COL_VY]**2 + data[:, COL_VZ]**2)
    return float(speeds.max())
