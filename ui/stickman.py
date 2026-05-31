# -*- coding: utf-8 -*-
"""
ui/stickman.py
--------------
Draws the skydiver (stickman body + parachute) on a matplotlib Axes for
one animation frame.

Design goals
~~~~~~~~~~~~
* No creepy googly eyes — replaced by a sleek amber visor slit.
* Orange high-visibility jumpsuit (recognisable skydiver look).
* Freefall: star/arch position with limbs animating + twirl/spin effect.
* Under canopy: arms reaching up to risers, legs dangling together.
* Parachute panel lines drawn correctly (rim → apex for domes;
  vertical cell seams for ram-air; grid for cruciform).
* Side view shows the edge-on / profile shape of the canopy, not a
  copy of the front view.
* Spin simulation: cos(spin_angle) compresses horizontal extents to
  mimic rotation around the vertical axis. Side view is offset by π/2
  so the two views always show orthogonal perspectives.
* Suspension lines gently twist when spinning (drawn as 3-point bent
  lines via mid-point offset).
* Landing: visor colour changes green/red; arms raise or slump.
"""
import numpy as np
from constants import PARACHUTE_SHAPES
import theme as T

# ── Colour overrides ──────────────────────────────────────────────────────────
_SUIT    = "#e67e22"   # vibrant orange high-vis jumpsuit
_BOOT    = "#1a202c"   # dark boots / gloves
_HELMET  = "#2d3748"   # dark slate helmet shell
_VISOR   = "#f39c12"   # amber visor (normal state)
_HARNESS = "#95a5a6"   # grey webbing harness


# ═══════════════════════════════════════════════════════════════════════════════
# Canopy shape renderers
# Each receives: scene, cx_c (horiz centre), cy_c (bottom y of canopy),
#                w (base width), h (base height), is_front (bool)
# ═══════════════════════════════════════════════════════════════════════════════

def _canopy_round(scene, cx_c, cy_c, w, h, is_front):
    """Hemispherical dome — full width in front, thin profile on side."""
    eff_w = w if is_front else w * 0.14
    theta = np.linspace(np.pi, 0, 32)
    arc   = np.column_stack([cx_c + (eff_w / 2) * np.cos(theta),
                              cy_c + h * np.sin(theta)])
    bot   = np.array([[cx_c + eff_w / 2, cy_c],
                      [cx_c - eff_w / 2, cy_c]])
    scene["canopy"].set_xy(np.vstack([arc, bot]))
    scene["canopy"].set_facecolor("#888888")
    scene["canopy"].set_alpha(0.82)


def _canopy_ramair(scene, cx_c, cy_c, w, h, is_front):
    """Rectangular ram-air / parafoil.
    Front: flat wide rectangle.  Side: thin airfoil cross-section.
    """
    if is_front:
        wr, hr = w * 1.18, h * 0.62
        pts = np.array([
            [cx_c - wr / 2, cy_c],
            [cx_c - wr / 2, cy_c + hr],
            [cx_c + wr / 2, cy_c + hr],
            [cx_c + wr / 2, cy_c],
            [cx_c + wr * 0.44, cy_c - hr * 0.20],
            [cx_c - wr * 0.44, cy_c - hr * 0.20],
        ])
    else:
        # Airfoil cross-section viewed edge-on
        cd = w * 0.17   # chord depth (side-view width)
        hr = h * 0.62
        pts = np.array([
            [cx_c - cd * 0.50, cy_c],
            [cx_c - cd * 0.50, cy_c + hr],
            [cx_c + cd * 0.30, cy_c + hr * 0.92],
            [cx_c + cd * 0.50, cy_c],
            [cx_c + cd * 0.35, cy_c - hr * 0.16],
            [cx_c - cd * 0.35, cy_c - hr * 0.12],
        ])
    scene["canopy"].set_xy(pts)
    scene["canopy"].set_facecolor("#888888")
    scene["canopy"].set_alpha(0.84)


def _canopy_cruciform(scene, cx_c, cy_c, w, h, is_front):
    """Cross / cruciform — shown narrow in side view."""
    a = w * 0.32 * (1.0 if is_front else 0.11)
    b = h * 0.52
    pts = np.array([
        [cx_c - a,     cy_c + b],
        [cx_c + a,     cy_c + b],
        [cx_c + a,     cy_c + b * 0.45],
        [cx_c + a * 2, cy_c + b * 0.45],
        [cx_c + a * 2, cy_c - b * 0.18],
        [cx_c + a,     cy_c - b * 0.18],
        [cx_c + a,     cy_c - b * 0.65],
        [cx_c - a,     cy_c - b * 0.65],
        [cx_c - a,     cy_c - b * 0.18],
        [cx_c - a * 2, cy_c - b * 0.18],
        [cx_c - a * 2, cy_c + b * 0.45],
        [cx_c - a,     cy_c + b * 0.45],
    ])
    scene["canopy"].set_xy(pts)
    scene["canopy"].set_facecolor("#888888")
    scene["canopy"].set_alpha(0.84)


def _canopy_annular(scene, cx_c, cy_c, w, h, is_front):
    """Annular / toroidal — narrow ring profile on side view."""
    eff_w = w if is_front else w * 0.14
    theta  = np.linspace(np.pi, 0, 30)
    arc    = np.column_stack([cx_c + (eff_w * 0.65) * np.cos(theta),
                              cy_c + (h * 0.55) * np.sin(theta)])
    inner  = np.column_stack([
        cx_c + (eff_w * 0.22) * np.cos(np.linspace(0, np.pi, 15)),
        cy_c + (h * 0.22) * np.sin(np.linspace(0, np.pi, 15)),
    ])
    bot    = np.array([[cx_c + eff_w * 0.65, cy_c],
                       [cx_c - eff_w * 0.65, cy_c]])
    scene["canopy"].set_xy(np.vstack([arc, bot, inner]))
    scene["canopy"].set_facecolor("#888888")
    scene["canopy"].set_alpha(0.76)


_CANOPY_RENDERERS = {
    "round":     _canopy_round,
    "ramair":    _canopy_ramair,
    "cruciform": _canopy_cruciform,
    "annular":   _canopy_annular,
}


# ═══════════════════════════════════════════════════════════════════════════════
# Panel-line renderers  (called after canopy is drawn)
# ═══════════════════════════════════════════════════════════════════════════════

def _draw_panel_lines(scene, vis, cx_c, cy_c, w, h, is_front):
    """Draw the seam / gore lines on the deployed canopy."""
    lns = scene["panel_lns"]
    n   = len(lns)

    if vis in ("round", "annular"):
        # Lines from skirt rim up to apex
        scale = 0.65 if vis == "annular" else 0.50
        apex_x = cx_c
        apex_y = cy_c + h * (0.55 if vis == "annular" else 1.0)
        eff_hw = w * scale * (1.0 if is_front else 0.14)
        thetas = np.linspace(np.pi * 0.06, np.pi * 0.94, n)
        for ln, th in zip(lns, thetas):
            rim_x = cx_c + eff_hw * np.cos(th)
            ln.set_data([rim_x, apex_x], [cy_c, apex_y])
            ln.set_visible(True)

    elif vis == "ramair":
        if is_front:
            wr, hr = w * 1.18, h * 0.62
            # Vertical cell seams
            for i, ln in enumerate(lns):
                cell_x = cx_c - wr / 2 + wr * i / max(1, n - 1)
                ln.set_data([cell_x, cell_x], [cy_c, cy_c + hr])
                ln.set_visible(True)
        else:
            # Horizontal lines showing cell depth layers
            cd, hr = w * 0.17, h * 0.62
            for i, ln in enumerate(lns):
                hy_l = cy_c + hr * i / max(1, n - 1)
                ln.set_data([cx_c - cd * 0.75, cx_c + cd * 0.75], [hy_l, hy_l])
                ln.set_visible(True)

    elif vis == "cruciform":
        a = w * 0.32 * (1.0 if is_front else 0.11)
        b = h * 0.52
        # Horizontal seams across the arms
        ys = np.linspace(cy_c - b * 0.65, cy_c + b, n)
        for ln, ly in zip(lns, ys):
            ln.set_data([cx_c - a * 2, cx_c + a * 2], [ly, ly])
            ln.set_visible(True)


# ═══════════════════════════════════════════════════════════════════════════════
# Main entry point
# ═══════════════════════════════════════════════════════════════════════════════

def draw_stickman(scene, ax, horiz_val, y, vx_vy, frame, params,
                  anim_state, is_front_view=True):
    """Render the skydiver body and parachute onto *ax* for the current frame.

    Parameters
    ----------
    scene        : dict  – scene dict returned by ui.scene.build_scene()
    ax           : Axes  – target matplotlib axis
    horiz_val    : float – x (front) or z (side) position
    y            : float – altitude
    vx_vy        : tuple – (horizontal_vel, vertical_vel) for this view
    frame        : int   – current animation frame index
    params       : SimulationParams
    anim_state   : dict  – shared mutable state from AnimController
    is_front_view: bool  – True for X-Y front view, False for Z-Y side view
    """
    x      = horiz_val
    vx_c   = vx_vy[0]

    # ── Pixel → data-unit scale ───────────────────────────────────────────
    try:
        bbox      = ax.get_window_extent()
        awp, ahp  = max(1, bbox.width), max(1, bbox.height)
    except Exception:
        awp, ahp  = 500, 400
    try:
        x0l, x1l = ax.get_xlim()
        y0l, y1l = ax.get_ylim()
        xr = max(1e-6, abs(x1l - x0l))
        yr = max(1e-6, abs(y1l - y0l))
    except Exception:
        xr, yr    = 100, params.h0 + 60
    dpx = xr / awp
    dpy = yr / ahp

    # ── Body proportions (pixels) ─────────────────────────────────────────
    HR, TP, AL, LL, SW, AH, LS = 11, 18, 15, 24, 13, 11, 9
    hr  = HR * dpy;  tp = TP * dpy;  al = AL * dpy;  ll = LL * dpy
    sw  = SW * dpx;  adx = AH * dpx; lsp = LS * dpx
    hw  = HR * 2.3 * dpx
    hh  = HR * 3.0 * dpy

    # ── Spin / twirl simulation ───────────────────────────────────────────
    # spin_angle advances each frame (set by AnimController._tick).
    # cos(angle) compresses horizontal extents to simulate rotation.
    # The side view is shifted by π/2 so the two views stay orthogonal.
    spin_angle   = anim_state.get("spin_angle", 0.0)
    angle_offset = 0.0 if is_front_view else np.pi / 2
    h_factor     = np.cos(spin_angle + angle_offset)  # ∈ [-1, 1]

    # Body appears narrower in side view (depth << arm span)
    if is_front_view:
        body_xs  = abs(h_factor)
        limb_dir = 1 if h_factor >= 0 else -1   # flip L/R when seen from behind
    else:
        body_xs  = max(0.08, abs(h_factor) * 0.30)
        limb_dir = 1

    eff_sw  = sw  * body_xs
    eff_adx = adx * body_xs
    eff_lsp = lsp * body_xs

    freefall = y > params.h_open

    # ── Head (helmet) ─────────────────────────────────────────────────────
    head = scene["head"]
    head.set_center((x, y))
    head.set_width(hw * (body_xs if is_front_view else max(0.18, body_xs * 0.6 + 0.15)))
    head.set_height(hh)
    head.set_facecolor(_HELMET)
    head.set_edgecolor("#4a90d9")
    head.set_linewidth(1.2)
    head.set_visible(True)

    # ── Visor (replaces googly eyes) ──────────────────────────────────────
    visor     = scene["helmet"]
    visor_w   = hw * 0.72 * (body_xs if is_front_view else max(0.14, body_xs * 0.5 + 0.10))
    visor_col = _VISOR   # updated on landing
    visor.set_center((x, y - hh * 0.12))
    visor.set_width(visor_w)
    visor.set_height(hh * 0.36)
    visor.set_facecolor(visor_col)
    visor.set_edgecolor("#e67e22")
    visor.set_linewidth(0.9)
    visor.set_alpha(0.82)
    visor.set_visible(True)

    # Eyes / pupils / mouth — permanently hidden (replaced by visor)
    for obj in (scene["eye_L"], scene["eye_R"],
                scene["pupil_L"], scene["pupil_R"]):
        obj.set_visible(False)
    scene["mouth_l"].set_data([], [])
    scene["status_text"].set_text("")

    # ── Torso ─────────────────────────────────────────────────────────────
    tt = y - hr           # top of torso (below helmet)
    tb = tt - tp          # bottom of torso (hip level)
    torso_width = max(1.5, 6.0 * (body_xs if is_front_view else body_xs * 0.5 + 0.06))
    scene["torso_l"].set_data([x, x], [tt, tb])
    scene["torso_l"].set_color(_SUIT)
    scene["torso_l"].set_linewidth(torso_width)
    scene["torso_l"].set_solid_capstyle("round")
    scene["torso_l"].set_visible(True)
    aay = tt  # shoulder/arm anchor y

    # ── Limb animations ───────────────────────────────────────────────────
    ft = frame * 0.30
    spin_flail = spin_angle * 1.8  # limbs flail in sync with spin

    if freefall:
        # Star / arch freefall position — limbs flair to sides with spin flail
        fy1 = 5 * dpy * np.sin(ft + spin_flail)       * body_xs
        fy2 = 5 * dpy * np.sin(ft + spin_flail + np.pi) * body_xs
        fly = 4 * dpy * np.sin(ft * 0.8 + spin_angle) * body_xs
        scene["arm_L"].set_data(
            [x - eff_sw * 0.25, x - eff_sw * limb_dir - eff_adx],
            [aay, aay - al * 0.45 + fy1])
        scene["arm_R"].set_data(
            [x + eff_sw * 0.25, x + eff_sw * limb_dir + eff_adx],
            [aay, aay - al * 0.45 + fy2])
        scene["leg_L"].set_data(
            [x - eff_lsp * 0.3, x - eff_lsp * 1.3],
            [tb,  tb - ll + fly])
        scene["leg_R"].set_data(
            [x + eff_lsp * 0.3, x + eff_lsp * 1.3],
            [tb,  tb - ll - fly])
    else:
        # Under canopy — arms reach UP to grab risers, legs hang together
        scene["arm_L"].set_data(
            [x - eff_sw * 0.20, x - eff_sw * 0.70],
            [aay, aay + al * 0.90])
        scene["arm_R"].set_data(
            [x + eff_sw * 0.20, x + eff_sw * 0.70],
            [aay, aay + al * 0.90])
        scene["leg_L"].set_data(
            [x - eff_lsp * 0.25, x - eff_lsp * 0.35],
            [tb, tb - ll * 0.88])
        scene["leg_R"].set_data(
            [x + eff_lsp * 0.25, x + eff_lsp * 0.35],
            [tb, tb - ll * 0.88])

    for part in ("arm_L", "arm_R", "leg_L", "leg_R"):
        scene[part].set_color(_SUIT)
        scene[part].set_linewidth(max(1.2, 4.5 * body_xs))
        scene[part].set_solid_capstyle("round")
        scene[part].set_visible(True)

    # ── Parachute canopy + rigging ────────────────────────────────────────
    ph  = (HR * 2.3 + TP + LL) * dpy   # total body height (px → data)
    pw  = SW * 2 * dpx
    cwb = 115 * dpx                     # base canopy width
    chb =  52 * dpy                     # base canopy height

    if not freefall:
        k    = max(0, frame - anim_state["deploy_idx"])
        infl = min(1.0, k / anim_state["inflation_frames"])

        # Sway with wind
        sway = np.clip((vx_c - params.wind_x) * 0.05, -0.8, 0.8) * infl
        w    = cwb * (0.55 + 0.55 * infl)
        h    = chb * (0.55 + 0.55 * infl)
        cx_c = x + sway
        cy_c = y + 1.38 * ph + 0.16 * ph * infl

        # Draw canopy shape
        shape_key = params.parachute_shape
        _, _, _, _, vis = PARACHUTE_SHAPES.get(shape_key, PARACHUTE_SHAPES["Round"])
        renderer = _CANOPY_RENDERERS.get(vis, _canopy_round)
        renderer(scene, cx_c, cy_c, w, h, is_front_view)
        scene["canopy"].set_visible(True)

        # Panel lines (shape + view aware)
        _draw_panel_lines(scene, vis, cx_c, cy_c, w, h, is_front_view)

        # ── Harness ───────────────────────────────────────────────────────
        hy2      = y + 0.30 * ph
        h_width  = max(0.8, 1.5 * pw * body_xs)
        h_height = max(0.25, 0.07 * ph)
        scene["harness"].set_width(h_width)
        scene["harness"].set_height(h_height)
        scene["harness"].set_xy((x - h_width / 2, hy2))
        scene["harness"].set_facecolor(_HARNESS)
        scene["harness"].set_visible(True)

        # ── Suspension lines ──────────────────────────────────────────────
        # Top attachment: spread across the canopy skirt
        # Bottom attachment: spread across the harness
        n_s = len(scene["susp_lns"])
        if vis == "ramair":
            eff_can_w = w * 1.18 * (0.44 if is_front_view else 0.10)
        elif vis == "annular":
            eff_can_w = w * 0.65 * (1.00 if is_front_view else 0.14)
        else:
            eff_can_w = w      * (0.50 if is_front_view else 0.07)

        top_xs = np.linspace(cx_c - eff_can_w, cx_c + eff_can_w, n_s)
        bot_xs = np.linspace(x - h_width * 0.45, x + h_width * 0.45, n_s)

        # Twist: when spinning under canopy, lines bow sideways
        spin_rate = anim_state.get("spin_rate", 0.0)
        twist_amp = np.sin(spin_angle) * (eff_can_w * 0.30) * min(1.0, spin_rate / 0.04)

        for ln, tx, bx in zip(scene["susp_lns"], top_xs, bot_xs):
            # Mid-point displaced to simulate line twist
            rel   = (tx - cx_c) / max(1e-9, eff_can_w)   # normalised position
            mid_x = (tx + bx) / 2 + twist_amp * rel
            mid_y = (cy_c + hy2) / 2
            ln.set_data([tx, mid_x, bx], [cy_c, mid_y, hy2])
            ln.set_color("#555555")
            ln.set_linewidth(0.85)
            ln.set_visible(True)

    else:
        # Freefall — hide everything above the body
        scene["canopy"].set_visible(False)
        scene["harness"].set_visible(False)
        for ln in scene["panel_lns"] + scene["susp_lns"]:
            ln.set_visible(False)

    # ── Landing pose and visor colour ─────────────────────────────────────
    if anim_state["landed"]:
        _draw_landing_pose(scene, x, aay, eff_sw, eff_adx, al,
                           anim_state["landing_safe"])


def _draw_landing_pose(scene, x, aay, eff_sw, eff_adx, al, is_safe):
    """Update pose and visor for post-landing expression."""
    if is_safe:
        scene["status_text"].set_text("[ SAFE LANDING! ]")
        scene["status_text"].set_color(T.ACCENT_GREEN)
        # Arms raised in V — victory
        scene["arm_L"].set_data(
            [x - eff_sw * 0.20, x - eff_sw * 0.85 - eff_adx * 0.55],
            [aay, aay + al * 1.05])
        scene["arm_R"].set_data(
            [x + eff_sw * 0.20, x + eff_sw * 0.85 + eff_adx * 0.55],
            [aay, aay + al * 1.05])
        # Visor glows green
        scene["helmet"].set_facecolor("#27ae60")
        scene["helmet"].set_edgecolor("#2ecc71")
    else:
        scene["status_text"].set_text("[ HARD LANDING! ]")
        scene["status_text"].set_color(T.ACCENT_RED)
        # Arms slumped down
        scene["arm_L"].set_data(
            [x - eff_sw * 0.20, x - eff_sw * 1.10],
            [aay, aay - al * 0.35])
        scene["arm_R"].set_data(
            [x + eff_sw * 0.20, x + eff_sw * 1.10],
            [aay, aay - al * 0.35])
        # Visor glows red
        scene["helmet"].set_facecolor("#c0392b")
        scene["helmet"].set_edgecolor("#e74c3c")
