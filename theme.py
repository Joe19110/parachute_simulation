"""Dark futuristic theme constants and drawing helpers."""
import numpy as np

# ── Color Palette ──────────────────────────────────────────────────────────
BG_DARK      = "#0d1117"
BG_PANEL     = "#161b22"
BG_CARD      = "#1c2333"
BG_INPUT     = "#21262d"
BORDER       = "#30363d"
TEXT_PRIMARY  = "#e6edf3"
TEXT_SECONDARY= "#8b949e"
ACCENT_CYAN   = "#00d4ff"
ACCENT_GREEN  = "#00ff88"
ACCENT_ORANGE = "#ff6b35"
ACCENT_RED    = "#ff4757"
ACCENT_MAGENTA= "#bd00ff"
ACCENT_YELLOW = "#ffd60a"
ACCENT_BLUE   = "#58a6ff"

# Default to night mode
IS_DAY       = False
SKY_TOP      = "#0b0e1a"
SKY_MID      = "#111833"
SKY_BOT      = "#1a1a3e"
GROUND_COLOR = "#1a1510"
GROUND_LINE  = "#3d3520"

# Canopy rainbow colors
CANOPY_COLORS = ["#ff4757", "#ff6b35", "#ffd60a", "#00ff88", "#00d4ff", "#bd00ff"]

# Stickman colors
SKIN_COLOR   = "#f4c09e"
HELMET_COLOR = "#00d4ff"
SUIT_COLOR   = "#58a6ff"
BOOT_COLOR   = "#8b949e"

# Star field cache
def generate_stars(n=80, seed=42):
    rng = np.random.RandomState(seed)
    xs = rng.uniform(0, 1, n)
    ys = rng.uniform(0.15, 1, n)
    sizes = rng.uniform(0.3, 1.5, n)
    return xs, ys, sizes

def generate_skyline(n_buildings=18, seed=99):
    """Return list of (x_center_frac, width_frac, height_frac) for city skyline."""
    rng = np.random.RandomState(seed)
    buildings = []
    x = 0.0
    for _ in range(n_buildings):
        w = rng.uniform(0.03, 0.08)
        h = rng.uniform(0.02, 0.08)
        buildings.append((x, w, h))
        x += w + rng.uniform(0.005, 0.02)
    return buildings

STARS = generate_stars()
SKYLINE = generate_skyline()

def draw_plane(ax, x, y, scale_x, scale_y, alpha=1.0):
    """Draw a detailed swept-wing jet aircraft. Returns list of patches."""
    from matplotlib.patches import Polygon, Ellipse, Rectangle, FancyBboxPatch
    sx, sy = scale_x, scale_y
    patches = []

    # --- Fuselage (streamlined tube) ---
    fus_pts = np.array([
        [x - 26*sx, y - 2.0*sy],  # tail-bottom
        [x - 29*sx, y           ],  # tail-tip
        [x - 26*sx, y + 2.0*sy],  # tail-top
        [x + 20*sx, y + 3.5*sy],  # nose-top
        [x + 25*sx, y           ],  # nose-tip
        [x + 20*sx, y - 3.5*sy],  # nose-bottom
    ])
    fuselage = Polygon(fus_pts, fc="#7d8590", ec="#58a6ff",
                       lw=1.5, alpha=alpha, zorder=15)
    ax.add_patch(fuselage); patches.append(fuselage)

    # Nose cone accent
    nose_pts = np.array([
        [x + 19*sx, y + 3.0*sy],
        [x + 25*sx, y           ],
        [x + 19*sx, y - 3.0*sy],
    ])
    nose = Polygon(nose_pts, fc="#b1bac4", ec="#00d4ff",
                   lw=1, alpha=alpha, zorder=16)
    ax.add_patch(nose); patches.append(nose)

    # Cockpit windows strip
    cockpit = Ellipse((x + 10*sx, y + 1.2*sy), 14*sx, 4*sy,
                      fc="#00d4ff", ec="#58a6ff",
                      lw=0.8, alpha=alpha * 0.50, zorder=16)
    ax.add_patch(cockpit); patches.append(cockpit)

    # --- Main wings (swept back) ---
    for sign in (1, -1):
        wing_pts = np.array([
            [x + 10*sx, sign *  3.5*sy + y],
            [x -  4*sx, sign * 24.0*sy + y],
            [x - 11*sx, sign * 24.0*sy + y],
            [x -  2*sx, sign *  3.5*sy + y],
        ])
        # Correct y for sign
        if sign == 1:
            pts = wing_pts
        else:
            pts = wing_pts.copy()
            pts[:, 1] = 2*y - wing_pts[:, 1]
        w = Polygon(pts, fc="#3d6bb5", ec="#00d4ff",
                    lw=1.0, alpha=alpha * 0.90, zorder=14)
        ax.add_patch(w); patches.append(w)

        # Winglet tip
        wl_x = pts[1, 0]
        wl_yc = pts[1, 1]
        winglet_pts = np.array([
            [wl_x,         wl_yc                ],
            [wl_x - 4*sx,  wl_yc + sign*3*sy    ],
            [wl_x - 6*sx,  wl_yc + sign*3.5*sy  ],
            [wl_x - 3*sx,  wl_yc                ],
        ]) if sign == 1 else np.array([
            [wl_x,         wl_yc                ],
            [wl_x - 4*sx,  wl_yc - sign*3*sy    ],
            [wl_x - 6*sx,  wl_yc - sign*3.5*sy  ],
            [wl_x - 3*sx,  wl_yc                ],
        ])
        wl = Polygon(winglet_pts, fc="#58a6ff", ec="#00d4ff",
                     lw=0.8, alpha=alpha * 0.85, zorder=13)
        ax.add_patch(wl); patches.append(wl)

        # Engine nacelle under each wing
        eng_y = y + sign * 16 * sy
        engine = Ellipse((x + 0*sx, eng_y), 18*sx, 4.5*sy,
                         fc="#21262d", ec="#58a6ff",
                         lw=1.0, alpha=alpha * 0.90, zorder=13)
        exhaust = Ellipse((x - 9*sx, eng_y), 5*sx, 3*sy,
                          fc="#ff6b35", ec=None, alpha=alpha * 0.75, zorder=13)
        ax.add_patch(engine); patches.append(engine)
        ax.add_patch(exhaust); patches.append(exhaust)

    # --- Vertical tail fin ---
    vtail_pts = np.array([
        [x - 18*sx, y + 2*sy],
        [x - 26*sx, y + 12*sy],
        [x - 24*sx, y + 12*sy],
        [x - 17*sx, y + 3.5*sy],
    ])
    vtail = Polygon(vtail_pts, fc="#3d6bb5", ec="#00d4ff",
                    lw=0.9, alpha=alpha * 0.90, zorder=15)
    ax.add_patch(vtail); patches.append(vtail)

    # --- Horizontal stabilisers ---
    for sign in (1, -1):
        htail_pts = np.array([
            [x - 18*sx, y + sign *  1.5*sy],
            [x - 26*sx, y + sign *  9.0*sy],
            [x - 29*sx, y + sign *  8.5*sy],
            [x - 21*sx, y + sign *  0.8*sy],
        ]) if sign == 1 else np.array([
            [x - 18*sx, y - sign *  1.5*sy],
            [x - 26*sx, y - sign *  9.0*sy],
            [x - 29*sx, y - sign *  8.5*sy],
            [x - 21*sx, y - sign *  0.8*sy],
        ])
        ht = Polygon(htail_pts, fc="#3d6bb5", ec="#00d4ff",
                     lw=0.8, alpha=alpha * 0.85, zorder=14)
        ax.add_patch(ht); patches.append(ht)

    return patches

def draw_helicopter(ax, x, y, scale_x, scale_y, alpha=1.0):
    """Draw a detailed helicopter. Returns (patches, rotor_lines, skid_lines)."""
    from matplotlib.patches import Ellipse, Rectangle, Polygon, Circle
    sx, sy = scale_x, scale_y
    patches = []

    # --- Main fuselage ---
    body = Ellipse((x, y), 44*sx, 16*sy,
                   fc="#21262d", ec="#00d4ff", lw=1.8, alpha=alpha, zorder=15)
    ax.add_patch(body); patches.append(body)

    # Cockpit bubble (front)
    cockpit = Ellipse((x + 12*sx, y + 2*sy), 18*sx, 10*sy,
                      fc="#00d4ff", ec="#58a6ff",
                      lw=1.0, alpha=alpha * 0.50, zorder=16)
    ax.add_patch(cockpit); patches.append(cockpit)

    # --- Tail boom ---
    tail_pts = np.array([
        [x - 22*sx, y + 3.0*sy],
        [x - 40*sx, y + 6.0*sy],
        [x - 40*sx, y + 1.5*sy],
        [x - 22*sx, y - 2.5*sy],
    ])
    tail_boom = Polygon(tail_pts, fc="#161b22", ec="#00d4ff",
                        lw=1.0, alpha=alpha * 0.90, zorder=14)
    ax.add_patch(tail_boom); patches.append(tail_boom)

    # Tail fin
    fin_pts = np.array([
        [x - 37*sx, y + 6*sy],
        [x - 43*sx, y + 14*sy],
        [x - 40*sx, y + 14*sy],
        [x - 35*sx, y + 6*sy],
    ])
    fin = Polygon(fin_pts, fc="#3d6bb5", ec="#00d4ff",
                  lw=0.9, alpha=alpha * 0.85, zorder=14)
    ax.add_patch(fin); patches.append(fin)

    # Tail rotor hub
    tr_hub = Circle((x - 40*sx, y + 10*sy), 2.5*sy,
                    fc="#30363d", ec="#58a6ff",
                    lw=1.0, alpha=alpha, zorder=16)
    ax.add_patch(tr_hub); patches.append(tr_hub)

    # Main rotor hub
    mr_hub = Circle((x, y + 9*sy), 2.5*sy,
                    fc="#30363d", ec="#00d4ff",
                    lw=1.2, alpha=alpha, zorder=17)
    ax.add_patch(mr_hub); patches.append(mr_hub)

    # Rotor mast (vertical strut)
    mast = Rectangle((x - 1*sx, y + 8*sy), 2*sx, 8*sy,
                     fc="#8b949e", ec=None, alpha=alpha * 0.8, zorder=15)
    ax.add_patch(mast); patches.append(mast)

    # --- Sliding door panel ---
    door = Rectangle((x - 4*sx, y - 4*sy), 10*sx, 7*sy,
                     fc="#30363d", ec="#58a6ff",
                     lw=0.8, alpha=alpha * 0.70, zorder=16)
    ax.add_patch(door); patches.append(door)

    # --- Main rotor blades (2 lines = 4 blades at 90°) ---
    rotor_main = ax.plot(
        [x - 34*sx, x + 34*sx], [y + 9*sy, y + 9*sy],
        color="#00d4ff", lw=2.5, alpha=alpha * 0.90, zorder=18,
    )
    rotor_cross = ax.plot(
        [x - 24*sx, x + 24*sx], [y + 9*sy, y + 9*sy],
        color="#58a6ff", lw=1.5, alpha=alpha * 0.65, zorder=17,
    )
    # Tail rotor blades
    tail_rotor = ax.plot(
        [x - 40*sx, x - 40*sx], [y + 6*sy, y + 14*sy],
        color="#ff6b35", lw=2.0, alpha=alpha * 0.85, zorder=17,
    )
    rotor_lines = rotor_main + rotor_cross + tail_rotor

    # --- Landing skids ---
    skid_top = ax.plot(
        [x - 14*sx, x + 14*sx], [y - 9*sy, y - 9*sy],
        color="#8b949e", lw=2.5, alpha=alpha * 0.90, zorder=14,
    )
    skid_bot = ax.plot(
        [x - 14*sx, x + 14*sx], [y - 12*sy, y - 12*sy],
        color="#8b949e", lw=2.5, alpha=alpha * 0.90, zorder=14,
    )
    post_l = ax.plot(
        [x - 9*sx, x - 9*sx], [y - 9*sy, y - 12*sy],
        color="#8b949e", lw=2.0, alpha=alpha * 0.85, zorder=14,
    )
    post_r = ax.plot(
        [x + 7*sx, x + 7*sx], [y - 9*sy, y - 12*sy],
        color="#8b949e", lw=2.0, alpha=alpha * 0.85, zorder=14,
    )
    skid_lines = skid_top + skid_bot + post_l + post_r

    return patches, rotor_lines, skid_lines


# ── Moon Colors ────────────────────────────────────────────────────────────
MOON_BODY   = "#e8e0d0"
MOON_SHADOW = "#c8bfaa"
MOON_CRATER = "#b8af99"

# ── Sky gradient colors (top → bottom) ─────────────────────────────────────
SKY_GRADIENT = [
    (0.85, 1.00, "#05060d"),   # very top – near-black
    (0.70, 0.85, "#0b0e1a"),   # deep navy
    (0.50, 0.70, "#111833"),   # dark blue
    (0.30, 0.50, "#1a1a3e"),   # dark indigo
    (0.10, 0.30, "#1e1540"),   # purple tint
    (0.00, 0.10, "#18122a"),   # near-horizon purple
]

def set_theme(is_day: bool):
    global IS_DAY, SKY_TOP, SKY_MID, SKY_BOT, GROUND_COLOR, GROUND_LINE, SKY_GRADIENT
    IS_DAY = is_day
    if is_day:
        SKY_TOP      = "#4a90e2"
        SKY_MID      = "#6bb5ff"
        SKY_BOT      = "#a8d3ff"
        GROUND_COLOR = "#4a5a3a"
        GROUND_LINE  = "#2d3822"
        SKY_GRADIENT = [
            (0.85, 1.00, "#3a7bd5"),
            (0.70, 0.85, "#4a90e2"),
            (0.50, 0.70, "#6bb5ff"),
            (0.30, 0.50, "#85c4ff"),
            (0.10, 0.30, "#a8d3ff"),
            (0.00, 0.10, "#cbe6ff"),
        ]
    else:
        SKY_TOP      = "#0b0e1a"
        SKY_MID      = "#111833"
        SKY_BOT      = "#1a1a3e"
        GROUND_COLOR = "#1a1510"
        GROUND_LINE  = "#3d3520"
        SKY_GRADIENT = [
            (0.85, 1.00, "#05060d"),
            (0.70, 0.85, "#0b0e1a"),
            (0.50, 0.70, "#111833"),
            (0.30, 0.50, "#1a1a3e"),
            (0.10, 0.30, "#1e1540"),
            (0.00, 0.10, "#18122a"),
        ]


def draw_sky_gradient(ax, y_min, y_max):
    """Draw horizontal gradient bands across the scene background."""
    y_range = y_max - y_min
    for frac_lo, frac_hi, color in SKY_GRADIENT:
        y_lo = y_min + frac_lo * y_range
        y_hi = y_min + frac_hi * y_range
        ax.axhspan(y_lo, y_hi, facecolor=color, zorder=0, alpha=0.95)


def draw_moon(ax, x_frac, y_frac):
    """Draw a crescent moon at fractional axes coordinates using scatter.
    Returns list of paths/collections for cleanup."""
    transform = ax.transAxes

    # Moon body (bright circle) or Sun if day
    body_color = "#ffdf80" if IS_DAY else MOON_BODY
    moon = ax.scatter([x_frac], [y_frac], s=800, c=body_color, 
                      alpha=0.95 if IS_DAY else 0.9, zorder=2, transform=transform)

    patches = [moon]
    if not IS_DAY:
        # Shadow to create crescent shape
        offset = 0.012
        shadow = ax.scatter([x_frac + offset], [y_frac + offset], s=700, 
                            c=SKY_TOP, alpha=1.0, zorder=3, transform=transform)
        patches.append(shadow)
        
    # Glow halo
    glow_color = "#ffdf80" if IS_DAY else MOON_BODY
    glow_alpha = 0.2 if IS_DAY else 0.06
    glow = ax.scatter([x_frac], [y_frac], s=2500, c=glow_color, 
                      alpha=glow_alpha, zorder=1, transform=transform)
    patches.append(glow)

    return patches



def draw_skyline(ax, x_min, x_max, ground_y=0.0, max_height_data=100.0):
    """Draw a city skyline silhouette just above the ground.
    Returns list of patches for cleanup."""
    from matplotlib.patches import Rectangle
    patches = []
    x_range = x_max - x_min
    # Scale building heights relative to data range (keep small)
    h_scale = max_height_data * 0.04

    for x_frac, w_frac, h_frac in SKYLINE:
        bx = x_min + x_frac * x_range
        bw = w_frac * x_range
        bh = h_frac * h_scale * 8
        # Main building
        bld = Rectangle((bx, ground_y), bw, bh, fc="#0d0f14", ec="#1a1f2e",
                          lw=0.8, alpha=0.85, zorder=1)
        ax.add_patch(bld)
        patches.append(bld)

        # Windows (tiny glowing dots)
        n_floors = max(1, int(bh / (h_scale * 0.5)))
        n_cols = max(1, int(bw / (0.015 * x_range)))
        for fy in range(n_floors):
            for fx in range(n_cols):
                # Random window lit chance
                if np.random.random() > 0.45:
                    wx = bx + (fx + 0.5) * (bw / max(1, n_cols))
                    wy = ground_y + (fy + 0.5) * (bh / max(1, n_floors))
                    win_color = np.random.choice(["#ffd60a", "#ff6b35", "#00d4ff", "#ffffff"])
                    win = Rectangle((wx - 0.002 * x_range, wy - h_scale * 0.08),
                                     0.004 * x_range, h_scale * 0.15,
                                     fc=win_color, ec=None, alpha=0.35 + np.random.random() * 0.3,
                                     zorder=2)
                    ax.add_patch(win)
                    patches.append(win)
    return patches
