"""
ui/params.py
------------
Helpers for reading widget state and converting it into a SimulationParams.
"""
from constants import SimulationParams, PARACHUTE_SHAPES


def _fval(entry, fallback):
    """Safely parse a float from a ttk.Entry widget."""
    try:
        return float(entry.get())
    except (ValueError, AttributeError):
        return fallback


def build_params_from_ui(
    sliders,
    adv_entries,
    drop_mode_var,
    vehicle_var,
    shape_var,
    target_entries,
    speed_entries,
    wind_shear_var,
    follow_cam_var,
):
    """Build a SimulationParams dataclass from the current UI widget state.

    Parameters
    ----------
    sliders       : dict[str, tk.DoubleVar]   – basic parameter sliders
    adv_entries   : dict[str, ttk.Entry]       – advanced Cd/Area overrides
    drop_mode_var : tk.StringVar               – selected drop mode
    vehicle_var   : tk.StringVar               – vehicle behaviour after drop
    shape_var     : tk.StringVar               – selected parachute shape key
    target_entries: dict[str, ttk.Entry]       – target X/Z landing coords
    speed_entries : dict[str, ttk.Entry]       – vehicle speed X/Z

    Returns
    -------
    SimulationParams
    """
    d = SimulationParams()

    # Parachute shape presets (overridable by adv_entries)
    shape_key = shape_var.get()
    cd_p, a_p, gr, gaz, _ = PARACHUTE_SHAPES.get(shape_key, PARACHUTE_SHAPES["Round"])
    m     = _fval(adv_entries["m"], 80.0)
    rho   = _fval(adv_entries["rho"], 1.225)
    cd_p  = _fval(adv_entries["Cd_para"], cd_p)
    a_p   = _fval(adv_entries["A_para"],  a_p)
    cd_fr = _fval(adv_entries["Cd_free"], d.Cd_free)
    a_fr  = _fval(adv_entries["A_free"],  d.A_free)

    vspx = _fval(speed_entries["vx"], d.vehicle_speed_x)
    vspz = _fval(speed_entries["vz"], d.vehicle_speed_z)
    tx   = _fval(target_entries["tx"], d.target_x)
    tz   = _fval(target_entries["tz"], d.target_z)
    c_sz_x = _fval(target_entries["cushion_size_x"], d.cushion_size_x)
    c_sz_z = _fval(target_entries["cushion_size_z"], d.cushion_size_z)

    p = SimulationParams(
        m                = m,
        rho              = rho,
        h0               = sliders["h0"].get(),
        h_open           = sliders["h_open"].get(),
        wind_x           = sliders["wind_x"].get(),
        wind_z           = sliders["wind_z"].get(),
        wind_speed       = sliders["wind_x"].get(),
        v_safe           = sliders["v_safe"].get(),
        Cd_free          = cd_fr,
        A_free           = a_fr,
        Cd_para          = cd_p,
        A_para           = a_p,
        glide_ratio      = gr,
        glide_az         = gaz,
        drop_mode        = drop_mode_var.get(),
        vehicle_behavior = vehicle_var.get(),
        vehicle_speed_x  = vspx,
        vehicle_speed_z  = vspz,
        parachute_shape  = shape_key,
        target_x         = tx,
        target_z         = tz,
        cushion_size_x   = c_sz_x,
        cushion_size_z   = c_sz_z,
        wind_shear       = wind_shear_var.get(),
        follow_cam       = follow_cam_var.get(),
    )

    # Set initial velocity from vehicle speed
    if p.drop_mode == "plane":
        p.vx0 = p.vehicle_speed_x
        p.vz0 = p.vehicle_speed_z
    elif p.drop_mode == "helicopter":
        p.vx0 = p.vehicle_speed_z   # lateral hover drift
        p.vz0 = 0.0

    return p
