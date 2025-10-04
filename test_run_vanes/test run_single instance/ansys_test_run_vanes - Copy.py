# -*- coding: utf-8 -*-
"""
Final Test Script for a Ventilated Brake Disc (Definitive Version)

This script combines the successful "build-up and glue" geometry method
with the successful "select elements by radius" and "SFE" load application method.
This is the final, correct implementation for our test run.
"""

import os
import numpy as np
from ansys.mapdl.core import launch_mapdl

# --- 1. Setup Simulation Environment ---
print("--- Setting up Simulation Environment ---")
simulation_dir_name = "vaned_disc_test_run"
main_project_dir = os.getcwd()
simulation_path = os.path.join(main_project_dir, simulation_dir_name)
if not os.path.exists(simulation_path):
    os.makedirs(simulation_path)
    print(f"Created subfolder: {simulation_path}")

# --- 2. Launch ANSYS MAPDL ---
print("\n--- Launching ANSYS MAPDL ---")
jobname = "disc_model"
try:
    mapdl = launch_mapdl(run_location=simulation_path, jobname=jobname, override=True, cleanup_on_exit=False)
    print(mapdl)
except Exception as e:
    print(f"Failed to launch MAPDL: {e}")
    exit()


# --- 3. Define All Project Parameters ---
# Geometric Parameters
vane_count = 48
vane_thickness_deg = 2.0
disc_outer_radius = 0.160
braking_band_outer_radius = 0.155
braking_band_inner_radius = 0.100
hub_radius = 0.080
# Material & Physics Parameters
thermal_conductivity = 55
density = 7200
specific_heat = 460
heat_flux = 9e6
convection_coeff = 120
ambient_temp = 22
initial_temp = 22
# Time Settings
braking_time = 4.0
end_time = 10.0
time_step = 0.25

# --- 4. Pre-Processing: Building the Model ---
print("\n--- Entering Pre-processing stage ---")
mapdl.clear()
mapdl.prep7()
mapdl.mp("KXX", 1, thermal_conductivity)
mapdl.mp("DENS", 1, density)
mapdl.mp("C", 1, specific_heat)
mapdl.et(1, "PLANE55")

# **PROVEN GEOMETRY METHOD: BUILD-UP AND GLUE**
print("Creating full geometry with ventilation vanes...")
# Step 1: Create the two solid rings using basic circle and subtract commands
c1 = mapdl.cyl4(0,0, disc_outer_radius)
c2 = mapdl.cyl4(0,0, braking_band_outer_radius)
mapdl.asba(c1, c2)

c3 = mapdl.cyl4(0,0, braking_band_inner_radius)
c4 = mapdl.cyl4(0,0, hub_radius)
mapdl.asba(c3, c4)

# Step 2: Create the solid vanes one by one from lines and arcs
for i in range(vane_count):
    angle_start_deg = (360 / vane_count) * i
    angle_end_deg = angle_start_deg + vane_thickness_deg
    
    angle_start_rad = np.deg2rad(angle_start_deg)
    angle_end_rad = np.deg2rad(angle_end_deg)

    k1 = mapdl.k("", braking_band_inner_radius * np.cos(angle_start_rad), braking_band_inner_radius * np.sin(angle_start_rad), 0)
    k2 = mapdl.k("", braking_band_outer_radius * np.cos(angle_start_rad), braking_band_outer_radius * np.sin(angle_start_rad), 0)
    k3 = mapdl.k("", braking_band_outer_radius * np.cos(angle_end_rad), braking_band_outer_radius * np.sin(angle_end_rad), 0)
    k4 = mapdl.k("", braking_band_inner_radius * np.cos(angle_end_rad), braking_band_inner_radius * np.sin(angle_end_rad), 0)
    
    l_side1 = mapdl.l(k1, k2)
    l_outer_arc = mapdl.larc(k2, k3, mapdl.k("", 0,0,0), braking_band_outer_radius)
    l_side2 = mapdl.l(k3, k4)
    l_inner_arc = mapdl.larc(k4, k1, mapdl.k("", 0,0,0), braking_band_inner_radius)

    mapdl.al(l_side1, l_outer_arc, l_side2, l_inner_arc)

# Step 3: Glue all adjacent areas together to form one part
mapdl.aglue('ALL')

# Mesh the final, complex geometry
mapdl.smrtsize(4)
mapdl.amesh('ALL')
print("Geometry and Mesh created.")

# Save the input geometry image to the MAIN project folder
png_path = os.path.join(main_project_dir, 'input_geometry_vaned.png')
try:
    mapdl.eplot(show_bounds=True, cpos='xy', savefig=png_path)
    print(f"Saved vaned geometry image to: {png_path}")
except Exception as e:
    print(f"Could not save geometry plot. Error: {e}")


# --- 5. Solution: Applying Loads and Solving ---
print("\n--- Entering Solution stage ---")
mapdl.finish()
mapdl.slashsolu()
mapdl.antype("TRANSIENT")
mapdl.tunif(initial_temp)

# Apply convection to all external lines
mapdl.lsel('S', 'EXT')
mapdl.sfl("all", "CONV", convection_coeff, "", ambient_temp)
mapdl.allsel()

# **ROBUST LOAD APPLICATION v2.0**: Select NODES by radius, then attached ELEMENTS.
mapdl.local(11, 1, 0, 0, 0) # Create CSYS 11 (Cylindrical)
mapdl.csys(11)              # Activate it

# Step 1: Select NODES within the radial braking band
mapdl.nsel('S', 'LOC', 'X', braking_band_inner_radius, braking_band_outer_radius)

# Step 2: Select all ELEMENTS attached to the selected nodes
mapdl.esln('S', 0)

# DEBUGGING CHECK: See how many elements were selected
elem_count = mapdl.get_value("ELEM", 0, "COUNT")
print(f"Selected {elem_count} elements for heat flux application.")
if elem_count == 0:
    print("FATAL: No elements selected. Stopping.")
    mapdl.exit() # Stop if the selection failed

# Step 3: Apply a SURFACE heat flux (SFE) to the faces of the selected elements
mapdl.sfe('ALL', 1, 'HFLUX', '', heat_flux)

mapdl.csys(0)    # IMPORTANT: Switch back to default CSYS
mapdl.allsel()   # Reselect everything for safety

# Set up the first load step (heating)
mapdl.time(braking_time)
mapdl.nsubst(int(braking_time / time_step))
mapdl.kbc(0)
mapdl.outres("ALL", "ALL")
print("Solving first load step (heating)...")
mapdl.solve()

# Set up the second load step (cooling)
mapdl.csys(11) # Activate cylindrical system again

# Reselect the same elements as before
mapdl.nsel('S', 'LOC', 'X', braking_band_inner_radius, braking_band_outer_radius)
mapdl.esln('S', 0)

# Delete the SURFACE heat flux load from the selected elements
mapdl.sfedele('ALL', 1, 'HFLUX')

mapdl.csys(0) # Switch back to default system
mapdl.allsel()

mapdl.time(end_time)
mapdl.nsubst(int((end_time - braking_time) / time_step))
print("Solving second load step (cooling)...")
mapdl.solve()
print("Solution complete.")


# --- 6. Post-Processing ---
print("\n--- Entering Post-processing stage ---")
mapdl.finish()
mapdl.post1()
print(f"Loading result at time = {braking_time} seconds...")
mapdl.set(time=braking_time)

# Save the output temperature image to the MAIN project folder
png_path_temp = os.path.join(main_project_dir, 'output_temperature_vaned.png')
try:
    mapdl.post_processing.plot_nodal_temperature(
        show_edges=True, cpos='xy', background='white', edge_color='black',
        show_bounds=True, scalar_bar_args={"title": "Temperature (°C)"},
        savefig=png_path_temp
    )
    print(f"Saved vaned temperature image to: {png_path_temp}")
except Exception as e:
    print(f"Could not save temperature plot. Error: {e}")


# --- 7. Finish ---
mapdl.exit()
print("Script finished.")