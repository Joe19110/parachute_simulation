import tkinter as tk
from tkinter import ttk, messagebox
import numpy as np
from analysis import final_speed, safe_landing
from constants import SimulationParams
from simulator import simulate
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure
from matplotlib.patches import Circle, Ellipse, Rectangle, Polygon, FancyArrowPatch
from matplotlib.lines import Line2D
import theme as T


def _build_params_from_sliders(sliders, adv_entries, drop_mode_var, vehicle_var):
    d = SimulationParams()
    p = SimulationParams(
        m=sliders["m"].get(), h0=sliders["h0"].get(), h_open=sliders["h_open"].get(),
        wind_speed=sliders["wind_speed"].get(), v_safe=sliders["v_safe"].get(),
        Cd_free=_fval(adv_entries["Cd_free"], d.Cd_free),
        A_free=_fval(adv_entries["A_free"], d.A_free),
        Cd_para=_fval(adv_entries["Cd_para"], d.Cd_para),
        A_para=_fval(adv_entries["A_para"], d.A_para),
        drop_mode=drop_mode_var.get(), vehicle_behavior=vehicle_var.get(),
    )
    if p.drop_mode == "plane":
        p.vx0 = 50.0
    elif p.drop_mode == "helicopter":
        p.vx0 = 0.0
    return p


def _fval(entry, fallback):
    try: return float(entry.get())
    except ValueError: return fallback


def launch_ui():
    root = tk.Tk()
    root.title("🪂 Parachute Simulation")
    root.minsize(1280, 750)
    root.configure(bg=T.BG_DARK)

    # ── Dark ttk styling ──────────────────────────────────────────────────
    style = ttk.Style()
    try: style.theme_use("clam")
    except: pass
    style.configure(".", background=T.BG_DARK, foreground=T.TEXT_PRIMARY, fieldbackground=T.BG_INPUT,
                     borderwidth=0, font=("Segoe UI", 10))
    style.configure("TFrame", background=T.BG_DARK)
    style.configure("TLabel", background=T.BG_DARK, foreground=T.TEXT_PRIMARY)
    style.configure("TLabelframe", background=T.BG_PANEL, foreground=T.ACCENT_CYAN,
                     bordercolor=T.BORDER, borderwidth=1, relief="solid",
                     padding=(8, 6))
    style.configure("TLabelframe.Label", background=T.BG_PANEL, foreground=T.ACCENT_CYAN,
                     font=("Segoe UI", 10, "bold"))
    style.configure("TEntry", fieldbackground=T.BG_INPUT, foreground=T.TEXT_PRIMARY,
                     insertcolor=T.TEXT_PRIMARY, borderwidth=1, relief="solid")
    style.configure("TRadiobutton", background=T.BG_PANEL, foreground=T.TEXT_PRIMARY,
                     font=("Segoe UI", 10))
    style.map("TRadiobutton", background=[("active", T.BG_CARD)])
    style.configure("TScale", background=T.BG_PANEL, troughcolor=T.BG_INPUT)
    style.configure("Title.TLabel", font=("Segoe UI", 16, "bold"), foreground=T.ACCENT_CYAN,
                     background=T.BG_DARK)
    style.configure("Sub.TLabel", foreground=T.TEXT_SECONDARY, background=T.BG_DARK,
                     font=("Segoe UI", 9))
    style.configure("Result.TLabel", foreground=T.ACCENT_CYAN, background=T.BG_CARD,
                     font=("Segoe UI", 11, "bold"))
    style.configure("ResVal.TLabel", foreground=T.TEXT_PRIMARY, background=T.BG_CARD,
                     font=("Segoe UI", 11))
    style.configure("Safe.TLabel", foreground=T.ACCENT_GREEN, background=T.BG_CARD,
                     font=("Segoe UI", 12, "bold"))
    style.configure("Unsafe.TLabel", foreground=T.ACCENT_RED, background=T.BG_CARD,
                     font=("Segoe UI", 12, "bold"))

    # Button styles
    for name, bg, fg in [("Run.TButton", T.ACCENT_CYAN, T.BG_DARK),
                          ("Pause.TButton", T.ACCENT_ORANGE, T.BG_DARK),
                          ("Quit.TButton", T.ACCENT_RED, T.TEXT_PRIMARY),
                          ("Reset.TButton", T.BORDER, T.TEXT_PRIMARY)]:
        style.configure(name, background=bg, foreground=fg, font=("Segoe UI", 10, "bold"),
                         borderwidth=0, padding=6)
        style.map(name, background=[("active", bg)])

    # ── Layout ────────────────────────────────────────────────────────────
    main = ttk.Frame(root)
    main.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)
    root.columnconfigure(0, weight=1); root.rowconfigure(0, weight=1)
    main.columnconfigure(0, weight=0); main.columnconfigure(1, weight=1)
    main.rowconfigure(1, weight=1)

    # Header
    hdr = ttk.Frame(main)
    hdr.grid(row=0, column=0, columnspan=2, sticky="ew", pady=(0, 10))
    ttk.Label(hdr, text="🪂  Parachute Simulation", style="Title.TLabel").pack(side="left")
    ttk.Label(hdr, text="  Dark Physics Engine  •  Adjust → Run → Watch",
              style="Sub.TLabel").pack(side="left", padx=12)

    left = ttk.Frame(main); left.grid(row=1, column=0, sticky="nsew", padx=(0, 10))

    # ── Scrollable left panel ─────────────────────────────────────────────
    LEFT_PANEL_WIDTH = 350
    left_canvas = tk.Canvas(left, bg=T.BG_DARK, highlightthickness=0, width=LEFT_PANEL_WIDTH)
    left_scroll = ttk.Scrollbar(left, orient="vertical", command=left_canvas.yview)
    left_inner = ttk.Frame(left_canvas)
    left_inner.columnconfigure(0, weight=1, minsize=LEFT_PANEL_WIDTH - 20)
    left_inner.bind("<Configure>", lambda e: left_canvas.configure(scrollregion=left_canvas.bbox("all")))
    left_canvas.create_window((0, 0), window=left_inner, anchor="nw", tags="inner_win")
    left_canvas.configure(yscrollcommand=left_scroll.set)
    left_canvas.pack(side="left", fill="both", expand=True)
    left_scroll.pack(side="right", fill="y")
    # Ensure inner frame fills canvas width
    def _on_canvas_configure(e):
        left_canvas.itemconfig("inner_win", width=e.width)
    left_canvas.bind("<Configure>", _on_canvas_configure)
    # Mouse wheel
    def _on_mousewheel(e):
        left_canvas.yview_scroll(int(-1*(e.delta/120)), "units")
    left_canvas.bind_all("<MouseWheel>", _on_mousewheel)

    # ── Drop Mode ─────────────────────────────────────────────────────────
    SEC_PAD_X = 6      # horizontal padding for each section inside left_inner
    SEC_PAD_Y = (0, 8)  # vertical gap between sections
    INNER_PAD_X = 10    # padding inside each LabelFrame
    INNER_PAD_Y = 4     # row spacing inside each LabelFrame

    mode_frame = ttk.LabelFrame(left_inner, text="  DROP MODE  ", padding=(INNER_PAD_X, 6))
    mode_frame.grid(row=0, column=0, sticky="ew", padx=SEC_PAD_X, pady=SEC_PAD_Y)
    mode_frame.columnconfigure(0, weight=1)
    drop_mode_var = tk.StringVar(value="freefall")
    for i, (txt, val) in enumerate([("🪂  Freefall", "freefall"),
                                      ("✈️  Plane Drop", "plane"),
                                      ("🚁  Helicopter Drop", "helicopter")]):
        ttk.Radiobutton(mode_frame, text=txt, variable=drop_mode_var, value=val
                         ).grid(row=i, column=0, sticky="w", padx=4, pady=INNER_PAD_Y)

    # Vehicle behavior
    veh_frame = ttk.LabelFrame(left_inner, text="  VEHICLE AFTER DROP  ", padding=(INNER_PAD_X, 6))
    veh_frame.grid(row=1, column=0, sticky="ew", padx=SEC_PAD_X, pady=SEC_PAD_Y)
    vehicle_var = tk.StringVar(value="fly_away")
    ttk.Radiobutton(veh_frame, text="✈️  Fly Away", variable=vehicle_var, value="fly_away"
                     ).grid(row=0, column=0, sticky="w", padx=4, pady=INNER_PAD_Y)
    ttk.Radiobutton(veh_frame, text="🔒  Stay / Hover", variable=vehicle_var, value="stay"
                     ).grid(row=1, column=0, sticky="w", padx=4, pady=INNER_PAD_Y)

    # ── Basic Sliders ─────────────────────────────────────────────────────
    sliders_frame = ttk.LabelFrame(left_inner, text="  PARAMETERS  ", padding=(INNER_PAD_X, 6))
    sliders_frame.grid(row=2, column=0, sticky="ew", padx=SEC_PAD_X, pady=SEC_PAD_Y)
    sliders_frame.columnconfigure(0, weight=1)

    defaults = SimulationParams()
    slider_defs = [
        ("Mass (kg)", "m", 40, 150, defaults.m, 1),
        ("Start Height (m)", "h0", 500, 10000, defaults.h0, 100),
        ("Deploy Height (m)", "h_open", 100, 5000, defaults.h_open, 50),
        ("Wind Speed (m/s)", "wind_speed", -30, 30, defaults.wind_speed, 0.5),
        ("Safe Landing (m/s)", "v_safe", 1, 15, defaults.v_safe, 0.5),
    ]
    sliders = {}

    def _make_slider(parent, row, label, key, lo, hi, default, res):
        f = ttk.Frame(parent); f.grid(row=row, column=0, sticky="ew", padx=2, pady=4)
        f.columnconfigure(0, weight=1)
        f.columnconfigure(1, weight=0)
        ttk.Label(f, text=label, foreground=T.TEXT_SECONDARY, font=("Segoe UI", 9)
                   ).grid(row=0, column=0, sticky="w")
        val_lbl = ttk.Label(f, text=f"{default}", foreground=T.ACCENT_CYAN,
                             font=("Segoe UI", 9, "bold"))
        val_lbl.grid(row=0, column=1, sticky="e", padx=(8, 0))
        var = tk.DoubleVar(value=default)
        def _upd(v, lbl=val_lbl, r=res):
            v = float(v)
            lbl.config(text=f"{v:.1f}" if r < 1 else f"{int(v)}")
        sc = ttk.Scale(f, from_=lo, to=hi, orient="horizontal", variable=var, command=_upd)
        sc.grid(row=1, column=0, columnspan=2, sticky="ew", pady=(2, 0))
        sliders[key] = var
        # Wind color hint
        if key == "wind_speed":
            def _wind_color(v, lbl=val_lbl):
                v = float(v)
                if v < 0: lbl.config(foreground=T.ACCENT_MAGENTA)
                elif v > 0: lbl.config(foreground=T.ACCENT_ORANGE)
                else: lbl.config(foreground=T.ACCENT_CYAN)
                lbl.config(text=f"{v:.1f}  {'← Left' if v<0 else '→ Right' if v>0 else '—'}")
            sc.config(command=_wind_color)
            _wind_color(default)

    for i, (lbl, key, lo, hi, val, res) in enumerate(slider_defs):
        _make_slider(sliders_frame, i, lbl, key, lo, hi, val, res)

    # ── Advanced (text entries) ───────────────────────────────────────────
    adv_frame = ttk.LabelFrame(left_inner, text="  ADVANCED  ", padding=(INNER_PAD_X, 6))
    adv_frame.grid(row=3, column=0, sticky="ew", padx=SEC_PAD_X, pady=SEC_PAD_Y)
    adv_frame.columnconfigure(0, weight=1)
    adv_frame.columnconfigure(1, weight=1)
    adv_entries = {}
    for i, (lbl, key) in enumerate([("Cd (freefall)", "Cd_free"), ("Area freefall (m²)", "A_free"),
                                      ("Cd (parachute)", "Cd_para"), ("Area parachute (m²)", "A_para")]):
        ttk.Label(adv_frame, text=lbl, foreground=T.TEXT_SECONDARY, font=("Segoe UI", 9)
                   ).grid(row=i, column=0, sticky="w", padx=(2, 8), pady=3)
        ent = ttk.Entry(adv_frame, width=10)
        ent.insert(0, str(getattr(defaults, key)))
        ent.grid(row=i, column=1, sticky="ew", padx=2, pady=3)
        adv_entries[key] = ent

    # ── Results Card ──────────────────────────────────────────────────────
    res_frame = tk.Frame(left_inner, bg=T.BG_CARD, highlightbackground=T.BORDER,
                          highlightthickness=1, padx=14, pady=10)
    res_frame.grid(row=4, column=0, sticky="ew", padx=SEC_PAD_X, pady=SEC_PAD_Y)
    res_frame.columnconfigure(0, weight=1)
    res_frame.columnconfigure(1, weight=1)
    tk.Label(res_frame, text="📊 RESULTS", bg=T.BG_CARD, fg=T.ACCENT_CYAN,
             font=("Segoe UI", 11, "bold")).grid(row=0, column=0, columnspan=2, sticky="w", pady=(0, 8))

    rvars = {}
    for i, (lbl, key) in enumerate([("Final Speed", "final_speed"), ("Safe Landing", "safe"),
                                      ("Flight Time", "flight_time"), ("Landing X", "landing_x"),
                                      ("Max Speed", "max_speed")], start=1):
        tk.Label(res_frame, text=lbl, bg=T.BG_CARD, fg=T.TEXT_SECONDARY,
                 font=("Segoe UI", 10)).grid(row=i, column=0, sticky="w", pady=3)
        sv = tk.StringVar(value="—")
        l = tk.Label(res_frame, textvariable=sv, bg=T.BG_CARD, fg=T.TEXT_PRIMARY,
                     font=("Segoe UI", 10, "bold"))
        l.grid(row=i, column=1, sticky="e", pady=3)
        rvars[key] = (sv, l)

    # ── Buttons ───────────────────────────────────────────────────────────
    btn_frame = ttk.Frame(left_inner)
    btn_frame.grid(row=5, column=0, sticky="ew", padx=SEC_PAD_X, pady=(4, 8))
    for col in range(4): btn_frame.columnconfigure(col, weight=1)

    # ── Speed slider ──────────────────────────────────────────────────────
    spd_frame = ttk.LabelFrame(left_inner, text="  ANIM SPEED  ", padding=(INNER_PAD_X, 6))
    spd_frame.grid(row=6, column=0, sticky="ew", padx=SEC_PAD_X, pady=(0, 10))
    spd_frame.columnconfigure(0, weight=1)
    anim_speed = tk.DoubleVar(value=10.0)
    spd_lbl = ttk.Label(spd_frame, text="10x", foreground=T.ACCENT_CYAN, font=("Segoe UI", 9, "bold"))
    spd_lbl.grid(row=0, column=0, sticky="e", padx=4)
    def _spd(v): spd_lbl.config(text=f"{int(float(v))}x")
    ttk.Scale(spd_frame, from_=1, to=200, orient="horizontal", variable=anim_speed,
              command=_spd).grid(row=1, column=0, sticky="ew", padx=2, pady=(2, 4))

    # ── Animation Figure (right) ──────────────────────────────────────────
    right_frame = tk.Frame(main, bg=T.BG_PANEL, highlightbackground=T.BORDER, highlightthickness=1,
                            padx=2, pady=2)
    right_frame.grid(row=1, column=1, sticky="nsew")
    right_frame.columnconfigure(0, weight=1); right_frame.rowconfigure(0, weight=1)

    fig = Figure(figsize=(7, 6), dpi=100, facecolor=T.BG_PANEL)
    ax = fig.add_subplot(111)
    ax.set_facecolor(T.SKY_TOP)
    ax.set_xlabel("x (m)", color=T.TEXT_SECONDARY, fontsize=10)
    ax.set_ylabel("height y (m)", color=T.TEXT_SECONDARY, fontsize=10)
    ax.set_title("2D Fall Simulation", color=T.ACCENT_CYAN, fontweight="bold", fontsize=13)
    ax.tick_params(colors=T.TEXT_SECONDARY)
    for spine in ax.spines.values():
        spine.set_color(T.BORDER)
    ax.grid(True, alpha=0.10, color=T.TEXT_SECONDARY, linestyle='--')

    canvas = FigureCanvasTkAgg(fig, master=right_frame)
    canvas.get_tk_widget().grid(row=0, column=0, sticky="nsew")

    # ── Scene elements ────────────────────────────────────────────────────
    # Ground band (drawn first; sky gradient added at reset when we know limits)
    ground_band = ax.axhspan(-500, 0, facecolor=T.GROUND_COLOR, zorder=0)
    ax.axhline(0, color=T.GROUND_LINE, linewidth=2, alpha=0.9, zorder=1)

    # Moon (drawn once, persists)
    moon_patches = T.draw_moon(ax, 0.12, 0.92)

    # Skyline & gradient patch storage (rebuilt on axis change)
    scene_extras = {"skyline": [], "gradient": []}

    # Stars
    star_xs, star_ys, star_sizes = T.STARS
    star_dots = ax.scatter([], [], s=[], c="white", alpha=0.6, zorder=1, marker="*")

    # Clouds (with base positions for drift)
    cloud_patches = []
    cloud_bases = []  # store (base_cx, base_cy, r) for drift animation
    for cx, cy, r in [(-25, defaults.h0*0.85, 6), (-10, defaults.h0*0.92, 4),
                       (15, defaults.h0*0.88, 7), (30, defaults.h0*0.80, 5)]:
        for dx, dy, rf in [(0, 0, 1), (r*0.9, r*0.2, 0.8), (-r*0.9, r*0.1, 0.75)]:
            c = Circle((cx+dx, cy+dy), r*rf, fc="white", ec=None, alpha=0.10, zorder=1)
            ax.add_patch(c)
            cloud_patches.append(c)
            cloud_bases.append((cx+dx, cy+dy, r*rf))

    # Wind arrow
    wind_arrow = FancyArrowPatch((0.78, 0.93), (0.96, 0.93), transform=ax.transAxes,
                                  arrowstyle="-|>", mutation_scale=14, lw=2,
                                  color=T.ACCENT_CYAN, zorder=10)
    ax.add_patch(wind_arrow)
    wind_label = ax.text(0.78, 0.96, "wind: 0.0 m/s", transform=ax.transAxes,
                          color=T.ACCENT_CYAN, fontsize=9, zorder=10)

    # Trail
    (trail_line,) = ax.plot([], [], color=T.ACCENT_CYAN, lw=1.8, alpha=0.6, zorder=2)

    # Velocity arrow
    vel_arrow = FancyArrowPatch((0, 0), (0, 0), arrowstyle="->", mutation_scale=12,
                                 lw=2, color=T.ACCENT_ORANGE, zorder=9)
    ax.add_patch(vel_arrow)

    # ── Stickman parts ────────────────────────────────────────────────────
    head = Ellipse((0, defaults.h0), 1, 1, fc=T.SKIN_COLOR, ec=T.HELMET_COLOR, lw=2, zorder=6)
    helmet = Ellipse((0, defaults.h0), 1, 1, fc=T.HELMET_COLOR, ec=T.ACCENT_CYAN, lw=1.5,
                      alpha=0.7, zorder=7)
    torso_line, = ax.plot([], [], color=T.SUIT_COLOR, lw=4, zorder=6)
    arm_L, = ax.plot([], [], color=T.SUIT_COLOR, lw=3, zorder=6)
    arm_R, = ax.plot([], [], color=T.SUIT_COLOR, lw=3, zorder=6)
    leg_L, = ax.plot([], [], color=T.SUIT_COLOR, lw=3, zorder=6)
    leg_R, = ax.plot([], [], color=T.SUIT_COLOR, lw=3, zorder=6)
    ax.add_patch(head); ax.add_patch(helmet)

    # Eyes
    eye_L = Ellipse((0,0), 0, 0, fc="white", zorder=8); ax.add_patch(eye_L)
    eye_R = Ellipse((0,0), 0, 0, fc="white", zorder=8); ax.add_patch(eye_R)
    pupil_L = Ellipse((0,0), 0, 0, fc="#1a202c", zorder=9); ax.add_patch(pupil_L)
    pupil_R = Ellipse((0,0), 0, 0, fc="#1a202c", zorder=9); ax.add_patch(pupil_R)
    mouth_line, = ax.plot([], [], color="#1a202c", lw=2, zorder=8)

    status_text = ax.text(0.68, 0.86, "", transform=ax.transAxes, fontsize=12,
                           fontweight="bold", color=T.ACCENT_GREEN, zorder=12)

    # ── Parachute ─────────────────────────────────────────────────────────
    canopy = Polygon([[0,0],[0,0],[0,0]], closed=True, fc=T.ACCENT_RED, ec=T.ACCENT_CYAN,
                      lw=2, alpha=0.95, zorder=5)
    ax.add_patch(canopy)
    panel_lines = [ax.plot([], [], lw=1.2, color=c, alpha=0.85, zorder=6)[0] for c in T.CANOPY_COLORS]
    susp_lines = [ax.plot([], [], lw=1.1, color=T.TEXT_SECONDARY, alpha=0.8, zorder=6)[0] for _ in range(8)]
    harness = Rectangle((0,0), 0.8, 0.25, fc=T.BORDER, zorder=6); ax.add_patch(harness)
    for obj in [canopy, harness] + panel_lines + susp_lines:
        if hasattr(obj, 'set_visible'): obj.set_visible(False)

    # Vehicle storage
    vehicle_patches = {"items": [], "lines": []}

    latest_params = {"value": defaults}
    latest_data = {"value": simulate(defaults)}

    anim_state = {"after_id": None, "frame": 0, "running": False, "deploy_idx": 0,
                  "inflation_frames": 1, "landed": False, "landing_safe": False,
                  "post_landing_frame": 0, "landing_idx": 0, "feet_offset": 0.0,
                  "vehicle_x": 0.0, "vehicle_y": 0.0, "vehicle_dropped": False}

    def _clear_vehicle():
        for p in vehicle_patches["items"]:
            p.remove()
        for lns in vehicle_patches["lines"]:
            for l in lns: l.remove()
        vehicle_patches["items"] = []; vehicle_patches["lines"] = []

    def _stop_anim():
        if anim_state["after_id"]:
            try: root.after_cancel(anim_state["after_id"])
            except: pass
            anim_state["after_id"] = None
        anim_state["running"] = False

    def _clear_scene_extras():
        for p in scene_extras["skyline"]:
            try: p.remove()
            except: pass
        scene_extras["skyline"] = []
        # gradient bands are axhspan artists; remove them too
        for p in scene_extras["gradient"]:
            try: p.remove()
            except: pass
        scene_extras["gradient"] = []

    def _update_axes(params, data):
        xs, ys = data[:, 1], data[:, 2]
        xpad = max(15, 0.15*(xs.max()-xs.min()+1e-9))
        ax.set_xlim(xs.min()-xpad, xs.max()+xpad)
        ax.set_ylim(min(-50, float(ys.min())-10), max(params.h0, float(ys.max()))+10)
        # Place stars
        x0, x1 = ax.get_xlim(); y0, y1 = ax.get_ylim()
        sx = x0 + star_xs*(x1-x0); sy = y0 + star_ys*(y1-y0)
        star_dots.set_offsets(np.column_stack([sx, sy]))
        star_dots.set_sizes(star_sizes * 3)

        # Draw sky gradient
        _clear_scene_extras()
        y_range = y1 - y0
        for frac_lo, frac_hi, color in T.SKY_GRADIENT:
            band = ax.axhspan(y0 + frac_lo * y_range, y0 + frac_hi * y_range,
                              facecolor=color, zorder=0, alpha=0.9)
            scene_extras["gradient"].append(band)

        # Draw city skyline
        scene_extras["skyline"] = T.draw_skyline(ax, x0, x1, ground_y=0.0,
                                                  max_height_data=params.h0)

        # Reposition clouds to match new axes scale
        for i, (bcx, bcy, br) in enumerate(cloud_bases):
            if i < len(cloud_patches):
                cloud_patches[i].set_center((bcx, bcy))
                cloud_patches[i].set_radius(br)

    def _reset_anim(params, data):
        _stop_anim(); _clear_vehicle()
        anim_state.update({"frame": 0, "landed": False, "landing_safe": False,
                           "post_landing_frame": 0, "vehicle_dropped": False,
                           "cloud_offset": 0.0})
        anim_state["deploy_idx"] = int(np.argmax(data[:,2] <= params.h_open)) if len(data) else 0
        anim_state["inflation_frames"] = max(1, int(1.5/max(1e-6, params.dt)))
        _update_axes(params, data)

        # Feet offset
        try:
            bbox = ax.get_window_extent(); ah = max(1, bbox.height)
        except: ah = 450.0
        try: y0, y1 = ax.get_ylim(); yr = max(1e-6, abs(y1-y0))
        except: yr = params.h0 + 60
        dppy = yr / ah
        fo = (9+12+20) * dppy
        anim_state["feet_offset"] = fo

        if len(data) > 5:
            gh = np.where(data[5:,2] <= fo)[0]
            anim_state["landing_idx"] = int(gh[0])+5 if len(gh) else len(data)-1
        else:
            anim_state["landing_idx"] = max(0, len(data)-1)

        # Vehicle starting position
        if params.drop_mode == "plane":
            anim_state["vehicle_x"] = float(data[0,1]) - 30
            anim_state["vehicle_y"] = params.h0
        elif params.drop_mode == "helicopter":
            anim_state["vehicle_x"] = float(data[0,1])
            anim_state["vehicle_y"] = params.h0 + 20

        # Reset visuals
        for obj in [canopy, harness, eye_L, eye_R, pupil_L, pupil_R]:
            obj.set_visible(False)
        for ln in panel_lines + susp_lines:
            ln.set_visible(False)
        for ln in [torso_line, arm_L, arm_R, leg_L, leg_R, mouth_line, trail_line]:
            ln.set_data([], [])
        status_text.set_text(""); vel_arrow.set_positions((0,0),(0,0))

        wind_label.set_text(f"wind: {params.wind_speed:.1f} m/s")
        if params.wind_speed >= 0:
            wind_arrow.set_positions((0.78, 0.93), (0.96, 0.93))
            wind_label.set_color(T.ACCENT_ORANGE if params.wind_speed > 0 else T.ACCENT_CYAN)
        else:
            wind_arrow.set_positions((0.96, 0.93), (0.78, 0.93))
            wind_label.set_color(T.ACCENT_MAGENTA)
        wind_arrow.set_color(wind_label.get_color())
        canvas.draw()

    def _tick_anim():
        params = latest_params["value"]; data = latest_data["value"]
        n = len(data)
        if n == 0: anim_state["running"] = False; return

        f = anim_state["frame"]; li = anim_state["landing_idx"]
        fo = anim_state["feet_offset"]

        if f >= li and not anim_state["landed"]:
            anim_state["landed"] = True
            anim_state["landing_safe"] = safe_landing(data, params, ground_y=fo)

        if anim_state["landed"]: f = min(li, n-1)

        x = float(data[min(f,n-1),1]); y = float(data[min(f,n-1),2])
        vx = float(data[min(f,n-1),3]); vy = float(data[min(f,n-1),4])
        if anim_state["landed"] or y < fo: y = fo

        # Pixel conversion
        try:
            bbox = ax.get_window_extent(); awp, ahp = max(1,bbox.width), max(1,bbox.height)
        except: awp, ahp = 500, 450
        try:
            x0l,x1l = ax.get_xlim(); y0l,y1l = ax.get_ylim()
            xr, yr = max(1e-6,abs(x1l-x0l)), max(1e-6,abs(y1l-y0l))
        except: xr, yr = 100, params.h0+60
        dpx, dpy = xr/awp, yr/ahp

        HR=9; TP=12; AL=11; LL=20; SP=10; AH=9; LS=7
        hs = HR*dpy; tl = TP*dpy; al = AL*dpy; ll = LL*dpy
        sw = SP*dpx; adx = AH*dpx; lsp = LS*dpx
        hw, hh = HR*2*dpx, HR*2*dpy

        # Head & helmet
        head.set_center((x,y)); head.set_width(hw); head.set_height(hh); head.set_visible(True)
        helmet.set_center((x, y+hs*0.4)); helmet.set_width(hw*1.1); helmet.set_height(hh*0.6)
        helmet.set_visible(True)

        # Torso
        tt = y - hs; tb = tt - tl
        torso_line.set_data([x,x],[tt,tb]); torso_line.set_visible(True)
        aay = tt

        # Flail
        ft = anim_state["frame"]*0.35
        fady = 7*dpy*np.sin(ft); fbdy = 7*dpy*np.sin(ft+np.pi)
        fldy = 5*dpy*np.sin(ft*0.7)

        if y > params.h_open:
            arm_L.set_data([x-sw*0.3, x-sw-adx], [aay, aay-al*0.75+fady])
            arm_R.set_data([x+sw*0.3, x+sw+adx], [aay, aay-al*0.75+fbdy])
        else:
            arm_L.set_data([x-sw*0.3, x-sw-adx*0.3], [aay, aay-al])
            arm_R.set_data([x+sw*0.3, x+sw+adx*0.3], [aay, aay-al])
        arm_L.set_visible(True); arm_R.set_visible(True)

        hy = tb
        if y > params.h_open:
            leg_L.set_data([x, x-lsp], [hy, hy-ll+fldy])
            leg_R.set_data([x, x+lsp], [hy, hy-ll-fldy])
        else:
            leg_L.set_data([x-lsp*0.4]*2, [hy, hy-ll])
            leg_R.set_data([x+lsp*0.4]*2, [hy, hy-ll])
        leg_L.set_visible(True); leg_R.set_visible(True)

        # Canopy
        ph = (HR*2+TP+LL)*dpy; pw = SP*2*dpx
        cwb = 80*dpx; chb = 35*dpy
        if y <= params.h_open:
            k = max(0, f - anim_state["deploy_idx"])
            infl = min(1.0, k / anim_state["inflation_frames"])
            sway = np.clip((vx-params.wind_speed)*0.05, -0.8, 0.8)*infl
            w = cwb*(0.55+0.55*infl); h = chb*(0.55+0.55*infl)
            cx_c = x + sway; cy_c = y + 1.35*ph + 0.15*ph*infl
            theta = np.linspace(np.pi, 0, 25)
            arc = np.column_stack([cx_c+(w/2)*np.cos(theta), cy_c+h*np.sin(theta)])
            bot = np.array([[cx_c+w/2, cy_c],[cx_c-w/2, cy_c]])
            canopy.set_xy(np.vstack([arc, bot])); canopy.set_visible(True)
            # Rainbow panels
            pt = np.linspace(np.pi*0.1, np.pi*0.9, len(panel_lines))
            for ln, th in zip(panel_lines, pt):
                ln.set_data([cx_c, cx_c+(w/2)*np.cos(th)], [cy_c, cy_c+h*np.sin(th)])
                ln.set_visible(True)
            # Canopy color gradient
            canopy.set_facecolor(T.ACCENT_RED); canopy.set_alpha(0.7)
            # Harness
            hy2 = y + 0.25*ph
            harness.set_width(max(0.8, 1.2*pw)); harness.set_height(max(0.25, 0.06*ph))
            harness.set_xy((x-harness.get_width()/2, hy2)); harness.set_visible(True)
            # Suspension
            caxs = np.linspace(cx_c-0.42*w, cx_c+0.42*w, len(susp_lines))
            haxs = np.linspace(x-0.45*harness.get_width(), x+0.45*harness.get_width(), len(susp_lines))
            for ln, ax2, hx in zip(susp_lines, caxs, haxs):
                ln.set_data([ax2, hx], [cy_c, hy2]); ln.set_visible(True)
        else:
            canopy.set_visible(False); harness.set_visible(False)
            for ln in panel_lines+susp_lines: ln.set_visible(False)

        # Eyes & face
        ew = HR*0.56*dpx; eh = HR*0.56*dpy
        eyo = HR*0.2*dpy; exo = HR*0.38*dpx
        if anim_state["landed"]:
            anim_state["post_landing_frame"] += 1
            if anim_state["landing_safe"]:
                status_text.set_text("✅ SAFE LANDING!"); status_text.set_color(T.ACCENT_GREEN)
                arm_L.set_data([x-sw*0.3, x-sw-adx*0.7], [aay, aay+al*0.9])
                arm_R.set_data([x+sw*0.3, x+sw+adx*0.7], [aay, aay+al*0.9])
                for e, ox in [(eye_L,-exo),(eye_R,exo)]:
                    e.set_center((x+ox,y+eyo)); e.set_width(ew); e.set_height(eh); e.set_visible(True)
                for p, ox in [(pupil_L,-exo),(pupil_R,exo)]:
                    p.set_center((x+ox,y+eyo)); p.set_width(ew*0.5); p.set_height(eh*0.5); p.set_visible(True)
                sh = HR*0.55*dpx; sa = HR*0.25*dpy
                sxs = np.linspace(x-sh, x+sh, 15)
                sys = (y-eyo*1.5) + sa*np.sin(np.linspace(0,np.pi,15))
                mouth_line.set_data(sxs, sys)
            else:
                status_text.set_text("❌ UNSAFE LANDING"); status_text.set_color(T.ACCENT_RED)
                for e,ox in [(eye_L,-exo),(eye_R,exo)]:
                    e.set_center((x+ox,y+eyo)); e.set_width(ew); e.set_height(eh); e.set_visible(True)
                pupil_L.set_visible(False); pupil_R.set_visible(False)
                fxs = np.linspace(x-HR*0.55*dpx, x+HR*0.55*dpx, 15)
                fys = (y-eyo*1.9) - HR*0.25*dpy*np.sin(np.linspace(0,np.pi,15))
                mouth_line.set_data(fxs, fys)
        else:
            for o in [eye_L,eye_R,pupil_L,pupil_R]: o.set_visible(False)
            mouth_line.set_data([],[]); status_text.set_text("")

        trail_line.set_data(data[:min(f+1,n),1], data[:min(f+1,n),2])
        if not anim_state["landed"]:
            vel_arrow.set_positions((x,y),(x+vx*0.25, y+vy*0.25))
        else:
            vel_arrow.set_positions((0,0),(0,0))

        # Vehicle rendering
        _clear_vehicle()
        dm = params.drop_mode
        if dm in ("plane", "helicopter"):
            vb = params.vehicle_behavior
            if dm == "plane":
                if not anim_state["vehicle_dropped"] and f < 5:
                    anim_state["vehicle_dropped"] = False
                else:
                    anim_state["vehicle_dropped"] = True
                if anim_state["vehicle_dropped"] and vb == "fly_away":
                    anim_state["vehicle_x"] += 2.0 * dpx * max(1, int(anim_speed.get()))
                vsx = dpx; vsy = dpy
                ps = T.draw_plane(ax, anim_state["vehicle_x"], anim_state["vehicle_y"], vsx, vsy,
                                   alpha=max(0.2, 1.0 - anim_state["frame"]*0.003) if vb=="fly_away" else 0.85)
                vehicle_patches["items"] = ps
            elif dm == "helicopter":
                if f > 3: anim_state["vehicle_dropped"] = True
                if anim_state["vehicle_dropped"] and vb == "fly_away":
                    anim_state["vehicle_y"] += 1.5 * dpy * max(1, int(anim_speed.get()))
                vsx = dpx; vsy = dpy
                ps, rl, sl = T.draw_helicopter(ax, anim_state["vehicle_x"], anim_state["vehicle_y"],
                                                vsx, vsy,
                                                alpha=max(0.2, 1.0-anim_state["frame"]*0.003) if vb=="fly_away" else 0.85)
                vehicle_patches["items"] = ps
                vehicle_patches["lines"] = [rl, sl]

        # Cloud drift with wind
        wind = params.wind_speed
        if abs(wind) > 0.1:
            anim_state["cloud_offset"] = anim_state.get("cloud_offset", 0.0) + wind * 0.02
            for i, (bcx, bcy, br) in enumerate(cloud_bases):
                if i < len(cloud_patches):
                    cloud_patches[i].set_center((bcx + anim_state["cloud_offset"], bcy))

        canvas.draw()

        if anim_state["landed"]:
            if anim_state["post_landing_frame"] < 200:
                anim_state["after_id"] = root.after(20, _tick_anim)
            else:
                anim_state["running"] = False; anim_state["after_id"] = None
        else:
            step = max(1, int(anim_speed.get()))
            anim_state["frame"] = min(n, anim_state["frame"]+step)
            anim_state["after_id"] = root.after(20, _tick_anim)

    def _start_anim():
        if anim_state["running"]: return
        anim_state["running"] = True
        anim_state["after_id"] = root.after(0, _tick_anim)

    def run_simulation():
        try:
            params = _build_params_from_sliders(sliders, adv_entries, drop_mode_var, vehicle_var)
        except Exception as exc:
            messagebox.showerror("Input Error", str(exc)); return
        data = simulate(params)
        latest_params["value"] = params; latest_data["value"] = data

        if len(data) == 0:
            for k in rvars: rvars[k][0].set("0.00")
        else:
            try:
                bbox = ax.get_window_extent(); ah = max(1, bbox.height)
                y0, y1 = ax.get_ylim(); yr = max(1e-6, abs(y1-y0))
            except: ah = 450; yr = params.h0+60
            dppy = yr/ah; fo = (9+12+20)*dppy
            fv = final_speed(data, ground_y=fo)
            is_safe = fv <= params.v_safe
            rvars["final_speed"][0].set(f"{fv:.2f} m/s")
            rvars["final_speed"][1].config(fg=T.ACCENT_GREEN if is_safe else T.ACCENT_RED)
            rvars["safe"][0].set("✅ YES" if is_safe else "❌ NO")
            rvars["safe"][1].config(fg=T.ACCENT_GREEN if is_safe else T.ACCENT_RED)
            hits = np.where(data[:,2] <= fo)[0]
            idx = hits[0] if len(hits) else -1
            rvars["flight_time"][0].set(f"{data[idx,0]:.2f} s")
            rvars["landing_x"][0].set(f"{data[idx,1]:.2f} m")
            ms = float(np.sqrt(data[:,3]**2+data[:,4]**2).max())
            rvars["max_speed"][0].set(f"{ms:.2f} m/s")

        _reset_anim(params, data); _start_anim()

    # Wire buttons
    ttk.Button(btn_frame, text="▶  Run", style="Run.TButton", command=run_simulation
               ).grid(row=0, column=0, sticky="ew", padx=2)
    ttk.Button(btn_frame, text="⏸  Pause", style="Pause.TButton", command=_stop_anim
               ).grid(row=0, column=1, sticky="ew", padx=2)
    ttk.Button(btn_frame, text="⏹  Reset", style="Reset.TButton",
               command=lambda: _reset_anim(latest_params["value"], latest_data["value"])
               ).grid(row=0, column=2, sticky="ew", padx=2)
    ttk.Button(btn_frame, text="✕  Quit", style="Quit.TButton", command=root.destroy
               ).grid(row=0, column=3, sticky="ew", padx=2)

    _reset_anim(defaults, latest_data["value"])
    root.mainloop()


if __name__ == "__main__":
    launch_ui()
