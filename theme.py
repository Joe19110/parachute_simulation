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

# Sky gradient stops (top→bottom for night sky)
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
    """Draw a simple plane shape. Returns list of patches."""
    from matplotlib.patches import Polygon, Ellipse
    # Fuselage
    body = Ellipse((x, y), 18*scale_x, 3*scale_y, fc="#8b949e", ec="#58a6ff", lw=1.2, alpha=alpha, zorder=15)
    # Wings
    wing_pts = np.array([
        [x - 3*scale_x, y],
        [x - 1*scale_x, y + 6*scale_y],
        [x + 4*scale_x, y + 6*scale_y],
        [x + 2*scale_x, y],
    ])
    wing = Polygon(wing_pts, fc="#58a6ff", ec="#00d4ff", lw=1, alpha=alpha*0.85, zorder=14)
    wing_b = Polygon(wing_pts * np.array([1, -1]) + np.array([0, 2*y]),
                      fc="#58a6ff", ec="#00d4ff", lw=1, alpha=alpha*0.85, zorder=14)
    # Tail
    tail_pts = np.array([
        [x - 8*scale_x, y],
        [x - 7*scale_x, y + 4*scale_y],
        [x - 5*scale_x, y + 3*scale_y],
        [x - 5*scale_x, y],
    ])
    tail = Polygon(tail_pts, fc="#30363d", ec="#58a6ff", lw=1, alpha=alpha*0.9, zorder=14)
    patches = [body, wing, wing_b, tail]
    for p in patches:
        ax.add_patch(p)
    return patches

def draw_helicopter(ax, x, y, scale_x, scale_y, alpha=1.0):
    """Draw a simple helicopter shape. Returns list of patches/lines."""
    from matplotlib.patches import Ellipse, Rectangle, Polygon
    # Body
    body = Ellipse((x, y), 14*scale_x, 4.5*scale_y, fc="#30363d", ec="#00d4ff", lw=1.5, alpha=alpha, zorder=15)
    # Cockpit window
    cockpit = Ellipse((x + 4*scale_x, y + 0.3*scale_y), 4*scale_x, 2.5*scale_y,
                       fc="#00d4ff", ec="#58a6ff", lw=1, alpha=alpha*0.5, zorder=16)
    # Tail boom
    tail_pts = np.array([
        [x - 7*scale_x, y + 0.5*scale_y],
        [x - 12*scale_x, y + 2*scale_y],
        [x - 12*scale_x, y - 0.5*scale_y],
        [x - 7*scale_x, y - 0.5*scale_y],
    ])
    tail = Polygon(tail_pts, fc="#21262d", ec="#00d4ff", lw=1, alpha=alpha*0.9, zorder=14)
    # Tail rotor
    tr = Rectangle((x - 12.5*scale_x, y + 1*scale_y), 1*scale_x, 3*scale_y,
                    fc="#ff6b35", ec=None, alpha=alpha*0.7, zorder=16)
    patches = [body, cockpit, tail, tr]
    for p in patches:
        ax.add_patch(p)
    # Main rotor (line)
    rotor = ax.plot([x - 10*scale_x, x + 10*scale_x], [y + 2.8*scale_y, y + 2.8*scale_y],
                     color="#00d4ff", lw=2, alpha=alpha*0.8, zorder=17)
    # Skids
    skid = ax.plot([x - 4*scale_x, x + 4*scale_x], [y - 2.8*scale_y, y - 2.8*scale_y],
                    color="#8b949e", lw=2, alpha=alpha*0.9, zorder=14)
    return patches, rotor, skid


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


def draw_sky_gradient(ax, y_min, y_max):
    """Draw horizontal gradient bands across the scene background."""
    y_range = y_max - y_min
    for frac_lo, frac_hi, color in SKY_GRADIENT:
        y_lo = y_min + frac_lo * y_range
        y_hi = y_min + frac_hi * y_range
        ax.axhspan(y_lo, y_hi, facecolor=color, zorder=0, alpha=0.95)


def draw_moon(ax, x_frac, y_frac):
    """Draw a crescent moon at fractional axes coordinates.
    Returns list of patches for cleanup."""
    from matplotlib.patches import Circle
    transform = ax.transAxes

    # Moon body (bright circle)
    moon = Circle((x_frac, y_frac), 0.035, fc=MOON_BODY, ec=None,
                   alpha=0.9, zorder=2, transform=transform)
    ax.add_patch(moon)

    # Crescent shadow (dark circle offset to create crescent shape)
    shadow = Circle((x_frac + 0.012, y_frac + 0.008), 0.030,
                     fc="#0b0e1a", ec=None, alpha=0.92, zorder=2,
                     transform=transform)
    ax.add_patch(shadow)

    # Small craters on visible part
    c1 = Circle((x_frac - 0.012, y_frac - 0.005), 0.005,
                 fc=MOON_CRATER, ec=None, alpha=0.4, zorder=3,
                 transform=transform)
    c2 = Circle((x_frac - 0.005, y_frac + 0.015), 0.003,
                 fc=MOON_CRATER, ec=None, alpha=0.35, zorder=3,
                 transform=transform)
    ax.add_patch(c1)
    ax.add_patch(c2)

    # Glow halo
    glow = Circle((x_frac, y_frac), 0.055, fc=MOON_BODY, ec=None,
                   alpha=0.06, zorder=1, transform=transform)
    ax.add_patch(glow)

    return [moon, shadow, c1, c2, glow]


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
