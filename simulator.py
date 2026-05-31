import numpy as np
from constants import SimulationParams
from physics import acceleration


def simulate(params: SimulationParams | None = None):
    """Run a 3D parachute simulation and return history as ndarray.

    Columns: time, x, y, z, vx, vy, vz
    (y is altitude, positive upward; x/z are horizontal axes)
    """
    params = params or SimulationParams()

    t = 0.0
    x, y, z = params.x0, params.h0, params.z0
    vx, vy, vz = params.vx0, params.vy0, params.vz0

    history = []

    while y > 0 and t < params.t_max:
        ax, ay, az = acceleration(vx, vy, vz, y, params)

        vx += ax * params.dt
        vy += ay * params.dt
        vz += az * params.dt

        x += vx * params.dt
        y += vy * params.dt
        z += vz * params.dt

        history.append([t, x, y, z, vx, vy, vz])
        t += params.dt

    return np.array(history)


def compute_drift(params: SimulationParams):
    """Simulate and return the total horizontal drift (dx, dz) from origin."""
    data = simulate(params)
    if len(data) == 0:
        return 0.0, 0.0
    # Find landing index
    hits = np.where(data[:, 2] <= 0)[0]
    idx = hits[0] if len(hits) else -1
    dx = float(data[idx, 1]) - params.x0
    dz = float(data[idx, 3]) - params.z0
    return dx, dz


def compute_jump_point(params: SimulationParams):
    """Return the (x0, z0) where a diver should jump to land at (target_x, target_z)."""
    # Simulate from origin to get drift
    test_params = SimulationParams(**{k: getattr(params, k) for k in params.__dataclass_fields__})
    test_params.x0 = 0.0
    test_params.z0 = 0.0
    dx, dz = compute_drift(test_params)
    jump_x = params.target_x - dx
    jump_z = params.target_z - dz
    return jump_x, jump_z
