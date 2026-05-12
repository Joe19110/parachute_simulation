import tkinter as tk
from tkinter import ttk, messagebox

import numpy as np

from analysis import final_speed, safe_landing
from constants import SimulationParams
from simulator import simulate

from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure
from matplotlib.patches import Circle, Ellipse, Rectangle, Arc
from matplotlib.patches import Polygon, FancyArrowPatch
from matplotlib.lines import Line2D


def _float_from_entry(entry: ttk.Entry, fallback: float) -> float:
    """Parse a float from an entry, falling back to a default on failure."""
    try:
        return float(entry.get())
    except ValueError:
        return fallback


def _build_params(entries: dict[str, ttk.Entry]) -> SimulationParams:
    defaults = SimulationParams()
    return SimulationParams(
        m=_float_from_entry(entries["m"], defaults.m),
        h0=_float_from_entry(entries["h0"], defaults.h0),
        h_open=_float_from_entry(entries["h_open"], defaults.h_open),
        Cd_free=_float_from_entry(entries["Cd_free"], defaults.Cd_free),
        A_free=_float_from_entry(entries["A_free"], defaults.A_free),
        Cd_para=_float_from_entry(entries["Cd_para"], defaults.Cd_para),
        A_para=_float_from_entry(entries["A_para"], defaults.A_para),
        wind_speed=_float_from_entry(entries["wind_speed"], defaults.wind_speed),
        v_safe=_float_from_entry(entries["v_safe"], defaults.v_safe),
    )


def launch_ui():
    root = tk.Tk()
    root.title("Parachute Simulation (2D)")
    root.minsize(980, 620)

    style = ttk.Style()
    try:
        style.theme_use("clam")
    except Exception:
        pass
    style.configure("Title.TLabel", font=("Segoe UI", 14, "bold"))
    style.configure("Section.TLabelframe", padding=10)
    style.configure("Section.TLabelframe.Label", font=("Segoe UI", 10, "bold"))

    main = ttk.Frame(root, padding=10)
    main.grid(row=0, column=0, sticky="nsew")
    root.columnconfigure(0, weight=1)
    root.rowconfigure(0, weight=1)

    # Two-column layout: controls/results on the left, animation on the right.
    main.columnconfigure(0, weight=0)
    main.columnconfigure(1, weight=1)
    main.rowconfigure(1, weight=1)

    header = ttk.Frame(main)
    header.grid(row=0, column=0, columnspan=2, sticky="ew", pady=(0, 10))
    header.columnconfigure(0, weight=1)
    ttk.Label(header, text="Parachute Simulation (2D)", style="Title.TLabel").grid(row=0, column=0, sticky="w")
    ttk.Label(header, text="Adjust factors → Run → Watch the fall + results", foreground="#555").grid(
        row=1, column=0, sticky="w"
    )

    entries: dict[str, ttk.Entry] = {}
    defaults = SimulationParams()

    left = ttk.Frame(main)
    left.grid(row=1, column=0, sticky="nsew", padx=(0, 10))
    left.columnconfigure(0, weight=1)

    right = ttk.LabelFrame(main, text="Simulation (animation)", style="Section.TLabelframe")
    right.grid(row=1, column=1, sticky="nsew")
    right.columnconfigure(0, weight=1)
    right.rowconfigure(0, weight=1)

    inputs_frame = ttk.LabelFrame(left, text="Inputs", style="Section.TLabelframe")
    inputs_frame.grid(row=0, column=0, sticky="ew")
    inputs_frame.columnconfigure(0, weight=1)

    basic_frame = ttk.LabelFrame(inputs_frame, text="Basic (recommended)", style="Section.TLabelframe")
    basic_frame.grid(row=0, column=0, sticky="ew")
    basic_frame.columnconfigure(1, weight=1)

    advanced_frame = ttk.LabelFrame(inputs_frame, text="Advanced (optional)", style="Section.TLabelframe")
    advanced_frame.grid(row=1, column=0, sticky="ew", pady=(10, 0))
    advanced_frame.columnconfigure(1, weight=1)

    basic_fields = [
        ("Mass (kg)", "m"),
        ("Start height (m)", "h0"),
        ("Deploy height (m)", "h_open"),
        ("Wind speed (m/s)", "wind_speed"),
        ("Safe landing speed (m/s)", "v_safe"),
    ]
    advanced_fields = [
        ("Cd (freefall)", "Cd_free"),
        ("Area (freefall m²)", "A_free"),
        ("Cd (parachute)", "Cd_para"),
        ("Area (parachute m²)", "A_para"),
    ]

    def _add_field(parent: ttk.LabelFrame, row: int, label: str, key: str):
        ttk.Label(parent, text=label).grid(row=row, column=0, sticky="w", pady=3, padx=(0, 8))
        ent = ttk.Entry(parent, width=12)
        ent.insert(0, str(getattr(defaults, key)))
        ent.grid(row=row, column=1, sticky="ew", pady=3)
        entries[key] = ent

    for i, (label, key) in enumerate(basic_fields):
        _add_field(basic_frame, i, label, key)
    for i, (label, key) in enumerate(advanced_fields):
        _add_field(advanced_frame, i, label, key)

    results_frame = ttk.LabelFrame(left, text="Calculated values", style="Section.TLabelframe")
    results_frame.grid(row=1, column=0, sticky="ew", pady=(10, 0))
    results_frame.columnconfigure(0, weight=1)
    results_frame.columnconfigure(1, weight=1)
    result_vars = {
        "final_speed": tk.StringVar(value="-"),
        "safe": tk.StringVar(value="-"),
        "flight_time": tk.StringVar(value="-"),
        "landing_x": tk.StringVar(value="-"),
        "max_speed": tk.StringVar(value="-"),
    }

    ttk.Label(results_frame, text="Final speed (m/s):").grid(row=0, column=0, sticky="w")
    ttk.Label(results_frame, textvariable=result_vars["final_speed"]).grid(row=0, column=1, sticky="e")

    ttk.Label(results_frame, text="Safe landing:").grid(row=1, column=0, sticky="w")
    ttk.Label(results_frame, textvariable=result_vars["safe"]).grid(row=1, column=1, sticky="e")

    ttk.Label(results_frame, text="Flight time (s):").grid(row=2, column=0, sticky="w")
    ttk.Label(results_frame, textvariable=result_vars["flight_time"]).grid(row=2, column=1, sticky="e")

    ttk.Label(results_frame, text="Landing x (m):").grid(row=3, column=0, sticky="w")
    ttk.Label(results_frame, textvariable=result_vars["landing_x"]).grid(row=3, column=1, sticky="e")

    ttk.Label(results_frame, text="Max speed (m/s):").grid(row=4, column=0, sticky="w")
    ttk.Label(results_frame, textvariable=result_vars["max_speed"]).grid(row=4, column=1, sticky="e")

    # --- Embedded animation figure (on the right) ---
    fig_anim = Figure(figsize=(6.8, 6.0), dpi=100)
    ax_anim = fig_anim.add_subplot(111)
    ax_anim.set_xlabel("x (m)")
    ax_anim.set_ylabel("height y (m)")
    ax_anim.set_title("2D fall (with wind)")
    ax_anim.grid(True, alpha=0.25)

    canvas_anim = FigureCanvasTkAgg(fig_anim, master=right)
    canvas_anim.get_tk_widget().grid(row=0, column=0, sticky="nsew")

    # --- Scene graphics (background + actor) ---
    # Background: layered sky + ground
    ax_anim.set_facecolor("#eaf4ff")
    ax_anim.axhspan(-60, 0, facecolor="#c7b299", zorder=0)  # ground
    ax_anim.axhline(0, color="#6b5b4a", linewidth=2, alpha=0.8, zorder=1)

    # A few "clouds" (simple circles) that drift a bit with wind (purely visual)
    cloud_patches = []
    for cx, cy, r in [(-25, defaults.h0 * 0.85, 6), (-10, defaults.h0 * 0.92, 4), (15, defaults.h0 * 0.88, 7)]:
        c1 = Circle((cx, cy), r, facecolor="white", edgecolor="#d6e9ff", linewidth=1, alpha=0.9, zorder=1)
        c2 = Circle((cx + r * 0.9, cy + r * 0.2), r * 0.8, facecolor="white", edgecolor="#d6e9ff", linewidth=1, alpha=0.9, zorder=1)
        c3 = Circle((cx - r * 0.9, cy + r * 0.1), r * 0.75, facecolor="white", edgecolor="#d6e9ff", linewidth=1, alpha=0.9, zorder=1)
        for c in (c1, c2, c3):
            ax_anim.add_patch(c)
            cloud_patches.append(c)

    # Wind indicator (arrow + label in axes coords)
    wind_arrow = FancyArrowPatch((0.78, 0.92), (0.96, 0.92), transform=ax_anim.transAxes, arrowstyle="-|>", mutation_scale=14,
                                 linewidth=2, color="#2b6cb0", zorder=10)
    ax_anim.add_patch(wind_arrow)
    wind_label = ax_anim.text(0.78, 0.95, "wind: 0.0 m/s", transform=ax_anim.transAxes, color="#2b6cb0",
                              fontsize=9, zorder=10)

    # Trajectory trail
    (trail_line,) = ax_anim.plot([], [], color="#1f77b4", linewidth=1.6, alpha=0.7, zorder=2)

    # Velocity vector (arrow) for motion readability
    vel_arrow = FancyArrowPatch((0, 0), (0, 0), arrowstyle="->", mutation_scale=12, linewidth=2, color="#d9480f", zorder=9)
    ax_anim.add_patch(vel_arrow)


    # Stickman skydiver (proper lines for limbs, more realistic)
    # Use Ellipse (not Circle) for head/eyes: Circle radius is in data-coords,
    # which is distorted when y_range >> x_range. Ellipse lets us set w and h separately.
    head = Ellipse((0, defaults.h0), 1.0, 1.0, color="#1a202c", zorder=6)
    torso_line, = ax_anim.plot([], [], color="#1a202c", linewidth=3.5, zorder=6)
    arm_left_line, = ax_anim.plot([], [], color="#1a202c", linewidth=2.8, zorder=6)
    arm_right_line, = ax_anim.plot([], [], color="#1a202c", linewidth=2.8, zorder=6)
    leg_left_line, = ax_anim.plot([], [], color="#1a202c", linewidth=2.8, zorder=6)
    leg_right_line, = ax_anim.plot([], [], color="#1a202c", linewidth=2.8, zorder=6)
    ax_anim.add_patch(head)
    
    # Facial features (eyes and mouth) – also Ellipse so they stay circular
    eye_left       = Ellipse((0, 0), 0, 0, color="#ffffff", zorder=7)
    eye_right      = Ellipse((0, 0), 0, 0, color="#ffffff", zorder=7)
    eye_pupil_left  = Ellipse((0, 0), 0, 0, color="#1a202c", zorder=8)
    eye_pupil_right = Ellipse((0, 0), 0, 0, color="#1a202c", zorder=8)
    mouth_line, = ax_anim.plot([], [], color="#1a202c", linewidth=2, zorder=7)
    ax_anim.add_patch(eye_left)
    ax_anim.add_patch(eye_right)
    ax_anim.add_patch(eye_pupil_left)
    ax_anim.add_patch(eye_pupil_right)
    
    # Status text (shown after landing)
    status_text = ax_anim.text(
        0.70, 0.86, "", transform=ax_anim.transAxes, fontsize=11, fontweight="bold", color="#2d3748", zorder=12
    )

    # Parachute canopy (semi-ellipse) + suspension lines + harness
    canopy_fill = Polygon([[0, defaults.h0], [0, defaults.h0], [0, defaults.h0]], closed=True,
                          facecolor="#b0b8c1", edgecolor="#495057", linewidth=2, alpha=0.97, zorder=5)
    ax_anim.add_patch(canopy_fill)

    # Panel lines on canopy (visual detail)
    canopy_panels = []
    for _ in range(6):
        (ln,) = ax_anim.plot([], [], linewidth=1.0, color="#6c757d", alpha=0.8, zorder=6)
        canopy_panels.append(ln)

    # Suspension lines
    suspension_lines = []
    for _ in range(8):
        (ln,) = ax_anim.plot([], [], linewidth=1.1, color="#495057", alpha=0.95, zorder=6)
        suspension_lines.append(ln)

    harness = Rectangle((0, 0), 0.8, 0.25, color="#495057", zorder=6)
    ax_anim.add_patch(harness)

    canopy_fill.set_visible(False)
    for ln in canopy_panels:
        ln.set_visible(False)
    for ln in suspension_lines:
        ln.set_visible(False)
    harness.set_visible(False)

    latest_params: dict[str, SimulationParams] = {"value": defaults}
    latest_data: dict[str, np.ndarray] = {"value": simulate(defaults)}
    anim_speed = tk.DoubleVar(value=10.0)  # multiplier: how many sim frames to advance per tick

    def _update_anim_axes(params: SimulationParams, data: np.ndarray):
        # Keep view stable-ish: center around trajectory with padding.
        xs = data[:, 1]
        ys = data[:, 2]
        x_pad = max(10.0, 0.15 * (xs.max() - xs.min() + 1e-9))
        ax_anim.set_xlim(xs.min() - x_pad, xs.max() + x_pad)
        ax_anim.set_ylim(min(-50.0, float(ys.min()) - 10.0), max(params.h0, float(ys.max())) + 10.0)

    # Tk-driven animation loop (more reliable than FuncAnimation in embedded canvases)
    anim_state = {
        "after_id": None,
        "frame": 0,
        "running": False,
        "deploy_idx": 0,
        "inflation_frames": 1,
        "landed": False,
        "landing_safe": False,
        "post_landing_frame": 0,
        "confetti_data": [],  # List of (x, y, vx, vy, color) for each particle
        "landing_idx": 0,    # Pre-computed ground-contact frame index
        "feet_offset": 0.0,  # Stickman feet offset in y-data-units below head center
    }

    def _stop_anim():
        if anim_state["after_id"] is not None:
            try:
                root.after_cancel(anim_state["after_id"])
            except Exception:
                pass
            anim_state["after_id"] = None
        anim_state["running"] = False

    def _reset_anim(params: SimulationParams, data: np.ndarray):
        _stop_anim()
        anim_state["frame"] = 0
        anim_state["deploy_idx"] = int(np.argmax(data[:, 2] <= params.h_open)) if len(data) else 0
        anim_state["inflation_frames"] = max(1, int(1.5 / max(1e-6, params.dt)))

        # Set axes limits first so we can read the pixel size.
        _update_anim_axes(params, data)

        # ── Compute stickman feet offset in data-units ────────────────────────
        # The stickman head center is at data_y. Feet are this many y-data-units below:
        #   feet_offset = (HEAD_R_PX + TORSO_PX + LEG_LEN_PX) * du_per_px_y
        # Landing should trigger when  data_y - feet_offset <= 0
        #   i.e. data_y <= feet_offset
        HEAD_R_PX = 9.0
        TORSO_PX  = 12.0
        LEG_LEN_PX = 20.0
        try:
            bbox = ax_anim.get_window_extent()
            ax_h_px = max(1.0, bbox.height)
        except Exception:
            ax_h_px = 450.0
        try:
            y0_lim, y1_lim = ax_anim.get_ylim()
            y_range = max(1e-6, abs(y1_lim - y0_lim))
        except Exception:
            y_range = params.h0 + 60.0
        du_per_px_y = y_range / ax_h_px
        feet_offset = (HEAD_R_PX + TORSO_PX + LEG_LEN_PX) * du_per_px_y
        anim_state["feet_offset"] = feet_offset   # saved so _tick_anim can clamp y

        # Find first frame (past frame 5) where visual feet reach ground (data_y <= feet_offset)
        if len(data) > 5:
            ground_hits = np.where(data[5:, 2] <= feet_offset)[0]
            anim_state["landing_idx"] = int(ground_hits[0]) + 5 if len(ground_hits) else len(data) - 1
        else:
            anim_state["landing_idx"] = max(0, len(data) - 1)
        # Reset parachute visibility
        for ln in canopy_panels:
            ln.set_visible(False)
        for ln in suspension_lines:
            ln.set_visible(False)
        canopy_fill.set_visible(False)
        harness.set_visible(False)
        # Reset stickman lines
        torso_line.set_data([], [])
        arm_left_line.set_data([], [])
        arm_right_line.set_data([], [])
        leg_left_line.set_data([], [])
        leg_right_line.set_data([], [])
        # Reset facial features
        eye_left.set_visible(False)
        eye_right.set_visible(False)
        eye_pupil_left.set_visible(False)
        eye_pupil_right.set_visible(False)
        mouth_line.set_data([], [])
        status_text.set_text("")
        # Reset trail and velocity arrow
        trail_line.set_data([], [])
        vel_arrow.set_positions((0, 0), (0, 0))
        wind_label.set_text(f"wind: {params.wind_speed:.1f} m/s")
        # Flip arrow direction based on sign
        if params.wind_speed >= 0:
            wind_arrow.set_positions((0.78, 0.92), (0.96, 0.92))
        else:
            wind_arrow.set_positions((0.96, 0.92), (0.78, 0.92))
        # Reset landing state
        anim_state["landed"] = False
        anim_state["landing_safe"] = False
        anim_state["post_landing_frame"] = 0
        anim_state["confetti_data"] = []
        canvas_anim.draw()

    def _tick_anim():
        params = latest_params["value"]
        data = latest_data["value"]
        n = len(data)
        if n == 0:
            anim_state["running"] = False
            return

        f = anim_state["frame"]
        landing_idx = anim_state["landing_idx"]

        # ── Landing detection: trigger when animation frame reaches landing_idx ─
        # Pre-computed at reset time → not affected by frame-skipping or y sign noise.
        if f >= landing_idx and not anim_state["landed"]:
            anim_state["landed"] = True
            anim_state["landing_safe"] = safe_landing(data, params, ground_y=anim_state["feet_offset"])

        # Clamp f to landing_idx once on the ground (freeze position at landing)
        if anim_state["landed"]:
            f = min(landing_idx, n - 1)

        x = float(data[min(f, n-1), 1])
        y = float(data[min(f, n-1), 2])
        vx = float(data[min(f, n-1), 3])
        vy = float(data[min(f, n-1), 4])

        # Pin y so feet sit exactly on the ground line (y=0).
        # feet_offset = stickman body height in y-data-units.
        # When head is at y=feet_offset, feet are at y - feet_offset = 0.
        feet_offset = anim_state["feet_offset"]
        if anim_state["landed"] or y < feet_offset:
            y = feet_offset

        # ── Axis range (data units) ──────────────────────────────────────────
        try:
            x0_lim, x1_lim = ax_anim.get_xlim()
            y0_lim, y1_lim = ax_anim.get_ylim()
            x_range = max(1e-6, abs(x1_lim - x0_lim))
            y_range = max(1e-6, abs(y1_lim - y0_lim))
        except Exception:
            x_range, y_range = 100.0, params.h0 + 60.0

        # ── Pixel ↔ data-unit conversion ─────────────────────────────────────
        # Ask matplotlib how many pixels the axes occupy, then derive how many
        # data-units correspond to 1 pixel on each axis separately.
        # All stickman dimensions are defined in PIXELS then converted → no distortion.
        try:
            bbox = ax_anim.get_window_extent()   # axes bounding box in display pixels
            ax_w_px = max(1.0, bbox.width)
            ax_h_px = max(1.0, bbox.height)
        except Exception:
            ax_w_px, ax_h_px = 500.0, 450.0

        du_per_px_x = x_range / ax_w_px   # data-units per pixel (X axis)
        du_per_px_y = y_range / ax_h_px   # data-units per pixel (Y axis)

        # ── Stickman pixel dimensions (tweak these to change on-screen size) ─
        HEAD_R_PX    = 9.0    # head radius
        TORSO_PX     = 12.0   # torso length  (short – user request)
        ARM_LEN_PX   = 11.0   # arm length (short)
        LEG_LEN_PX   = 20.0   # leg length
        SHOULDER_PX  = 10.0   # shoulder half-width
        ARM_H_PX     = 9.0    # arm horizontal spread (short)
        LEG_SPR_PX   = 7.0    # leg spread at hip

        # Convert to data units using each axis independently
        head_size  = HEAD_R_PX   * du_per_px_y
        torso_len  = TORSO_PX    * du_per_px_y
        arm_len    = ARM_LEN_PX  * du_per_px_y   # vertical component
        leg_len    = LEG_LEN_PX  * du_per_px_y
        shoulder_w = SHOULDER_PX * du_per_px_x   # horizontal  (x-data-units)
        arm_dx     = ARM_H_PX    * du_per_px_x   # arm horiz spread (x-data-units)
        leg_spread = LEG_SPR_PX  * du_per_px_x   # leg spread  (x-data-units)

        # ── Flail oscillation (freefall panic animation) ──────────────────────
        # Use current frame to drive a sinusoidal wave; left and right arms are
        # 180° out of phase so they alternate like a real panicking skydiver.
        flail_t = anim_state["frame"] * 0.35          # time variable (speed of flailing)
        flail_amp_dy = 7.0 * du_per_px_y             # ± vertical flail in y-data-units
        flail_amp_dx = 5.0 * du_per_px_x             # ± horizontal flail in x-data-units
        # Left arm oscillates with sin, right arm with -sin (opposite phase)
        flail_L_dy = flail_amp_dy * np.sin(flail_t)
        flail_R_dy = flail_amp_dy * np.sin(flail_t + np.pi)
        # Legs flail slightly too (slower, quarter-period offset)
        flail_leg_dy = 5.0 * du_per_px_y * np.sin(flail_t * 0.7)

        # ── Canopy / harness sizes (also pixel-derived) ───────────────────────
        person_h     = (HEAD_R_PX * 2 + TORSO_PX + LEG_LEN_PX) * du_per_px_y
        person_w     = SHOULDER_PX * 2 * du_per_px_x
        canopy_w_base = 80.0 * du_per_px_x   # 80 px wide canopy
        canopy_h_base = 35.0 * du_per_px_y   # 35 px tall canopy

        # ── Plane: removed by user request ───────────────────────────────────

        # width/height set separately in x/y data-units so it renders as a circle on screen
        head_w = HEAD_R_PX * 2 * du_per_px_x
        head_h = HEAD_R_PX * 2 * du_per_px_y
        head.set_center((x, y))
        head.set_width(head_w)
        head.set_height(head_h)
        head.set_visible(True)

        # ── Torso (vertical line just below head) ─────────────────────────────
        torso_top_y    = y - head_size   # head_size = HEAD_R_PX * du_per_px_y
        torso_bottom_y = torso_top_y - torso_len
        torso_line.set_data([x, x], [torso_top_y, torso_bottom_y])
        torso_line.set_linewidth(3.0)
        torso_line.set_visible(True)

        # Shoulder attachment point (top of torso)
        arm_attach_y = torso_top_y

        # ── Arms ─────────────────────────────────────────────────────────────
        if y > params.h_open:
            # Freefall: arms FLAIL – left/right endpoints oscillate opposite phase
            arm_dy = arm_len * 0.75
            arm_left_line.set_data(
                [x - shoulder_w * 0.3, x - shoulder_w - arm_dx],
                [arm_attach_y,          arm_attach_y - arm_dy + flail_L_dy],
            )
            arm_right_line.set_data(
                [x + shoulder_w * 0.3, x + shoulder_w + arm_dx],
                [arm_attach_y,          arm_attach_y - arm_dy + flail_R_dy],
            )
        else:
            # Parachute open: arms calm, slightly out and down
            arm_dy = arm_len
            arm_left_line.set_data(
                [x - shoulder_w * 0.3, x - shoulder_w - arm_dx * 0.3],
                [arm_attach_y,          arm_attach_y - arm_dy],
            )
            arm_right_line.set_data(
                [x + shoulder_w * 0.3, x + shoulder_w + arm_dx * 0.3],
                [arm_attach_y,          arm_attach_y - arm_dy],
            )
        arm_left_line.set_linewidth(2.5)
        arm_right_line.set_linewidth(2.5)
        arm_left_line.set_visible(True)
        arm_right_line.set_visible(True)

        # ── Legs ─────────────────────────────────────────────────────────────
        hip_y = torso_bottom_y
        if y > params.h_open:
            # Freefall: legs KICK – left/right alternate up/down (opposite phase)
            leg_left_line.set_data(
                [x, x - leg_spread],
                [hip_y, hip_y - leg_len + flail_leg_dy],
            )
            leg_right_line.set_data(
                [x, x + leg_spread],
                [hip_y, hip_y - leg_len - flail_leg_dy],
            )
        else:
            # Parachute: legs together, straight and calm
            leg_left_line.set_data(
                [x - leg_spread * 0.4, x - leg_spread * 0.4],
                [hip_y, hip_y - leg_len],
            )
            leg_right_line.set_data(
                [x + leg_spread * 0.4, x + leg_spread * 0.4],
                [hip_y, hip_y - leg_len],
            )
        leg_left_line.set_linewidth(2.5)
        leg_right_line.set_linewidth(2.5)
        leg_left_line.set_visible(True)
        leg_right_line.set_visible(True)

        if y <= params.h_open:
            k = max(0, f - anim_state["deploy_idx"])
            inflate = min(1.0, k / anim_state["inflation_frames"])

            # Slight sway based on horizontal speed/wind to make it feel alive
            sway = np.clip((vx - params.wind_speed) * 0.05, -0.8, 0.8) * inflate

            # Filled canopy polygon (semi-ellipse canopy)
            w = canopy_w_base * (0.55 + 0.55 * inflate)
            h = canopy_h_base * (0.55 + 0.55 * inflate)
            cx = x + sway
            cy = y + 1.35 * person_h + 0.15 * person_h * inflate

            # Build semi-ellipse arc (left -> right) + bottom edge back to left
            theta = np.linspace(np.pi, 0, 25)
            arc = np.column_stack([cx + (w / 2) * np.cos(theta), cy + h * np.sin(theta)])
            bottom = np.array([[cx + w / 2, cy], [cx - w / 2, cy]])
            poly = np.vstack([arc, bottom])
            canopy_fill.set_xy(poly)
            canopy_fill.set_visible(True)

            # Canopy panel lines (radials)
            panel_thetas = np.linspace(np.pi * 0.15, np.pi * 0.85, len(canopy_panels))
            for ln, th in zip(canopy_panels, panel_thetas):
                px = cx + (w / 2) * np.cos(th)
                py = cy + h * np.sin(th)
                ln.set_data([cx, px], [cy, py])
                ln.set_visible(True)

            # Harness just above person
            harness_y = y + 0.25 * person_h
            harness.set_width(max(0.8, 1.2 * person_w))
            harness.set_height(max(0.25, 0.06 * person_h))
            harness.set_xy((x - harness.get_width() / 2, harness_y))
            harness.set_visible(True)

            # Suspension lines connect canopy edge to harness points
            canopy_attach_xs = np.linspace(cx - 0.42 * w, cx + 0.42 * w, len(suspension_lines))
            harness_attach_xs = np.linspace(
                x - 0.45 * harness.get_width(), x + 0.45 * harness.get_width(), len(suspension_lines)
            )
            for ln, axx, hxx in zip(suspension_lines, canopy_attach_xs, harness_attach_xs):
                ln.set_data([axx, hxx], [cy, harness_y])
                ln.set_visible(True)
        else:
            canopy_fill.set_visible(False)
            for ln in canopy_panels:
                ln.set_visible(False)
            for ln in suspension_lines:
                ln.set_visible(False)
            harness.set_visible(False)

        # ── Facial features (Ellipse, separate x/y sizes) ─────────────────────
        eye_w        = HEAD_R_PX * 0.56 * du_per_px_x   # width  in x-data-units
        eye_h        = HEAD_R_PX * 0.56 * du_per_px_y   # height in y-data-units
        pupil_w      = eye_w * 0.5
        pupil_h      = eye_h * 0.5
        eye_y_offset = HEAD_R_PX * 0.20 * du_per_px_y
        eye_x_offset = HEAD_R_PX * 0.38 * du_per_px_x
        
        if anim_state["landed"]:
            # Post-landing: show success or failure animation
            anim_state["post_landing_frame"] += 1
            
            if anim_state["landing_safe"]:
                status_text.set_text("SAFE LANDING!")
                status_text.set_color("#2f9e44")
                # SUCCESS: Celebration pose + confetti + smile
                # Arms raised up in V shape
                arm_left_line.set_data(
                    [x - shoulder_w * 0.3, x - shoulder_w - arm_dx * 0.7],
                    [arm_attach_y,          arm_attach_y + arm_len * 0.9]
                )
                arm_right_line.set_data(
                    [x + shoulder_w * 0.3, x + shoulder_w + arm_dx * 0.7],
                    [arm_attach_y,          arm_attach_y + arm_len * 0.9]
                )
                # Legs slightly bent (jumping pose)
                leg_left_line.set_data(
                    [x - leg_spread * 0.3, x - leg_spread * 0.9],
                    [hip_y,                 hip_y - leg_len * 0.65]
                )
                leg_right_line.set_data(
                    [x + leg_spread * 0.3, x + leg_spread * 0.9],
                    [hip_y,                 hip_y - leg_len * 0.65]
                )
                
                # Happy eyes (normal)
                eye_left.set_center((x - eye_x_offset, y + eye_y_offset))
                eye_left.set_width(eye_w)
                eye_left.set_height(eye_h)
                eye_left.set_visible(True)
                eye_right.set_center((x + eye_x_offset, y + eye_y_offset))
                eye_right.set_width(eye_w)
                eye_right.set_height(eye_h)
                eye_right.set_visible(True)
                eye_pupil_left.set_center((x - eye_x_offset, y + eye_y_offset))
                eye_pupil_left.set_width(pupil_w)
                eye_pupil_left.set_height(pupil_h)
                eye_pupil_left.set_visible(True)
                eye_pupil_right.set_center((x + eye_x_offset, y + eye_y_offset))
                eye_pupil_right.set_width(pupil_w)
                eye_pupil_right.set_height(pupil_h)
                eye_pupil_right.set_visible(True)
                
                # Smile (arc) – width in x-data-units, amplitude in y-data-units
                smile_y     = y - eye_y_offset * 1.5
                smile_half  = HEAD_R_PX * 0.55 * du_per_px_x
                smile_amp   = HEAD_R_PX * 0.25 * du_per_px_y
                smile_pts   = 15
                smile_xs = np.linspace(x - smile_half, x + smile_half, smile_pts)
                smile_ys = smile_y + smile_amp * np.sin(np.linspace(0, np.pi, smile_pts))
                mouth_line.set_data(smile_xs, smile_ys)
                mouth_line.set_data(smile_xs, smile_ys)
            else:
                # UNSAFE landing (non-violent): dizzy/sad face + warning text
                status_text.set_text("UNSAFE LANDING")
                status_text.set_color("#c92a2a")

                # Keep body upright but a little "slumped" (small wobble)
                wobble = arm_dx * 0.12 * np.sin(anim_state["post_landing_frame"] * 0.25)
                torso_line.set_data([x, x + wobble], [torso_top_y, torso_bottom_y])

                # Arms slumped downward
                arm_left_line.set_data(
                    [x - shoulder_w * 0.3, x - shoulder_w - arm_dx * 0.3],
                    [arm_attach_y,          arm_attach_y - arm_len * 0.9]
                )
                arm_right_line.set_data(
                    [x + shoulder_w * 0.3, x + shoulder_w + arm_dx * 0.3],
                    [arm_attach_y,          arm_attach_y - arm_len * 0.9]
                )

                # Legs slightly bent outward
                leg_left_line.set_data(
                    [x - leg_spread * 0.3, x - leg_spread * 0.8],
                    [hip_y,                 hip_y - leg_len * 0.75]
                )
                leg_right_line.set_data(
                    [x + leg_spread * 0.3, x + leg_spread * 0.8],
                    [hip_y,                 hip_y - leg_len * 0.75]
                )

                # Dizzy eyes (no pupils)
                eye_left.set_center((x - eye_x_offset, y + eye_y_offset))
                eye_left.set_width(eye_w)
                eye_left.set_height(eye_h)
                eye_left.set_visible(True)
                eye_right.set_center((x + eye_x_offset, y + eye_y_offset))
                eye_right.set_width(eye_w)
                eye_right.set_height(eye_h)
                eye_right.set_visible(True)
                eye_pupil_left.set_visible(False)
                eye_pupil_right.set_visible(False)

                # Frown – width in x-data-units, amplitude in y-data-units
                frown_y    = y - eye_y_offset * 1.9
                frown_half = HEAD_R_PX * 0.55 * du_per_px_x
                frown_amp  = HEAD_R_PX * 0.25 * du_per_px_y
                pts = 15
                xs = np.linspace(x - frown_half, x + frown_half, pts)
                ys = frown_y - frown_amp * np.sin(np.linspace(0, np.pi, pts))
                mouth_line.set_data(xs, ys)
        else:
            # Normal flight: no facial features visible
            eye_left.set_visible(False)
            eye_right.set_visible(False)
            eye_pupil_left.set_visible(False)
            eye_pupil_right.set_visible(False)
            mouth_line.set_data([], [])
            status_text.set_text("")

        # Trail
        trail_line.set_data(data[: min(f + 1, n), 1], data[: min(f + 1, n), 2])

        # Velocity arrow for readability (scaled down) - hide after landing
        if not anim_state["landed"]:
            scale = 0.25
            vel_arrow.set_positions((x, y), (x + vx * scale, y + vy * scale))
        else:
            vel_arrow.set_positions((0, 0), (0, 0))

        # Draw immediately to force refresh on Tk
        canvas_anim.draw()
        # Advance multiple frames per tick for "speed-up" (but continue post-landing animation)
        if anim_state["landed"]:
            # Post-landing: continue animation for celebration/death scene
            if anim_state["post_landing_frame"] < 200:  # Run post-landing for 200 frames (~4 seconds)
                anim_state["after_id"] = root.after(20, _tick_anim)
            else:
                # Stop after post-landing animation completes
                anim_state["running"] = False
                anim_state["after_id"] = None
        else:
            step = max(1, int(anim_speed.get()))
            anim_state["frame"] = min(n, anim_state["frame"] + step)
            anim_state["after_id"] = root.after(20, _tick_anim)

    def _start_anim():
        if anim_state["running"]:
            return
        anim_state["running"] = True
        anim_state["after_id"] = root.after(0, _tick_anim)

    def run_simulation():
        try:
            params = _build_params(entries)
        except Exception as exc:
            messagebox.showerror("Invalid input", f"Could not parse inputs: {exc}")
            return

        data = simulate(params)
        latest_params["value"] = params
        latest_data["value"] = data

        if len(data) == 0:
            result_vars["final_speed"].set("0.00")
            result_vars["safe"].set("No")
            result_vars["flight_time"].set("0.00")
            result_vars["landing_x"].set("0.00")
            result_vars["max_speed"].set("0.00")
        else:
            # Synchronize landing results with the visual impact point (where feet touch)
            # Fetch the feet offset from anim_state (which is updated in _reset_anim)
            # Actually _reset_anim is called AFTER this, so we need to compute it.
            HEAD_R_PX = 9.0
            TORSO_PX  = 12.0
            LEG_LEN_PX = 20.0
            try:
                # We need to compute feet_offset here to show correct results in the sidebar
                bbox = ax_anim.get_window_extent()
                ax_h_px = max(1.0, bbox.height)
                y0_lim, y1_lim = ax_anim.get_ylim() # Note: uses current limits, might be slightly off if limits change
                y_range = max(1e-6, abs(y1_lim - y0_lim))
            except Exception:
                ax_h_px = 450.0
                y_range = params.h0 + 60.0
            
            # Simple approximation for feet_offset if UI isn't fully laid out yet
            du_per_px_y = y_range / ax_h_px
            feet_off = (HEAD_R_PX + TORSO_PX + LEG_LEN_PX) * du_per_px_y

            final_v = final_speed(data, ground_y=feet_off)
            result_vars["final_speed"].set(f"{final_v:.2f}")

            # Re-check safety at the feet impact point
            is_safe = final_v <= params.v_safe
            result_vars["safe"].set("Yes" if is_safe else "No")
            
            # Find the index of landing for other stats
            hits = np.where(data[:, 2] <= feet_off)[0]
            idx = hits[0] if len(hits) > 0 else -1
            
            result_vars["flight_time"].set(f"{data[idx, 0]:.2f}")
            result_vars["landing_x"].set(f"{data[idx, 1]:.2f}")
            max_speed = float(np.sqrt(data[:, 3] ** 2 + data[:, 4] ** 2).max())
            result_vars["max_speed"].set(f"{max_speed:.2f}")

        _reset_anim(params, data)
        _start_anim()

    # Initialize visuals with defaults
    _reset_anim(defaults, latest_data["value"])

    # Button bar at bottom
    button_frame = ttk.Frame(left)
    button_frame.grid(row=2, column=0, sticky="ew", pady=(10, 0))
    button_frame.columnconfigure(0, weight=1)
    button_frame.columnconfigure(1, weight=1)
    button_frame.columnconfigure(2, weight=1)

    ttk.Button(button_frame, text="Run", command=run_simulation).grid(row=0, column=0, sticky="ew", padx=(0, 6))
    ttk.Button(button_frame, text="Pause", command=_stop_anim).grid(row=0, column=1, sticky="ew", padx=6)
    ttk.Button(button_frame, text="Quit", command=root.destroy).grid(row=0, column=2, sticky="ew", padx=(6, 0))

    # Animation speed control
    speed_frame = ttk.LabelFrame(left, text="Animation speed", style="Section.TLabelframe")
    speed_frame.grid(row=3, column=0, sticky="ew", pady=(10, 0))
    speed_frame.columnconfigure(0, weight=1)
    
    speed_top = ttk.Frame(speed_frame)
    speed_top.grid(row=0, column=0, sticky="ew")
    speed_top.columnconfigure(0, weight=1)

    ttk.Label(speed_top, text="Speed multiplier:").grid(row=0, column=0, sticky="w")
    speed_val_label = ttk.Label(speed_top, text="10x")
    speed_val_label.grid(row=0, column=1, sticky="e")

    def _on_speed_change(evt=None):
        v = anim_speed.get()
        speed_val_label.config(text=f"{int(v)}x")

    speed_scale = ttk.Scale(
        speed_frame, 
        from_=1, 
        to=200, 
        orient="horizontal", 
        variable=anim_speed,
        command=_on_speed_change
    )
    speed_scale.grid(row=1, column=0, sticky="ew", pady=(5, 0))

    root.mainloop()


if __name__ == "__main__":
    launch_ui()
