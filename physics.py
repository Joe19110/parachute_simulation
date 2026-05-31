import numpy as np
from constants import SimulationParams


def drag_force_3d(vx_rel, vy_rel, vz_rel, Cd, A, rho):
    """Compute 3-axis drag force using relative velocity to air."""
    v = np.sqrt(vx_rel**2 + vy_rel**2 + vz_rel**2)
    if v == 0:
        return 0.0, 0.0, 0.0
    F = 0.5 * rho * Cd * A * v**2
    Fx = -F * vx_rel / v
    Fy = -F * vy_rel / v
    Fz = -F * vz_rel / v
    return Fx, Fy, Fz


def glide_force_3d(vx, vy, vz, vx_rel, glide_ratio, glide_az, m, rho, Cd, A):
    """
    Compute forward lift force for ram-air (gliding) parachutes.

    A ram-air chute acts like a wing: it generates forward thrust proportional
    to its glide ratio (L/D). The lift is applied in the horizontal plane in
    the direction of horizontal motion relative to the air, and counters some
    of the descent rate.

    Returns (Flift_x, Flift_y, Flift_z) in Newtons.
    """
    if glide_ratio == 0.0 and glide_az == 0.0:
        return 0.0, 0.0, 0.0

    # Weight component (the lift that must be generated to achieve glide_ratio)
    weight = m * 9.81
    # Horizontal speed squared
    vh_sq = vx**2 + vz**2
    vh = np.sqrt(vh_sq)

    if vh < 0.01:
        return 0.0, 0.0, 0.0

    # A ram-air chute self-propels forward at a trim speed; model as a constant
    # forward force F_fwd = weight / glide_ratio projected into the heading direction.
    F_fwd = weight / max(0.01, glide_ratio) if glide_ratio > 0 else 0.0

    Fx_glide = F_fwd * (vx / vh)
    Fz_glide = F_fwd * (vz / vh)

    # Vertical component: glide generates upward lift that offsets some drag
    # It is already implicitly handled by forward momentum, but we add a small
    # vertical lift term proportional to glide efficiency.
    Fy_glide = weight * (glide_ratio / max(1.0, glide_ratio + 1))

    return Fx_glide, Fy_glide, Fz_glide


def acceleration(vx, vy, vz, y, params: SimulationParams):
    """Acceleration from drag + glide + gravity at current state (3D)."""
    if y > params.h_open:
        Cd, A = params.Cd_free, params.A_free
    else:
        Cd, A = params.Cd_para, params.A_para

    if getattr(params, 'wind_shear', False):
        scale = max(0.0, min(1.0, y / max(1.0, params.h0)))
        wx = params.wind_x * scale
        wz = params.wind_z * scale
    else:
        wx = params.wind_x
        wz = params.wind_z

    # Relative velocity to air (x and z winds only; no vertical wind)
    vx_rel = vx - wx
    vy_rel = vy
    vz_rel = vz - wz

    Fx, Fy, Fz = drag_force_3d(vx_rel, vy_rel, vz_rel, Cd, A, params.rho)

    # Glide force (ram-air only, below deployment height)
    if y <= params.h_open:
        Gx, Gy, Gz = glide_force_3d(vx, vy, vz, vx_rel,
                                      params.glide_ratio, params.glide_az,
                                      params.m, params.rho, Cd, A)
    else:
        Gx, Gy, Gz = 0.0, 0.0, 0.0

    ax = (Fx + Gx) / params.m
    ay = (Fy + Gy) / params.m - params.g
    az = (Fz + Gz) / params.m
    return ax, ay, az
