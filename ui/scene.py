"""
ui/scene.py
-----------
Matplotlib scene construction and per-frame axis management.

Public API
~~~~~~~~~~
build_scene(ax, h0)          → scene dict with all persistent artists
style_ax(ax, title, xlabel)  → apply dark style to an axis
update_axes(...)             → rescale limits, rebuild sky/skyline/stars
reset_scene(scene)           → hide / clear all animated artists
clear_scene_extras(scene)    → remove gradient bands and skyline patches
update_cushions(...)         → show/hide the green landing-pad ellipses
"""
import numpy as np
from matplotlib.patches import Circle, Ellipse, Rectangle, Polygon, FancyArrowPatch
import theme as T


# ── Axis styling ─────────────────────────────────────────────────────────────

def style_ax(ax, title, xlabel):
    """Apply the dark futuristic look to one matplotlib Axes."""
    ax.set_facecolor(T.SKY_TOP)
    ax.set_xlabel(xlabel, color=T.TEXT_SECONDARY, fontsize=10)
    ax.set_ylabel("Height y (m)", color=T.TEXT_SECONDARY, fontsize=10)
    ax.set_title(title, color=T.ACCENT_CYAN, fontweight="bold", fontsize=12)
    ax.tick_params(colors=T.TEXT_SECONDARY)
    for spine in ax.spines.values():
        spine.set_color(T.BORDER)
    ax.grid(True, alpha=0.10, color=T.TEXT_SECONDARY, linestyle="--")

    # Lock panning to horizontal only (X axis)
    original_drag_pan = ax.drag_pan
    def locked_drag_pan(button, key, x, y):
        if getattr(ax, "disable_pan", False):
            return
        return original_drag_pan(button, "x", x, y)
    ax.drag_pan = locked_drag_pan


# ── Scene construction ────────────────────────────────────────────────────────

def build_scene(ax, h0=4000.0):
    """Create all persistent matplotlib artists for one view axis.

    Returns a flat dict keyed by artist name so callers never need to
    remember positional indices.
    """
    # Ground
    ground_band = ax.axhspan(-500, 0, facecolor=T.GROUND_COLOR, zorder=0)
    ground_line = ax.axhline(0, color=T.GROUND_LINE, linewidth=2, alpha=0.9, zorder=1)

    # Celestial
    moon_p    = T.draw_moon(ax, 0.12, 0.92)
    star_xs, star_ys, star_sizes = T.STARS
    star_dots = ax.scatter(star_xs, star_ys, s=star_sizes * 4, c="white", alpha=0.6,
                           zorder=1, marker="*", transform=ax.transAxes)
    if T.IS_DAY:
        star_dots.set_visible(False)

    # Clouds (positioned relative to h0 so they appear near the top)
    cloud_patches, cloud_bases = [], []
    for cx, cy_frac, r in [(-25, 0.85, 6), (-10, 0.92, 4),
                            ( 15, 0.88, 7), ( 30, 0.80, 5)]:
        cy = h0 * cy_frac
        for dx, dy_frac, rf in [(0, 0, 1), (r*0.9, r*0.2, 0.8), (-r*0.9, r*0.1, 0.75)]:
            c = Circle((cx + dx, cy + dy_frac), r * rf,
                       fc="white", ec=None, alpha=0.10, zorder=1)
            if not T.IS_DAY:
                c.set_visible(False)
            ax.add_patch(c)
            cloud_patches.append(c)
            cloud_bases.append((cx + dx, cy + dy_frac, r * rf))

    # Screen-sticky sky gradient
    gradient_bands = []
    for frac_lo, frac_hi, color in T.SKY_GRADIENT:
        band = Rectangle((0, frac_lo), 1, frac_hi - frac_lo, transform=ax.transAxes,
                         facecolor=color, zorder=0, alpha=0.95)
        ax.add_patch(band)
        gradient_bands.append(band)

    # Wind indicator
    wind_arrow = FancyArrowPatch(
        (0.78, 0.93), (0.96, 0.93),
        transform=ax.transAxes,
        arrowstyle="-|>", mutation_scale=14, lw=2,
        color=T.ACCENT_CYAN, zorder=10,
    )
    ax.add_patch(wind_arrow)
    wind_label = ax.text(
        0.78, 0.96, "wind: 0.0 m/s",
        transform=ax.transAxes, color=T.ACCENT_CYAN, fontsize=9, zorder=10,
    )

    # Trajectory trail + velocity arrow
    (trail_line,) = ax.plot([], [], color=T.ACCENT_CYAN, lw=1.8, alpha=0.6, zorder=2)
    vel_arrow = FancyArrowPatch(
        (0, 0), (0, 0),
        arrowstyle="->", mutation_scale=12, lw=2,
        color=T.ACCENT_CYAN, zorder=9,
    )
    ax.add_patch(vel_arrow)

    # ── Stickman body parts ───────────────────────────────────────────────
    head    = Ellipse((0, 0), 1, 1, fc=T.SKIN_COLOR,   ec=T.HELMET_COLOR, lw=2,   zorder=6)
    helmet  = Ellipse((0, 0), 1, 1, fc=T.HELMET_COLOR, ec=T.ACCENT_CYAN,  lw=1.5,
                      alpha=0.7, zorder=7)
    for patch in (head, helmet):
        ax.add_patch(patch)

    torso_l, = ax.plot([], [], color=T.SUIT_COLOR, lw=4, zorder=6)
    arm_L,   = ax.plot([], [], color=T.SUIT_COLOR, lw=3, zorder=6)
    arm_R,   = ax.plot([], [], color=T.SUIT_COLOR, lw=3, zorder=6)
    leg_L,   = ax.plot([], [], color=T.SUIT_COLOR, lw=3, zorder=6)
    leg_R,   = ax.plot([], [], color=T.SUIT_COLOR, lw=3, zorder=6)

    # Face
    eye_L   = Ellipse((0, 0), 0, 0, fc="white",   zorder=8)
    eye_R   = Ellipse((0, 0), 0, 0, fc="white",   zorder=8)
    pupil_L = Ellipse((0, 0), 0, 0, fc="#1a202c", zorder=9)
    pupil_R = Ellipse((0, 0), 0, 0, fc="#1a202c", zorder=9)
    for patch in (eye_L, eye_R, pupil_L, pupil_R):
        ax.add_patch(patch)
    mouth_l, = ax.plot([], [], color="#1a202c", lw=2, zorder=8)

    status_text = ax.text(
        0.52, 0.86, "",
        transform=ax.transAxes,
        fontsize=11, fontweight="bold",
        color=T.ACCENT_GREEN, zorder=12,
    )

    # ── Parachute canopy + rigging ────────────────────────────────────────
    canopy    = Polygon([[0, 0], [0, 0], [0, 0]], closed=True,
                        fc=T.ACCENT_RED, ec="#000000", lw=2, alpha=0.95, zorder=5)
    ax.add_patch(canopy)
    panel_lns = [
        ax.plot([], [], lw=1.2, color="#000000", alpha=0.85, zorder=6)[0]
        for _ in T.CANOPY_COLORS
    ]
    susp_lns  = [
        ax.plot([], [], lw=1.1, color="#555555", alpha=0.8, zorder=6)[0]
        for _ in range(8)
    ]
    harness = Rectangle((0, 0), 0.8, 0.25, fc=T.BORDER, zorder=6)
    ax.add_patch(harness)

    # ── Landing cushion (inflatable pad) ──────────────────────────────────
    cushion_patch = Polygon(
        [[0, 0], [0, 0], [0, 0]], closed=True,
        fc=T.ACCENT_GREEN, ec="#2ecc71", lw=2, alpha=0.5, zorder=3,
    )
    ax.add_patch(cushion_patch)
    cushion_patch.set_visible(False)
    cushion_label = ax.text(0, 0, "[ SAFE ZONE ]", fontsize=11, fontweight="bold",
                            color=T.ACCENT_GREEN, ha="center", va="bottom", zorder=4)
    cushion_label.set_visible(False)
    
    # Off-screen indicator
    cushion_arrow = ax.text(0.5, 0.05, "", transform=ax.transAxes, fontsize=12,
                            fontweight="bold", color=T.ACCENT_GREEN, zorder=15)
    cushion_arrow.set_visible(False)

    # Start all animated objects hidden
    for obj in (canopy, harness, eye_L, eye_R, pupil_L, pupil_R):
        obj.set_visible(False)
    for ln in panel_lns + susp_lns:
        ln.set_visible(False)

    return {
        # Background
        "ground_band":   ground_band,
        "ground_line":   ground_line,
        "moon":          moon_p,
        "star_dots":     star_dots,
        "cloud_patches": cloud_patches,
        "cloud_bases":   cloud_bases,
        # Wind HUD
        "wind_arrow":    wind_arrow,
        "wind_label":    wind_label,
        # Trail + velocity
        "trail_line":    trail_line,
        "vel_arrow":     vel_arrow,
        # Stickman body
        "head":          head,
        "helmet":        helmet,
        "torso_l":       torso_l,
        "arm_L":         arm_L,
        "arm_R":         arm_R,
        "leg_L":         leg_L,
        "leg_R":         leg_R,
        # Face
        "eye_L":         eye_L,
        "eye_R":         eye_R,
        "pupil_L":       pupil_L,
        "pupil_R":       pupil_R,
        "mouth_l":       mouth_l,
        "status_text":   status_text,
        # Canopy
        "canopy":        canopy,
        "panel_lns":     panel_lns,
        "susp_lns":      susp_lns,
        "harness":       harness,
        # Landing pad
        "cushion_patch": cushion_patch,
        "cushion_label": cushion_label,
        "cushion_arrow": cushion_arrow,
        # Mutable extras (rebuilt each reset)
        "scene_extras":     {"skyline": [], "gradient": gradient_bands},
        "vehicle_patches":  {"items": [], "lines": []},
    }


# ── Per-reset helpers ─────────────────────────────────────────────────────────

def apply_theme_to_scene(ax, scene):
    """Update facecolors and background patches when the day/night theme changes."""
    ax.set_facecolor(T.SKY_TOP)
    scene["ground_band"].set_facecolor(T.GROUND_COLOR)
    scene["ground_line"].set_color(T.GROUND_LINE)
    
    # Redraw moon/sun
    for p in scene["moon"]:
        if p is not None:
            p.remove()
    scene["moon"] = T.draw_moon(ax, 0.12, 0.92)

    # Redraw gradient
    for band in scene["scene_extras"]["gradient"]:
        band.remove()
    scene["scene_extras"]["gradient"] = []
    for frac_lo, frac_hi, color in T.SKY_GRADIENT:
        band = Rectangle((0, frac_lo), 1, frac_hi - frac_lo, transform=ax.transAxes,
                         facecolor=color, zorder=0, alpha=0.95)
        ax.add_patch(band)
        scene["scene_extras"]["gradient"].append(band)

    # Toggle celestial elements based on day/night
    scene["star_dots"].set_visible(not T.IS_DAY)
    for c in scene["cloud_patches"]:
        c.set_visible(T.IS_DAY)

def clear_scene_extras(scene):
    """Remove city-skyline patches from a scene."""
    for p in scene["scene_extras"]["skyline"]:
        try:
            p.remove()
        except Exception:
            pass
    scene["scene_extras"]["skyline"] = []


def update_axes(ax, scene, params, data, horiz_col, wind_spd, wind_label_txt):
    """Rescale axis limits and rebuild all background elements for one view.

    Parameters
    ----------
    horiz_col     : int   – column index for the horizontal axis (1=x, 3=z)
    wind_spd      : float – signed wind speed for arrow direction
    wind_label_txt: str   – text shown next to the wind arrow
    """
    ys = data[:, 2]
    hs = data[:, horiz_col]
    hpad = max(15, 0.15 * (hs.max() - hs.min() + 1e-9))
    ax.set_xlim(hs.min() - hpad, hs.max() + hpad)
    ax.set_ylim(
        min(-50, float(ys.min()) - 10),
        max(params.h0, float(ys.max())) + 150,
    )

    x0, x1 = ax.get_xlim()
    y0, y1 = ax.get_ylim()

    # City skyline
    clear_scene_extras(scene)
    scene["scene_extras"]["skyline"] = T.draw_skyline(
        ax, x0, x1, ground_y=0.0, max_height_data=params.h0)

    # Reposition cloud patches to match rescaled axes
    for i, (bcx, bcy, br) in enumerate(scene["cloud_bases"]):
        if i < len(scene["cloud_patches"]):
            scene["cloud_patches"][i].set_center((bcx, bcy))
            scene["cloud_patches"][i].set_radius(br)

    # Wind HUD
    scene["wind_label"].set_text(wind_label_txt)
    if wind_spd >= 0:
        scene["wind_arrow"].set_positions((0.78, 0.93), (0.96, 0.93))
        scene["wind_label"].set_color(
            T.ACCENT_ORANGE if wind_spd > 0 else T.ACCENT_CYAN)
    else:
        scene["wind_arrow"].set_positions((0.96, 0.93), (0.78, 0.93))
        scene["wind_label"].set_color(T.ACCENT_MAGENTA)
    scene["wind_arrow"].set_color(scene["wind_label"].get_color())


def reset_scene(scene):
    """Hide/clear all animated artists back to their idle state."""
    for obj in (scene["head"], scene["helmet"],
                scene["canopy"], scene["harness"],
                scene["eye_L"], scene["eye_R"],
                scene["pupil_L"], scene["pupil_R"]):
        obj.set_visible(False)
    for ln in scene["panel_lns"] + scene["susp_lns"]:
        ln.set_visible(False)
    for ln in (scene["torso_l"], scene["arm_L"], scene["arm_R"],
               scene["leg_L"],  scene["leg_R"],  scene["mouth_l"],
               scene["trail_line"]):
        ln.set_data([], [])
    scene["status_text"].set_text("")
    scene["vel_arrow"].set_positions((0, 0), (0, 0))


def update_cushions(params, scene_f, scene_s, ax_f, ax_s, enabled):
    """Show or hide the green landing-cushion ellipses on both views.

    When enabled, the front view cushion is centred at target_x and the
    side view cushion is centred at target_z — both at ground level y=0.
    """
    if not enabled:
        for sc in (scene_f, scene_s):
            sc["cushion_patch"].set_visible(False)
            sc["cushion_label"].set_visible(False)
            sc["cushion_arrow"].set_visible(False)
        return

    for ax_ref, sc, hval, pad_hw in [
        (ax_f, scene_f, params.target_x, getattr(params, 'cushion_size_x', 20.0) / 2.0),
        (ax_s, scene_s, params.target_z, getattr(params, 'cushion_size_z', 20.0) / 2.0),
    ]:
        x0, x1 = ax_ref.get_xlim()
        pad_h  = max(15, params.h0 * 0.015)  # height of the inflatable
        
        # Check if off-screen
        if hval < x0:
            sc["cushion_arrow"].set_text("← SAFE ZONE")
            sc["cushion_arrow"].set_position((0.02, 0.05))
            sc["cushion_arrow"].set_horizontalalignment("left")
            sc["cushion_arrow"].set_visible(True)
        elif hval > x1:
            sc["cushion_arrow"].set_text("SAFE ZONE →")
            sc["cushion_arrow"].set_position((0.98, 0.05))
            sc["cushion_arrow"].set_horizontalalignment("right")
            sc["cushion_arrow"].set_visible(True)
        else:
            sc["cushion_arrow"].set_visible(False)

        # Draw a trapezoidal inflatable cushion sitting on the ground
        pts = np.array([
            [hval - pad_hw, 0],
            [hval + pad_hw, 0],
            [hval + pad_hw * 0.9, pad_h],
            [hval - pad_hw * 0.9, pad_h],
        ])
        sc["cushion_patch"].set_xy(pts)
        sc["cushion_patch"].set_visible(True)
        sc["cushion_label"].set_position((hval, pad_h + 2))
        sc["cushion_label"].set_visible(True)
