"""
ui/app.py
---------
Application entry point — builds the root window, lays out the two graphs,
wires all widgets together, and defines the run/auto-jump callbacks.

This module intentionally contains no drawing logic or physics.  It delegates:
  • style setup     → ui.style
  • left panel      → ui.panels
  • matplotlib axes → ui.scene
  • animation loop  → ui.animation.AnimController
  • param reading   → ui.params
  • simulation      → simulator, analysis
"""
import tkinter as tk
from tkinter import ttk, messagebox
import numpy as np
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
from matplotlib.figure import Figure

from constants import SimulationParams
from simulator import simulate, compute_jump_point
from analysis import (final_speed, safe_landing,
                      landing_position, flight_time, max_speed)
import theme as T

from ui.style import configure_styles
from ui.panels import build_left_panel
from ui.scene import build_scene, style_ax
from ui.animation import AnimController
from ui.params import build_params_from_ui


def launch_ui():
    """Create and run the main application window."""
    root = tk.Tk()
    root.title("🪂 Parachute Simulation — 3D Edition")
    root.minsize(1100, 700)
    try:
        root.state("zoomed")
    except Exception:
        pass
    root.configure(bg=T.BG_DARK)

    configure_styles(ttk.Style())

    # ── Root grid ─────────────────────────────────────────────────────────
    main = ttk.Frame(root)
    main.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)
    root.columnconfigure(0, weight=1)
    root.rowconfigure(0, weight=1)
    main.columnconfigure(0, weight=0)   # left panel — fixed width
    main.columnconfigure(1, weight=1)   # right graphs — expands
    main.rowconfigure(1, weight=1)

    # ── Header ────────────────────────────────────────────────────────────
    hdr = ttk.Frame(main)
    hdr.grid(row=0, column=0, columnspan=2, sticky="ew", pady=(0, 10))
    ttk.Label(hdr, text="🪂  Parachute Simulation — 3D Edition",
              style="Title.TLabel").pack(side="left")
    ttk.Label(hdr,
              text="  Front View  +  Side View  •  Adjust → Run → Watch",
              style="Sub.TLabel").pack(side="left", padx=12)

    # ── Scrollable left panel ─────────────────────────────────────────────
    left_outer = ttk.Frame(main)
    left_outer.grid(row=1, column=0, sticky="nsew", padx=(0, 10))

    LEFT_W = 280
    left_canvas = tk.Canvas(left_outer, bg=T.BG_DARK,
                             highlightthickness=0, width=LEFT_W)
    left_scroll  = ttk.Scrollbar(left_outer, orient="vertical",
                                  command=left_canvas.yview)
    left_inner   = ttk.Frame(left_canvas)
    left_inner.columnconfigure(0, weight=1, minsize=LEFT_W - 18)
    left_inner.bind(
        "<Configure>",
        lambda e: left_canvas.configure(scrollregion=left_canvas.bbox("all")))
    left_canvas.create_window((0, 0), window=left_inner,
                               anchor="nw", tags="inner_win")
    left_canvas.configure(yscrollcommand=left_scroll.set)
    left_canvas.pack(side="left", fill="both", expand=True)
    left_scroll.pack(side="right", fill="y")
    left_canvas.bind("<Configure>",
                     lambda e: left_canvas.itemconfig("inner_win", width=e.width))
    left_canvas.bind_all(
        "<MouseWheel>",
        lambda e: left_canvas.yview_scroll(int(-1 * (e.delta / 120)), "units"))

    # Build all left-panel widgets; get back a single flat dict of vars
    w = build_left_panel(left_inner)
    sliders        = w["sliders"]
    adv_entries    = w["adv_entries"]
    speed_entries  = w["speed_entries"]
    target_entries = w["target_entries"]
    drop_mode_var  = w["drop_mode_var"]
    vehicle_var    = w["vehicle_var"]
    shape_var      = w["shape_var"]
    cushion_enabled= w["cushion_enabled"]
    rvars          = w["rvars"]
    anim_speed     = w["anim_speed"]
    jump_x_var     = w["jump_x_var"]
    jump_z_var     = w["jump_z_var"]
    btn_frame      = w["btn_frame"]
    theme_var      = w["theme_var"]
    target_entries = w["target_entries"]

    # ── Right panel: Notebook ───────────────────────────────
    right_frame = tk.Frame(main, bg=T.BG_PANEL,
                           highlightbackground=T.BORDER, highlightthickness=1,
                           padx=2, pady=2)
    right_frame.grid(row=1, column=1, sticky="nsew")
    right_frame.columnconfigure(0, weight=1)
    right_frame.rowconfigure(0, weight=1)

    notebook = ttk.Notebook(right_frame)
    notebook.grid(row=0, column=0, sticky="nsew")

    tab1 = ttk.Frame(notebook)
    tab2 = ttk.Frame(notebook)
    notebook.add(tab1, text="Live View")
    notebook.add(tab2, text="Telemetry")
    tab1.columnconfigure(0, weight=1)
    tab1.rowconfigure(0, weight=1)
    tab2.columnconfigure(0, weight=1)
    tab2.rowconfigure(0, weight=1)

    # Two graphs stacked vertically — saves horizontal space on laptops
    fig = Figure(figsize=(8.5, 8.5), dpi=100, facecolor=T.BG_PANEL)
    fig.subplots_adjust(left=0.09, right=0.97, top=0.95,
                        bottom=0.06, hspace=0.42)
    ax_f = fig.add_subplot(2, 1, 1)   # Front view: X–Y  (top)
    ax_s = fig.add_subplot(2, 1, 2)   # Side  view: Z–Y  (bottom)
    style_ax(ax_f, "Front View (X–Y)", "x (m)")
    style_ax(ax_s, "Side View (Z–Y)",  "z (m)")

    canvas = FigureCanvasTkAgg(fig, master=tab1)
    canvas.get_tk_widget().grid(row=0, column=0, sticky="nsew")

    # Hidden toolbar to enable native pan/zoom without taking up space
    toolbar = NavigationToolbar2Tk(canvas, tab1, pack_toolbar=False)
    toolbar.update()
    toolbar.pan()  # enable pan (left click) and zoom (right click) by default

    # ── Telemetry Tab ────────────────────────────────────────────────────────
    fig_tel = Figure(figsize=(8.5, 8.5), dpi=100, facecolor=T.BG_PANEL)
    fig_tel.subplots_adjust(left=0.1, right=0.95, top=0.95, bottom=0.08, hspace=0.4)
    ax_t1 = fig_tel.add_subplot(3, 1, 1)
    ax_t2 = fig_tel.add_subplot(3, 1, 2, sharex=ax_t1)
    ax_t3 = fig_tel.add_subplot(3, 1, 3, sharex=ax_t1)
    
    for ax_t, title, ylabel in zip([ax_t1, ax_t2, ax_t3], 
                                 ["Altitude", "Speed", "G-Force"], 
                                 ["m", "m/s", "G"]):
        ax_t.set_facecolor(T.BG_CARD)
        ax_t.set_title(title, color=T.TEXT_PRIMARY, fontsize=10)
        ax_t.set_ylabel(ylabel, color=T.TEXT_SECONDARY)
        ax_t.tick_params(colors=T.TEXT_SECONDARY)
        for spine in ax_t.spines.values():
            spine.set_color(T.BORDER)
    ax_t3.set_xlabel("Time (s)", color=T.TEXT_SECONDARY)
    
    line_alt, = ax_t1.plot([], [], color=T.ACCENT_CYAN, lw=2)
    line_spd, = ax_t2.plot([], [], color=T.ACCENT_MAGENTA, lw=2)
    line_gf,  = ax_t3.plot([], [], color=T.ACCENT_ORANGE, lw=2)
    
    scrub1 = ax_t1.axvline(0, color=T.ACCENT_RED, lw=1.5, alpha=0.8)
    scrub2 = ax_t2.axvline(0, color=T.ACCENT_RED, lw=1.5, alpha=0.8)
    scrub3 = ax_t3.axvline(0, color=T.ACCENT_RED, lw=1.5, alpha=0.8)
    
    canvas_tel = FigureCanvasTkAgg(fig_tel, master=tab2)
    canvas_tel.get_tk_widget().grid(row=0, column=0, sticky="nsew")
    toolbar_tel = NavigationToolbar2Tk(canvas_tel, tab2, pack_toolbar=False)
    toolbar_tel.update()
    toolbar_tel.pan()

    telemetry = {
        "axes": (ax_t1, ax_t2, ax_t3),
        "lines": (line_alt, line_spd, line_gf),
        "scrubbers": (scrub1, scrub2, scrub3),
        "canvas": canvas_tel,
        "notebook": notebook
    }

    defaults  = SimulationParams()
    scene_f   = build_scene(ax_f, h0=defaults.h0)
    scene_s   = build_scene(ax_s, h0=defaults.h0)

    # Shared mutable refs passed around by reference (dict wrapping)
    latest_params = {"value": defaults}
    latest_data   = {"value": simulate(defaults)}

    # Immediate visual update for wind speed sliders
    def _update_wind_hud(var_name, scene, prefix):
        def _cb(*args):
            try:
                spd = float(sliders[var_name].get())
            except Exception:
                return
            scene["wind_label"].set_text(f"{prefix}: {spd:.1f} m/s")
            if spd >= 0:
                scene["wind_arrow"].set_positions((0.78, 0.93), (0.96, 0.93))
                scene["wind_label"].set_color(T.ACCENT_ORANGE if spd > 0 else T.ACCENT_CYAN)
            else:
                scene["wind_arrow"].set_positions((0.96, 0.93), (0.78, 0.93))
                scene["wind_label"].set_color(T.ACCENT_MAGENTA)
            scene["wind_arrow"].set_color(scene["wind_label"].get_color())
            canvas.draw_idle()
        return _cb

    sliders["wind_x"].trace_add("write", _update_wind_hud("wind_x", scene_f, "wind X"))
    sliders["wind_z"].trace_add("write", _update_wind_hud("wind_z", scene_s, "wind Z"))

    # ── Animation controller ──────────────────────────────────────────────
    anim = AnimController(
        root, canvas,
        ax_f, ax_s, scene_f, scene_s,
        latest_data, latest_params,
        lambda: cushion_enabled.get(),
        anim_speed,
        telemetry=telemetry,
        follow_cam_fn=lambda: w["follow_cam_var"].get()
    )
    anim.cushion_enabled_fn = cushion_enabled.get

    # ── Callbacks ─────────────────────────────────────────────────────────

    def _on_theme_change(*_):
        T.set_theme(theme_var.get() == "day")
        from ui.scene import apply_theme_to_scene, update_axes
        apply_theme_to_scene(ax_f, scene_f)
        apply_theme_to_scene(ax_s, scene_s)
        p = latest_params["value"]
        d = latest_data["value"]
        if len(d) > 0:
            update_axes(ax_f, scene_f, p, d, 1, p.wind_x, f"wind X: {p.wind_x:.1f} m/s")
            update_axes(ax_s, scene_s, p, d, 3, p.wind_z, f"wind Z: {p.wind_z:.1f} m/s")
        canvas.draw()

    theme_var.trace_add("write", _on_theme_change)

    # Draggable cushion logic
    dragging_cushion = None

    def on_press(event):
        nonlocal dragging_cushion
        if not cushion_enabled.get() or event.xdata is None: return
        try:
            tx = float(target_entries["tx"].get())
            tz = float(target_entries["tz"].get())
            sz_x = float(target_entries["cushion_size_x"].get()) / 2.0
            sz_z = float(target_entries["cushion_size_z"].get()) / 2.0
        except Exception:
            return
            
        if event.inaxes == ax_f and abs(event.xdata - tx) <= sz_x:
            dragging_cushion = "x"
            ax_f.disable_pan = True
        elif event.inaxes == ax_s and abs(event.xdata - tz) <= sz_z:
            dragging_cushion = "z"
            ax_s.disable_pan = True

    def on_motion(event):
        if not dragging_cushion or event.xdata is None: return
        cx = float(event.xdata)
        if dragging_cushion == "x" and event.inaxes == ax_f:
            try: sz_x = float(target_entries["cushion_size_x"].get()) / 2
            except: sz_x = 10.0
            target_entries["tx"].delete(0, tk.END)
            target_entries["tx"].insert(0, str(round(cx, 1)))
            scene_f["cushion_patch"].set_xy([[cx - sz_x, 0], [cx + sz_x, 0], [cx + sz_x*0.8, 4], [cx - sz_x*0.8, 4]])
            scene_f["cushion_label"].set_position((cx, 4))
            canvas.draw_idle()
        elif dragging_cushion == "z" and event.inaxes == ax_s:
            try: sz_z = float(target_entries["cushion_size_z"].get()) / 2
            except: sz_z = 10.0
            target_entries["tz"].delete(0, tk.END)
            target_entries["tz"].insert(0, str(round(cx, 1)))
            scene_s["cushion_patch"].set_xy([[cx - sz_z, 0], [cx + sz_z, 0], [cx + sz_z*0.8, 4], [cx - sz_z*0.8, 4]])
            scene_s["cushion_label"].set_position((cx, 4))
            canvas.draw_idle()

    def on_release(event):
        nonlocal dragging_cushion
        if dragging_cushion:
            if dragging_cushion == "x": ax_f.disable_pan = False
            if dragging_cushion == "z": ax_s.disable_pan = False
            dragging_cushion = None
            _rebuild_sim()

    canvas.mpl_connect('button_press_event', on_press)
    canvas.mpl_connect('motion_notify_event', on_motion)
    canvas.mpl_connect('button_release_event', on_release)

    cushion_enabled.trace_add("write", lambda *_: _rebuild_sim())
    w["drop_mode_var"].trace_add("write", lambda *_: _rebuild_sim())
    w["vehicle_var"].trace_add("write", lambda *_: _rebuild_sim())

    def _get_params():
        """Read current UI state → SimulationParams (raises on bad input)."""
        return build_params_from_ui(
            sliders, adv_entries, drop_mode_var, vehicle_var,
            shape_var, target_entries, speed_entries,
            w["wind_shear_var"], w["follow_cam_var"])

    def _update_results(data, params):
        """Populate the results card from simulation output and update telemetry graphs."""
        if len(data) == 0:
            for k in rvars:
                rvars[k][0].set("0.00")
            return
            
        # Telemetry update
        t = data[:, 0]
        y_data = data[:, 2]
        vx = data[:, 4]
        vy = data[:, 5]
        vz = data[:, 6]
        speed = np.sqrt(vx**2 + vy**2 + vz**2)
        
        dt = np.diff(t, prepend=t[0]+0.01)
        dt = np.where(dt == 0, 0.01, dt)
        ax_a = np.diff(vx, prepend=vx[0]) / dt
        ay_a = np.diff(vy, prepend=vy[0]) / dt
        az_a = np.diff(vz, prepend=vz[0]) / dt
        g_force = np.sqrt(ax_a**2 + (ay_a + 9.81)**2 + az_a**2) / 9.81
        
        telemetry["lines"][0].set_data(t, y_data)
        telemetry["lines"][1].set_data(t, speed)
        telemetry["lines"][2].set_data(t, g_force)
        for ax_ in telemetry["axes"]:
            ax_.relim()
            ax_.autoscale_view()
        telemetry["canvas"].draw_idle()
            
        try:
            bbox = ax_f.get_window_extent()
            ah   = max(1, bbox.height)
            y0l, y1l = ax_f.get_ylim()
            yr   = max(1e-6, abs(y1l - y0l))
        except Exception:
            ah = 450; yr = params.h0 + 60
        fo  = (9 + 12 + 20) * (yr / ah)

        # Physics calculations should evaluate at actual ground (y=0),
        # not the visual "feet offset" which changes with zoom level.
        fv      = final_speed(data, ground_y=0.0)
        is_safe = fv <= params.v_safe
        lx, lz  = landing_position(data, ground_y=0.0)
        
        if cushion_enabled.get():
            try:
                tx = float(target_entries["tx"].get())
                tz = float(target_entries["tz"].get())
                sz_x = float(target_entries["cushion_size_x"].get()) / 2.0
                sz_z = float(target_entries["cushion_size_z"].get()) / 2.0
                # If they land within the cushion, consider it a safe landing
                if abs(lx - tx) <= sz_x and abs(lz - tz) <= sz_z:
                    is_safe = True
            except Exception:
                pass
                
        ft      = flight_time(data, ground_y=0.0)
        ms      = max_speed(data)

        rvars["final_speed"][0].set(f"{fv:.2f} m/s")
        rvars["final_speed"][1].config(
            fg=T.ACCENT_GREEN if is_safe else T.ACCENT_RED)
        rvars["safe"][0].set("✅ YES" if is_safe else "❌ NO")
        rvars["safe"][1].config(
            fg=T.ACCENT_GREEN if is_safe else T.ACCENT_RED)
        rvars["flight_time"][0].set(f"{ft:.2f} s")
        rvars["landing_x"][0].set(f"{lx:.2f} m")
        rvars["landing_z"][0].set(f"{lz:.2f} m")
        rvars["max_speed"][0].set(f"{ms:.2f} m/s")

    def _rebuild_sim(*args):
        try:
            params = _get_params()
        except Exception:
            return
        
        latest_params["value"] = params
        anim.reset(params, latest_data["value"])
        
        if cushion_enabled.get():
            try:
                jx, jz = compute_jump_point(params)
                jump_x_var.set(f"{jx:.1f} m")
                jump_z_var.set(f"{jz:.1f} m")
            except:
                pass
        else:
            jump_x_var.set("—")
            jump_z_var.set("—")
            
        canvas.draw_idle()

    def run_simulation():
        try:
            params = _get_params()
        except Exception as exc:
            messagebox.showerror("Input Error", str(exc))
            return

        data = simulate(params)
        latest_params["value"] = params
        latest_data["value"]   = data

        # Jump-point calculation (when cushion is active)
        if cushion_enabled.get():
            jx, jz = compute_jump_point(params)
            jump_x_var.set(f"{jx:.1f} m")
            jump_z_var.set(f"{jz:.1f} m")
        else:
            jump_x_var.set("—")
            jump_z_var.set("—")

        anim.reset(params, data)
        _update_results(data, params)
        anim.start()

    def auto_jump():
        """Calculate the ideal jump point and re-run the simulation from it."""
        try:
            params = _get_params()
        except Exception as exc:
            messagebox.showerror("Input Error", str(exc))
            return
        if not cushion_enabled.get():
            messagebox.showinfo("Auto-Jump", "Enable the Landing Cushion first.")
            return

        jx, jz = compute_jump_point(params)
        jump_x_var.set(f"{jx:.1f} m")
        jump_z_var.set(f"{jz:.1f} m")
        messagebox.showinfo(
            "Auto-Jump Calculated",
            f"Jump from  X = {jx:.1f} m,  Z = {jz:.1f} m\n"
            f"to land at  X = {params.target_x:.1f} m,  Z = {params.target_z:.1f} m\n\n"
            "Simulation starting from those jump coordinates.",
        )
        params.x0 = jx
        params.z0 = jz
        data = simulate(params)
        latest_params["value"] = params
        latest_data["value"]   = data
        anim.reset(params, data)
        _update_results(data, params)
        anim.start()

    # ── Wire buttons — 2 rows so text never gets clipped ────────────────
    # Reconfigure the frame for 3 equal columns
    for col in range(3):
        btn_frame.columnconfigure(col, weight=1)

    # Row 0: Run | Pause | Reset
    ttk.Button(btn_frame, text="▶  Run",    style="Run.TButton",
               command=run_simulation
               ).grid(row=0, column=0, sticky="ew", padx=2, pady=(0, 3))
    ttk.Button(btn_frame, text="⏸  Pause", style="Pause.TButton",
               command=anim.stop
               ).grid(row=0, column=1, sticky="ew", padx=2, pady=(0, 3))
    ttk.Button(btn_frame, text="⏹  Reset", style="Reset.TButton",
               command=lambda: anim.reset(latest_params["value"],
                                          latest_data["value"])
               ).grid(row=0, column=2, sticky="ew", padx=2, pady=(0, 3))

    # Row 1: Auto-Jump (span 2) | Quit
    ttk.Button(btn_frame, text="🎯 Auto-Jump", style="Jump.TButton",
               command=auto_jump
               ).grid(row=1, column=0, columnspan=2, sticky="ew", padx=2)
    ttk.Button(btn_frame, text="✕  Quit",      style="Quit.TButton",
               command=root.destroy
               ).grid(row=1, column=2, sticky="ew", padx=2)

    # ── Initial render ────────────────────────────────────────────────────
    anim.reset(defaults, latest_data["value"])
    root.mainloop()
