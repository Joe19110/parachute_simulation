from dataclasses import dataclass, field

# Physical constants
g = 9.81
rho = 1.225

# Simulation control
dt = 0.01
t_max = 1000.0

# Skydiver parameters
m = 80.0
h0 = 4000.0
x0 = 0.0
z0 = 0.0
vx0 = 0.0
vy0 = 0.0
vz0 = 0.0

# Parachute parameters (default: Round)
h_open = 800.0
Cd_free = 1.0
A_free = 0.7
Cd_para = 1.5
A_para = 60.0

# Glide parameters (only for ram-air)
glide_ratio = 0.0   # L/D forward glide; 0 = no glide (round chutes)
glide_az = 0.0      # Same for z-axis

# Wind
wind_x = 2.0        # horizontal wind (x direction, m/s)
wind_z = 0.0       # crosswind (z direction, m/s)
wind_shear = False  # If true, wind scales down linearly from h0 to 0 at the ground

# Safety threshold
v_safe = 5.0

# Drop mode: "freefall", "plane", "helicopter"
drop_mode = "freefall"

# Vehicle behaviour after drop: "fly_away" or "stay"
vehicle_behavior = "fly_away"

# Vehicle speed (overrides vx0 when drop_mode != freefall)
vehicle_speed_x = 50.0   # plane forward speed (m/s)
vehicle_speed_z = 0.0    # side speed / helicopter drift (m/s)

# Target landing spot (for jump-point calculation)
target_x = 0.0
target_z = 0.0
cushion_size_x = 20.0  # width of the safe zone in X (m)
cushion_size_z = 20.0  # width of the safe zone in Z (m)

# ── Parachute shape presets ───────────────────────────────────────────────────
# Each entry: (Cd_para, A_para, glide_ratio, glide_az, visual)
PARACHUTE_SHAPES = {
    "Round":      (1.5,  60.0,  0.0,  0.0, "round"),
    "Ram-Air":    (0.8,  25.0,  2.5,  0.0, "ramair"),
    "Cruciform":  (1.6,  45.0,  0.0,  0.0, "cruciform"),
    "Annular":    (1.2,  50.0,  0.0,  0.0, "annular"),
}

# Default parachute shape key
parachute_shape = "Round"


@dataclass
class SimulationParams:
    g:               float = g
    rho:             float = rho
    dt:              float = dt
    t_max:           float = t_max
    m:               float = m
    h0:              float = h0
    x0:              float = x0
    z0:              float = z0
    vx0:             float = vx0
    vy0:             float = vy0
    vz0:             float = vz0
    h_open:          float = h_open
    Cd_free:         float = Cd_free
    A_free:          float = A_free
    Cd_para:         float = Cd_para
    A_para:          float = A_para
    glide_ratio:     float = glide_ratio
    glide_az:        float = glide_az
    wind_x:          float = wind_x
    wind_z:          float = wind_z
    # Legacy alias: wind_speed mapped to wind_x for backwards compat
    wind_speed:      float = wind_x
    v_safe:          float = v_safe
    drop_mode:       str   = drop_mode
    vehicle_behavior:str   = vehicle_behavior
    vehicle_speed_x: float = vehicle_speed_x
    vehicle_speed_z: float = vehicle_speed_z
    target_x:        float = target_x
    target_z:        float = target_z
    cushion_size_x:  float = cushion_size_x
    cushion_size_z:  float = cushion_size_z
    parachute_shape: str   = parachute_shape
    wind_shear:      bool  = wind_shear
    follow_cam:      bool  = False

    def __post_init__(self):
        # Keep wind_x and wind_speed in sync (wind_x takes precedence)
        if self.wind_x != 0.0 and self.wind_speed == 0.0:
            self.wind_speed = self.wind_x
        elif self.wind_speed != 0.0 and self.wind_x == 0.0:
            self.wind_x = self.wind_speed
