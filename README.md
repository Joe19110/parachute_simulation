# 3D Parachute Physics Simulation

A comprehensive, Python-based physics simulation that models the aerodynamic trajectory of a payload dropping through the atmosphere. The project uses numerical integration (Euler's Method) to compute 3D kinematics, fluid dynamics (drag), and wind drift in real-time. It features a fully interactive GUI with live animated playback and post-simulation telemetry analysis.

## Features

- **Accurate Physics Engine:** Simulates gravitational acceleration, aerodynamic drag, and terminal velocity using real-world fluid dynamics formulas ($F = \frac{1}{2}\rho C_d A v^2$).
- **Dynamic Wind Shear:** Simulates realistic altitude-varying wind that scales linearly from the drop altitude down to the surface, creating parabolic drift trajectories.
- **Ram-Air Glide Mechanics:** Simulates "Square" parachutes that act as airfoils, generating forward aerodynamic thrust based on a specific Glide Ratio ($L/D$).
- **Auto-Jump Calculator:** Uses background forward-simulation to calculate exactly where an aircraft needs to drop a payload to land perfectly on a designated target cushion, accounting for complex wind drift.
- **Interactive GUI:** Built with Tkinter and Matplotlib. Features live day/night mode toggles, real-time wind HUDs, and dynamic camera panning.
- **Telemetry Dashboard:** Automatically plots Altitude vs. Time, Total Speed vs. Time, and G-Forces vs. Time, capturing the massive deceleration shock of parachute deployment.

## Installation

This project requires **Python 3** and a few standard mathematical/graphical libraries.

1. Clone this repository to your local machine.
2. Install the required dependencies using `pip`:
   ```bash
   pip install numpy matplotlib
   ```

## How to Run

To launch the interactive graphical simulation, simply run the `main.py` file from your terminal:

```bash
python main.py
```
*(On some Windows systems, you may need to use `py main.py` instead).*

## How to Use

1. **Parameters:** Use the sliders on the left panel to configure the starting altitude, parachute deployment altitude, wind speed, and payload mass.
2. **Advanced Settings:** Open the advanced panel to swap parachute types. Select **"Ram-Air"** to enable forward glide, or **"Round"** for a standard vertical drop.
3. **Landing Cushion:** Enable the landing cushion and drag it along the ground on the screen to set a target zone.
4. **Auto-Jump:** Click the `🎯 Auto-Jump` button to automatically calculate the required release coordinates and execute a perfectly targeted drop.
5. **Run:** Click `▶ Run` to execute the simulation. The physics engine will calculate the trajectory instantly, and the animation player will visually replay the drop.

## Project Structure

The codebase is built with a highly modular architecture, completely separating the physics math from the graphical rendering:

- `main.py` — The entry point of the application.
- `constants.py` — Central configuration file holding all physical constants and default simulation parameters.
- `physics.py` — The strict mathematical formulas for calculating Drag Force, Glide Thrust, and Net Acceleration.
- `simulator.py` — The core numerical integration engine. Runs the Euler loop over $dt$ time-steps and returns the flight history array.
- `analysis.py` — Parses the history array to determine maximum G-forces, flight time, and safe landing thresholds.
- `ui/` — The front-end graphics package containing the Tkinter window layout (`app.py`), the parameter sliders (`panels.py`), the Matplotlib patch drawing (`scene.py`), and the animation ticker (`animation.py`).
