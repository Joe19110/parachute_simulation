import numpy as np
from constants import SimulationParams


def drag_force(vx_rel, vy_rel, Cd, A, rho):
    """Compute drag force using relative velocity to air."""
    v = np.sqrt(vx_rel**2 + vy_rel**2)
    if v == 0:
        return 0.0, 0.0
    F = 0.5 * rho * Cd * A * v**2
    Fx = -F * vx_rel / v
    Fy = -F * vy_rel / v
    return Fx, Fy


def acceleration(vx, vy, y, params: SimulationParams):
    """Acceleration from drag + gravity at current state."""
    if y > params.h_open:
        Cd, A = params.Cd_free, params.A_free
    else:
        Cd, A = params.Cd_para, params.A_para

    # Relative velocity to air considering wind
    vx_rel = vx - params.wind_speed
    vy_rel = vy

    Fx, Fy = drag_force(vx_rel, vy_rel, Cd, A, params.rho)
    ax = Fx / params.m
    ay = Fy / params.m - params.g
    return ax, ay

