"""
ui/panels.py
------------
Builds the scrollable left control panel.

Public API
~~~~~~~~~~
build_left_panel(left_inner) → dict of all widget variable references
"""
import tkinter as tk
from tkinter import ttk
from constants import SimulationParams, PARACHUTE_SHAPES
import theme as T


def build_left_panel(left_inner):
    """Create all left-panel sections and pack them into *left_inner*.

    Returns a flat dict with every widget variable needed by app.py:
        sliders, adv_entries, speed_entries, target_entries,
        drop_mode_var, vehicle_var, shape_var, cushion_enabled,
        rvars, anim_speed, jump_x_var, jump_z_var, btn_frame
    """
    defaults = SimulationParams()
    SPX = 6;  SPY = (0, 8);  IPX = 10;  IPY = 4
    row = 0

    # ── Drop mode ─────────────────────────────────────────────────────────
    row, drop_mode_var = _build_drop_mode(left_inner, row, IPX, IPY, SPX, SPY)

    # ── Vehicle behavior ───────────────────────────────────────────────────
    row, vehicle_var = _build_vehicle_behavior(left_inner, row, IPX, IPY, SPX, SPY)

    # ── Vehicle speed ──────────────────────────────────────────────────────
    row, speed_entries = _build_vehicle_speed(left_inner, row, IPX, SPX, SPY)

    # ── Parachute type + advanced overrides ───────────────────────────────
    row, shape_var, adv_entries = _build_parachute_section(
        left_inner, row, defaults, IPX, SPX, SPY)

    # ── Basic parameter sliders ────────────────────────────────────────────
    row, sliders = _build_sliders(left_inner, row, defaults, IPX, SPX, SPY)

    # ── Landing cushion + jump-point display ───────────────────────────────
    row, cushion_enabled, target_entries, jump_x_var, jump_z_var = _build_cushion(
        left_inner, row, IPX, SPX, SPY)

    # ── Results card ───────────────────────────────────────────────────────
    row, rvars = _build_results(left_inner, row, SPX, SPY)

    # ── Buttons (wired externally by app.py) ───────────────────────────────
    btn_frame = ttk.Frame(left_inner)
    btn_frame.grid(row=row, column=0, sticky="ew", padx=SPX, pady=(4, 8))
    for col in range(3):
        btn_frame.columnconfigure(col, weight=1)
    row += 1

    # ── Animation speed & Theme ────────────────────────────────────────────
    row, anim_speed, theme_var, wind_shear_var, follow_cam_var = _build_anim_speed_and_theme(left_inner, row, IPX, SPX)

    return {
        "sliders":         sliders,
        "adv_entries":     adv_entries,
        "speed_entries":   speed_entries,
        "target_entries":  target_entries,
        "drop_mode_var":   drop_mode_var,
        "vehicle_var":     vehicle_var,
        "shape_var":       shape_var,
        "cushion_enabled": cushion_enabled,
        "rvars":           rvars,
        "anim_speed":      anim_speed,
        "jump_x_var":      jump_x_var,
        "jump_z_var":      jump_z_var,
        "btn_frame":       btn_frame,
        "theme_var":       theme_var,
        "wind_shear_var":  wind_shear_var,
        "follow_cam_var":  follow_cam_var,
    }


# ── Section builders (private) ────────────────────────────────────────────────

def _build_drop_mode(parent, row, IPX, IPY, SPX, SPY):
    f = ttk.LabelFrame(parent, text="  DROP MODE  ", padding=(IPX, 6))
    f.grid(row=row, column=0, sticky="ew", padx=SPX, pady=SPY)
    f.columnconfigure(0, weight=1)
    var = tk.StringVar(value="freefall")
    for i, (txt, val) in enumerate([
        ("Freefall",        "freefall"),
        ("Plane Drop",      "plane"),
        ("Helicopter Drop", "helicopter"),
    ]):
        ttk.Radiobutton(f, text=txt, variable=var, value=val).grid(
            row=i, column=0, sticky="w", padx=4, pady=IPY)
    return row + 1, var


def _build_vehicle_behavior(parent, row, IPX, IPY, SPX, SPY):
    f = ttk.LabelFrame(parent, text="  VEHICLE AFTER DROP  ", padding=(IPX, 6))
    f.grid(row=row, column=0, sticky="ew", padx=SPX, pady=SPY)
    var = tk.StringVar(value="fly_away")
    ttk.Radiobutton(f, text="Fly Away",      variable=var, value="fly_away").grid(
        row=0, column=0, sticky="w", padx=4, pady=IPY)
    ttk.Radiobutton(f, text="Stay / Hover", variable=var, value="stay").grid(
        row=1, column=0, sticky="w", padx=4, pady=IPY)
    return row + 1, var


def _build_vehicle_speed(parent, row, IPX, SPX, SPY):
    f = ttk.LabelFrame(parent, text="  VEHICLE SPEED  ", padding=(IPX, 6))
    f.grid(row=row, column=0, sticky="ew", padx=SPX, pady=SPY)
    f.columnconfigure(0, weight=1); f.columnconfigure(1, weight=1)
    entries = {}
    for i, (lbl, key, default) in enumerate([
        ("Forward Speed X (m/s)", "vx", 50.0),
        ("Side Speed Z (m/s)",    "vz",  0.0),
    ]):
        ttk.Label(f, text=lbl, foreground=T.TEXT_SECONDARY,
                  font=("Segoe UI", 9)).grid(row=i, column=0, sticky="w",
                                            padx=(2, 8), pady=3)
        ent = ttk.Entry(f, width=10)
        ent.insert(0, str(default))
        ent.grid(row=i, column=1, sticky="ew", padx=2, pady=3)
        entries[key] = ent
    return row + 1, entries


def _build_parachute_section(parent, row, defaults, IPX, SPX, SPY):
    """Parachute type combobox + advanced Cd/Area entry overrides."""
    # Shape picker
    shape_f = ttk.LabelFrame(parent, text="  PARACHUTE TYPE  ", padding=(IPX, 6))
    shape_f.grid(row=row, column=0, sticky="ew", padx=SPX, pady=SPY)
    shape_f.columnconfigure(0, weight=1)
    row += 1

    shape_var  = tk.StringVar(value="Round")
    info_lbl   = ttk.Label(shape_f, text="", foreground=T.TEXT_SECONDARY,
                            font=("Segoe UI", 8), wraplength=230)
    shape_combo = ttk.Combobox(shape_f, textvariable=shape_var,
                                values=list(PARACHUTE_SHAPES.keys()),
                                state="readonly", width=20)
    shape_combo.grid(row=0, column=0, sticky="ew", padx=2, pady=(4, 2))
    info_lbl.grid(row=1, column=0, sticky="w", padx=4, pady=(0, 4))

    # Advanced overrides
    adv_f = ttk.LabelFrame(parent, text="  ADVANCED (override)  ", padding=(IPX, 6))
    adv_f.grid(row=row, column=0, sticky="ew", padx=SPX, pady=SPY)
    adv_f.columnconfigure(0, weight=1); adv_f.columnconfigure(1, weight=1)
    row += 1

    adv_entries = {}
    for i, (lbl, key) in enumerate([
        ("Payload Mass (kg)", "m"),
        ("Air Density (kg/m³)", "rho"),
        ("Cd (freefall)",    "Cd_free"),
        ("Area freefall m²", "A_free"),
        ("Cd (parachute)",   "Cd_para"),
        ("Area parachute m²","A_para"),
    ]):
        ttk.Label(adv_f, text=lbl, foreground=T.TEXT_SECONDARY,
                  font=("Segoe UI", 9)).grid(row=i, column=0, sticky="w",
                                            padx=(2, 8), pady=3)
        ent = ttk.Entry(adv_f, width=10)
        ent.insert(0, str(getattr(defaults, key)))
        ent.grid(row=i, column=1, sticky="ew", padx=2, pady=3)
        adv_entries[key] = ent

    # Wire shape selection → update info label + auto-fill Cd/Area
    def _on_shape_change(*_):
        key = shape_var.get()
        cd_p, a_p, gr, _, _ = PARACHUTE_SHAPES.get(key, PARACHUTE_SHAPES["Round"])
        for ek, val in (("Cd_para", cd_p), ("A_para", a_p)):
            adv_entries[ek].delete(0, tk.END)
            adv_entries[ek].insert(0, str(val))
        glide_txt = f"  Glide ratio: {gr:.1f}" if gr > 0 else "  No glide (drag-only)"
        info_lbl.config(text=f"Cd={cd_p}  Area={a_p}m²{glide_txt}")

    shape_combo.bind("<<ComboboxSelected>>", _on_shape_change)
    _on_shape_change()

    return row, shape_var, adv_entries


def _build_sliders(parent, row, defaults, IPX, SPX, SPY):
    f = ttk.LabelFrame(parent, text="  PARAMETERS  ", padding=(IPX, 6))
    f.grid(row=row, column=0, sticky="ew", padx=SPX, pady=SPY)
    f.columnconfigure(0, weight=1)

    defs = [
        ("Mass (kg)",          "m",       40,   150, defaults.m,      1  ),
        ("Start Height (m)",   "h0",     500, 10000, defaults.h0,    100 ),
        ("Deploy Height (m)",  "h_open", 100,  5000, defaults.h_open, 50 ),
        ("Wind Speed X (m/s)", "wind_x", -30,    30, defaults.wind_x, 0.5),
        ("Wind Speed Z (m/s)", "wind_z", -30,    30, defaults.wind_z, 0.5),
        ("Safe Landing (m/s)", "v_safe",   1,    15, defaults.v_safe, 0.5),
    ]
    sliders = {}
    for i, (lbl, key, lo, hi, val, res) in enumerate(defs):
        sliders[key] = _make_slider(f, i, lbl, key, lo, hi, val, res)

    return row + 1, sliders


def _make_slider(parent, row, label, key, lo, hi, default, res):
    """Create a labelled slider row and return its DoubleVar."""
    f = ttk.Frame(parent)
    f.grid(row=row, column=0, sticky="ew", padx=2, pady=4)
    f.columnconfigure(0, weight=1); f.columnconfigure(1, weight=0)

    ttk.Label(f, text=label, foreground=T.TEXT_SECONDARY,
              font=("Segoe UI", 9)).grid(row=0, column=0, sticky="w")
    val_lbl = ttk.Label(f, text=f"{default}", foreground=T.ACCENT_CYAN,
                        font=("Segoe UI", 9, "bold"))
    val_lbl.grid(row=0, column=1, sticky="e", padx=(8, 0))

    var = tk.DoubleVar(value=default)

    def _upd(v, lbl=val_lbl, r=res):
        v = float(v)
        lbl.config(text=f"{v:.1f}" if r < 1 else f"{int(v)}")

    sc = ttk.Scale(f, from_=lo, to=hi, orient="horizontal",
                   variable=var, command=_upd)
    sc.grid(row=1, column=0, columnspan=2, sticky="ew", pady=(2, 0))

    # Coloured wind direction hint
    if key in ("wind_x", "wind_z"):
        suffix = "X" if key == "wind_x" else "Z"

        def _wind_color(v, lbl=val_lbl, suf=suffix):
            v = float(v)
            lbl.config(
                foreground=(T.ACCENT_MAGENTA if v < 0
                            else T.ACCENT_ORANGE if v > 0
                            else T.ACCENT_CYAN),
                text=f"{v:.1f}  {'← ' + suf + '−' if v < 0 else '→ ' + suf + '+' if v > 0 else '—'}",
            )
        sc.config(command=_wind_color)
        _wind_color(default)

    return var


def _build_cushion(parent, row, IPX, SPX, SPY):
    f = ttk.LabelFrame(parent, text="  LANDING CUSHION  ", padding=(IPX, 6))
    f.grid(row=row, column=0, sticky="ew", padx=SPX, pady=SPY)
    f.columnconfigure(0, weight=1); f.columnconfigure(1, weight=1)

    enabled = tk.BooleanVar(value=False)
    ttk.Checkbutton(f, text="Enable Landing Cushion", variable=enabled,
                    style="TCheckbutton").grid(row=0, column=0, columnspan=2,
                                              sticky="w", pady=(0, 6))
    
    entries = {}
    for i, (lbl, key, default) in enumerate([
        ("Target X (m)", "tx", 0.0),
        ("Target Z (m)", "tz", 0.0),
        ("Size X (m)",   "cushion_size_x", 20.0),
        ("Size Z (m)",   "cushion_size_z", 20.0),
    ], start=1):
        ttk.Label(f, text=lbl, foreground=T.TEXT_SECONDARY,
                  font=("Segoe UI", 9)).grid(row=i, column=0, sticky="w",
                                            padx=(2, 8), pady=3)
        ent = ttk.Entry(f, width=10)
        ent.insert(0, str(default))
        ent.grid(row=i, column=1, sticky="ew", padx=2, pady=3)
        entries[key] = ent

    # Jump-point display card
    jf = tk.Frame(f, bg=T.BG_CARD, padx=8, pady=6)
    jf.grid(row=5, column=0, columnspan=2, sticky="ew", padx=2, pady=(6, 2))
    jf.columnconfigure(0, weight=1); jf.columnconfigure(1, weight=1)
    tk.Label(jf, text="Required Jump Point:", bg=T.BG_CARD, fg=T.ACCENT_YELLOW,
             font=("Segoe UI", 9, "bold")).grid(row=0, column=0, columnspan=2,
                                               sticky="w", pady=(0, 4))
    jump_x = tk.StringVar(value="—")
    jump_z = tk.StringVar(value="—")
    for i, (lbl, var) in enumerate([("Jump X:", jump_x), ("Jump Z:", jump_z)]):
        tk.Label(jf, text=lbl, bg=T.BG_CARD, fg=T.TEXT_SECONDARY,
                 font=("Segoe UI", 9)).grid(row=i + 1, column=0, sticky="w")
        tk.Label(jf, textvariable=var, bg=T.BG_CARD, fg=T.ACCENT_YELLOW,
                 font=("Segoe UI", 9, "bold")).grid(row=i + 1, column=1, sticky="e")

    return row + 1, enabled, entries, jump_x, jump_z


def _build_results(parent, row, SPX, SPY):
    f = tk.Frame(parent, bg=T.BG_CARD, highlightbackground=T.BORDER,
                 highlightthickness=1, padx=14, pady=10)
    f.grid(row=row, column=0, sticky="ew", padx=SPX, pady=SPY)
    f.columnconfigure(0, weight=1); f.columnconfigure(1, weight=1)
    tk.Label(f, text="RESULTS", bg=T.BG_CARD, fg=T.ACCENT_CYAN,
             font=("Segoe UI", 11, "bold")).grid(row=0, column=0, columnspan=2,
                                                sticky="w", pady=(0, 8))
    rvars = {}
    for i, (lbl, key) in enumerate([
        ("Final Speed",  "final_speed"),
        ("Safe Landing", "safe"),
        ("Flight Time",  "flight_time"),
        ("Landing X",    "landing_x"),
        ("Landing Z",    "landing_z"),
        ("Max Speed",    "max_speed"),
    ], start=1):
        tk.Label(f, text=lbl, bg=T.BG_CARD, fg=T.TEXT_SECONDARY,
                 font=("Segoe UI", 10)).grid(row=i, column=0, sticky="w", pady=3)
        sv = tk.StringVar(value="—")
        lw = tk.Label(f, textvariable=sv, bg=T.BG_CARD,
                      fg=T.TEXT_PRIMARY, font=("Segoe UI", 10, "bold"))
        lw.grid(row=i, column=1, sticky="e", pady=3)
        rvars[key] = (sv, lw)
    return row + 1, rvars


def _build_anim_speed_and_theme(parent, row, IPX, SPX):
    f = ttk.LabelFrame(parent, text="  SETTINGS  ", padding=(IPX, 6))
    f.grid(row=row, column=0, sticky="ew", padx=SPX, pady=(0, 10))
    f.columnconfigure(0, weight=1)

    # Theme Toggle
    theme_var = tk.StringVar(value="night")
    theme_f = ttk.Frame(f)
    theme_f.grid(row=0, column=0, sticky="w", pady=(0, 6))
    ttk.Radiobutton(theme_f, text="☀ Day Mode", variable=theme_var,
                    value="day", style="TRadiobutton").pack(side="left", padx=(0, 8))
    ttk.Radiobutton(theme_f, text="☾ Night Mode", variable=theme_var,
                    value="night", style="TRadiobutton").pack(side="left")

    # Anim Speed
    ttk.Label(f, text="Animation Speed", foreground=T.TEXT_SECONDARY,
              font=("Segoe UI", 8)).grid(row=1, column=0, sticky="w")
    var     = tk.DoubleVar(value=10.0)
    spd_lbl = ttk.Label(f, text="10x", foreground=T.ACCENT_CYAN,
                        font=("Segoe UI", 9, "bold"))
    spd_lbl.grid(row=1, column=0, sticky="e", padx=4)

    def _spd(v):
        spd_lbl.config(text=f"{int(float(v))}x")

    ttk.Scale(f, from_=1, to=200, orient="horizontal",
              variable=var, command=_spd).grid(row=2, column=0,
                                              sticky="ew", padx=2, pady=(2, 4))
                                              
    # Toggles
    wind_shear_var = tk.BooleanVar(value=False)
    follow_cam_var = tk.BooleanVar(value=False)
    ttk.Checkbutton(f, text="Altitude-Varying Wind (Shear)", variable=wind_shear_var,
                    style="TCheckbutton").grid(row=3, column=0, sticky="w", pady=(4, 0))
    ttk.Checkbutton(f, text="Follow Camera", variable=follow_cam_var,
                    style="TCheckbutton").grid(row=4, column=0, sticky="w", pady=(2, 0))
                    
    return row + 1, var, theme_var, wind_shear_var, follow_cam_var
