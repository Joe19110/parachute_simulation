"""
ui/animation.py
---------------
AnimController — owns all animation state and drives the per-frame tick loop.

Usage
-----
    anim = AnimController(root, canvas, ax_f, ax_s, scene_f, scene_s,
                          anim_speed_var, latest_params, latest_data)
    anim.cushion_enabled_fn = cushion_enabled.get   # callable → bool
    anim.reset(params, data)
    anim.start()
"""
import numpy as np
from analysis import safe_landing
from ui.scene import update_axes, reset_scene, update_cushions
from ui.stickman import draw_stickman
import theme as T


class AnimController:
    """Manages animation state and drives the Tkinter after-loop."""

    # ── Construction ──────────────────────────────────────────────────────

    def __init__(
        self,
        root,
        canvas,
        ax_f, ax_s,
        scene_f, scene_s,
        latest_data,
        latest_params,
        cushion_enabled_fn,
        anim_speed_var,
        telemetry=None,
        follow_cam_fn=None,
    ):
        self.root           = root
        self.canvas         = canvas
        self.ax_f           = ax_f
        self.ax_s           = ax_s
        self.scene_f        = scene_f
        self.scene_s        = scene_s
        self.latest_data    = latest_data
        self.latest_params  = latest_params
        self.cushion_enabled_fn = cushion_enabled_fn
        self.anim_speed     = anim_speed_var
        self.telemetry      = telemetry
        self.follow_cam_fn  = follow_cam_fn or (lambda: False)


        self._state = {
            "after_id":           None,
            "frame":              0,
            "running":            False,
            "deploy_idx":         0,
            "inflation_frames":   1,
            "landed":             False,
            "landing_safe":       False,
            "post_landing_frame": 0,
            "landing_idx":        0,
            "feet_offset":        0.0,
            "vehicle_x":          0.0,
            "vehicle_y":          0.0,
            "vehicle_dropped":    False,
            "cloud_offset":       0.0,
            "spin_angle":         0.0,
            "spin_rate":          0.0,
            "was_follow_cam":     False,
        }

    # ── Public API ────────────────────────────────────────────────────────

    def start(self):
        """Start (or resume) the animation loop."""
        if self._state["running"]:
            return
        self._state["running"] = True
        self._state["after_id"] = self.root.after(0, self._tick)

    def stop(self):
        """Pause the animation loop."""
        if self._state["after_id"]:
            try:
                self.root.after_cancel(self._state["after_id"])
            except Exception:
                pass
            self._state["after_id"] = None
        self._state["running"] = False

    def reset(self, params, data):
        """Reset animation to frame 0, rebuild axis limits and backgrounds."""
        self.stop()
        self._clear_vehicle(self.scene_f)
        self._clear_vehicle(self.scene_s)

        st = self._state
        st.update({
            "frame": 0, "landed": False, "landing_safe": False,
            "post_landing_frame": 0, "vehicle_dropped": False,
            "cloud_offset": 0.0,
            "spin_angle": 0.0,
            "spin_rate": np.random.uniform(0.15, 0.35) * np.random.choice([-1, 1]),
        })

        st["deploy_idx"] = (
            int(np.argmax(data[:, 2] <= params.h_open)) if len(data) else 0)
        st["inflation_frames"] = max(1, int(1.5 / max(1e-6, params.dt)))

        # Rebuild both views
        update_axes(self.ax_f, self.scene_f, params, data,
                    horiz_col=1,
                    wind_spd=params.wind_x,
                    wind_label_txt=f"wind X: {params.wind_x:.1f} m/s")
        update_axes(self.ax_s, self.scene_s, params, data,
                    horiz_col=3,
                    wind_spd=params.wind_z,
                    wind_label_txt=f"wind Z: {params.wind_z:.1f} m/s")
        update_cushions(params, self.scene_f, self.scene_s,
                        self.ax_f, self.ax_s,
                        self.cushion_enabled_fn())

        # Compute ground feet offset in data units
        try:
            bbox = self.ax_f.get_window_extent()
            ah   = max(1, bbox.height)
        except Exception:
            ah = 450.0
        try:
            y0l, y1l = self.ax_f.get_ylim()
            yr = max(1e-6, abs(y1l - y0l))
        except Exception:
            yr = params.h0 + 60
        fo = (9 + 12 + 20) * (yr / ah)
        st["feet_offset"] = fo

        if len(data) > 5:
            gh = np.where(data[5:, 2] <= fo)[0]
            st["landing_idx"] = int(gh[0]) + 5 if len(gh) else len(data) - 1
        else:
            st["landing_idx"] = max(0, len(data) - 1)

        # Vehicle starting position
        if params.drop_mode == "plane":
            st["vehicle_x"] = float(data[0, 1]) - 30
            st["vehicle_y"] = params.h0
        elif params.drop_mode == "helicopter":
            st["vehicle_x"] = float(data[0, 1])
            st["vehicle_y"] = params.h0 + 20

        reset_scene(self.scene_f)
        reset_scene(self.scene_s)
        self._render_vehicle(params, 0)
        self.canvas.draw()

    # ── Private: per-frame tick ───────────────────────────────────────────

    def _tick(self):
        params = self.latest_params["value"]
        data   = self.latest_data["value"]
        n = len(data)
        if n == 0:
            self._state["running"] = False
            return

        st = self._state
        f  = st["frame"]
        li = st["landing_idx"]
        fo = st["feet_offset"]

        # Detect touchdown
        if f >= li and not st["landed"]:
            st["landed"]       = True
            st["landing_safe"] = safe_landing(data, params, ground_y=fo)

        if st["landed"]:
            f = min(li, n - 1)
            st["post_landing_frame"] += 1

        fi  = min(f, n - 1)
        x   = float(data[fi, 1]);  y  = float(data[fi, 2])
        z   = float(data[fi, 3])
        vx  = float(data[fi, 4]);  vy = float(data[fi, 5])
        vz  = float(data[fi, 6])

        if st["landed"] or y < fo:
            y = fo

        # Update spin physics
        if not st["landed"]:
            st["spin_angle"] += st["spin_rate"]
            if y > params.h_open:
                # Freefall tumbling - maintain or slightly vary spin
                st["spin_rate"] += np.random.uniform(-0.02, 0.02)
                st["spin_rate"] = np.clip(st["spin_rate"], -0.5, 0.5)
            else:
                # Under canopy - spin decays
                st["spin_rate"] *= 0.96
                # Gentle twist from horizontal flight dynamics
                st["spin_rate"] += (vx * 0.002)

        # Front view (X–Y)
        draw_stickman(self.scene_f, self.ax_f, x, y, (vx, vy), f, params, st)
        self.scene_f["trail_line"].set_data(data[:min(f + 1, n), 1],
                                             data[:min(f + 1, n), 2])

        # Side view (Z–Y)
        draw_stickman(self.scene_s, self.ax_s, z, y, (vz, vy), f, params, st)
        self.scene_s["trail_line"].set_data(data[:min(f + 1, n), 3],
                                             data[:min(f + 1, n), 2])

        if not st["landed"]:
            self.scene_f["vel_arrow"].set_visible(True)
            self.scene_s["vel_arrow"].set_visible(True)
            self.scene_f["vel_arrow"].set_positions((x, y), (x + vx * 0.25, y + vy * 0.25))
            self.scene_s["vel_arrow"].set_positions((z, y), (z + vz * 0.25, y + vy * 0.25))
        else:
            self.scene_f["vel_arrow"].set_visible(False)
            self.scene_s["vel_arrow"].set_visible(False)

        # Dynamic Follow Camera
        is_follow = self.follow_cam_fn()
        if is_follow:
            y_bot = max(-30.0, y - 70.0)
            y_top = max(100.0, y_bot + 130.0)
            self.ax_f.set_xlim(x - 70.0, x + 70.0)
            self.ax_f.set_ylim(y_bot, y_top)
            self.ax_s.set_xlim(z - 70.0, z + 70.0)
            self.ax_s.set_ylim(y_bot, y_top)
            st["was_follow_cam"] = True
        elif st.get("was_follow_cam", False):
            # Restore static limits
            hw = params.h0 * 0.8
            self.ax_f.set_xlim(-hw, hw)
            self.ax_f.set_ylim(-30, max(200, params.h0 + 50))
            self.ax_s.set_xlim(-hw, hw)
            self.ax_s.set_ylim(-30, max(200, params.h0 + 50))
            st["was_follow_cam"] = False

        # Wind Shear visualization
        if getattr(params, "wind_shear", False):
            scale = max(0.0, min(1.0, y / max(1.0, params.h0)))
            wx, wz = params.wind_x * scale, params.wind_z * scale
            for scn, val, prefix in [(self.scene_f, wx, "wind X"), (self.scene_s, wz, "wind Z")]:
                scn["wind_label"].set_text(f"{prefix}: {val:.1f} m/s")
                if val >= 0:
                    scn["wind_arrow"].set_positions((0.78, 0.93), (0.96, 0.93))
                    scn["wind_label"].set_color(T.ACCENT_ORANGE if val > 0 else T.ACCENT_CYAN)
                else:
                    scn["wind_arrow"].set_positions((0.96, 0.93), (0.78, 0.93))
                    scn["wind_label"].set_color(T.ACCENT_MAGENTA)
                scn["wind_arrow"].set_color(scn["wind_label"].get_color())

        # Vehicle rendering (front view only for clarity)
        self._render_vehicle(params, f)

        # Cloud drift
        self._drift_clouds(params)

        self.canvas.draw()
        
        # Telemetry scrubber update
        if self.telemetry is not None and "notebook" in self.telemetry:
            # Check if telemetry tab is selected (index 1) to save rendering time
            if self.telemetry["notebook"].index(self.telemetry["notebook"].select()) == 1:
                cur_time = data[min(n, st["frame"]), 0]
                for scrub in self.telemetry["scrubbers"]:
                    scrub.set_xdata([cur_time, cur_time])
                self.telemetry["canvas"].draw_idle()

        # Schedule next frame or stop
        if st["landed"]:
            if st["post_landing_frame"] < 200:
                st["after_id"] = self.root.after(20, self._tick)
            else:
                st["running"]  = False
                st["after_id"] = None
        else:
            step = max(1, int(self.anim_speed.get()))
            st["frame"]    = min(n, st["frame"] + step)
            st["after_id"] = self.root.after(20, self._tick)

    # ── Private: vehicle rendering ────────────────────────────────────────

    def _render_vehicle(self, params, f):
        """Draw the plane or helicopter in the front view."""
        self._clear_vehicle(self.scene_f)
        dm = params.drop_mode
        if dm not in ("plane", "helicopter"):
            return

        dpx_f, dpy_f = self._front_scale()
        vb  = params.vehicle_behavior
        st  = self._state
        alpha = (max(0.2, 1.0 - st["frame"] * 0.003)
                 if vb == "fly_away" else 0.85)

        if dm == "plane":
            if f >= 5:
                st["vehicle_dropped"] = True
            if st["vehicle_dropped"] and vb == "fly_away":
                st["vehicle_x"] += 2.0 * dpx_f * max(1, int(self.anim_speed.get()))
            ps = T.draw_plane(self.ax_f, st["vehicle_x"], st["vehicle_y"],
                              dpx_f, dpy_f, alpha=alpha)
            self.scene_f["vehicle_patches"]["items"] = ps

        elif dm == "helicopter":
            if f > 3:
                st["vehicle_dropped"] = True
            if st["vehicle_dropped"] and vb == "fly_away":
                st["vehicle_y"] += 1.5 * dpy_f * max(1, int(self.anim_speed.get()))
            ps, rl, sl = T.draw_helicopter(self.ax_f, st["vehicle_x"], st["vehicle_y"],
                                           dpx_f, dpy_f, alpha=alpha)
            self.scene_f["vehicle_patches"]["items"] = ps
            self.scene_f["vehicle_patches"]["lines"] = [rl, sl]

    def _drift_clouds(self, params):
        """Animate cloud drift with wind in both views."""
        wind_mag = max(abs(params.wind_x), abs(params.wind_z))
        if wind_mag <= 0.1:
            return
        self._state["cloud_offset"] = (
            self._state.get("cloud_offset", 0.0) + params.wind_x * 0.02)
        for sc in (self.scene_f, self.scene_s):
            for i, (bcx, bcy, br) in enumerate(sc["cloud_bases"]):
                if i < len(sc["cloud_patches"]):
                    sc["cloud_patches"][i].set_center(
                        (bcx + self._state["cloud_offset"], bcy))

    # ── Private: utilities ────────────────────────────────────────────────

    def _clear_vehicle(self, scene):
        """Remove all vehicle patches and lines from a scene."""
        for p in scene["vehicle_patches"]["items"]:
            p.remove()
        for lns in scene["vehicle_patches"]["lines"]:
            for ln in lns:
                ln.remove()
        scene["vehicle_patches"]["items"] = []
        scene["vehicle_patches"]["lines"] = []

    def _front_scale(self):
        """Return (dpx, dpy) data-units-per-pixel for the front-view axis."""
        try:
            bbox = self.ax_f.get_window_extent()
            awp, ahp = max(1, bbox.width), max(1, bbox.height)
        except Exception:
            awp, ahp = 500, 450
        try:
            x0l, x1l = self.ax_f.get_xlim()
            y0l, y1l = self.ax_f.get_ylim()
            xr = max(1e-6, abs(x1l - x0l))
            yr = max(1e-6, abs(y1l - y0l))
        except Exception:
            xr, yr = 100, 4060
        return xr / awp, yr / ahp
