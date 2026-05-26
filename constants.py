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
vx0 = 0.0
vy0 = 0.0

# Parachute parameters
h_open = 800.0
Cd_free = 1.0
A_free = 0.7
Cd_para = 1.5
A_para = 40.0

# Safety threshold
wind_speed = 0.0
v_safe = 5.0

# Drop mode: "freefall", "plane", "helicopter"
drop_mode = "freefall"

# Vehicle behaviour after drop: "fly_away" or "stay"
vehicle_behavior = "fly_away"


@dataclass
class SimulationParams:
    g: float = g
    rho: float = rho
    dt: float = dt
    t_max: float = t_max
    m: float = m
    h0: float = h0
    x0: float = x0
    vx0: float = vx0
    vy0: float = vy0
    h_open: float = h_open
    Cd_free: float = Cd_free
    A_free: float = A_free
    Cd_para: float = Cd_para
    A_para: float = A_para
    wind_speed: float = wind_speed
    v_safe: float = v_safe
    drop_mode: str = drop_mode
    vehicle_behavior: str = vehicle_behavior
