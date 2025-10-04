# simulation_runner.py
# CONTAINS THE DEFINITIVE, VALIDATED SIMULATION LOGIC

import os
import numpy as np
from ansys.mapdl.core import launch_mapdl
from datetime import datetime

def run_single_simulation(run_id, params, base_run_dir, final_image_dir):
    """
    Runs a single ANSYS simulation for a given set of brake disc parameters
    using the validated geometry and load application method.
    
    Returns a dictionary containing the key numerical results.
    """
    # --- 1. Setup Simulation Environment ---
    print(f"--- Setting up Simulation for Run ID: {run_id} ---")
    simulation_dir_name = f"run_{run_id:04d}"
    simulation_path = os.path.join(base_run_dir, simulation_dir_name)
    if not os.path.exists(simulation_path):
        os.makedirs(simulation_path)

    # --- 2. Launch ANSYS MAPDL ---
    jobname = "disc_model"
    try:
        # Note: Set cleanup_on_exit=True for automated runs to save disk space
        mapdl = launch_mapdl(run_location=simulation_path, jobname=jobname, override=True, cleanup_on_exit=True)
    except Exception as e:
        print(f"Failed to launch MAPDL for run {run_id}. Error: {e}")
        return {'peak_temp': float('nan'), 'status': 'launch_failed', 'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S")}

    # --- 3. Define All Project Parameters ---
    # Parameters passed in from the master script
    vane_count = params['vane_count']
    vane_thickness_deg = params['vane_thickness_deg']
    heat_flux = params['heat_flux']
    
    # Fixed Parameters (as defined in your script)
    disc_outer_radius = 0.160
    braking_band_outer_radius = 0.155
    braking_band_inner_radius = 0.100
    hub_radius = 0.080
    thermal_conductivity, density, specific_heat = 55, 7200, 460
    convection_coeff, ambient_temp, initial_temp = 120, 22, 22
    braking_time, end_time, time_step = 4.0, 10.0, 0.25

    # --- 4. Pre-Processing: Building the Model ---
    mapdl.clear()
    mapdl.prep7()
    mapdl.mp("KXX", 1, thermal_conductivity); mapdl.mp("DENS", 1, density); mapdl.mp("C", 1, specific_heat)
    mapdl.et(1, "PLANE55")
    
    # PROVEN GEOMETRY METHOD: BUILD-UP AND GLUE
    c1 = mapdl.cyl4(0,0, disc_outer_radius); c2 = mapdl.cyl4(0,0, braking_band_outer_radius); mapdl.asba(c1, c2)
    c3 = mapdl.cyl4(0,0, braking_band_inner_radius); c4 = mapdl.cyl4(0,0, hub_radius); mapdl.asba(c3, c4)

    for i in range(vane_count):
        angle_start_deg = (360 / vane_count) * i; angle_end_deg = angle_start_deg + vane_thickness_deg
        angle_start_rad, angle_end_rad = np.deg2rad(angle_start_deg), np.deg2rad(angle_end_deg)
        k1 = mapdl.k("", braking_band_inner_radius * np.cos(angle_start_rad), braking_band_inner_radius * np.sin(angle_start_rad), 0)
        k2 = mapdl.k("", braking_band_outer_radius * np.cos(angle_start_rad), braking_band_outer_radius * np.sin(angle_start_rad), 0)
        k3 = mapdl.k("", braking_band_outer_radius * np.cos(angle_end_rad), braking_band_outer_radius * np.sin(angle_end_rad), 0)
        k4 = mapdl.k("", braking_band_inner_radius * np.cos(angle_end_rad), braking_band_inner_radius * np.sin(angle_end_rad), 0)
        l_side1, l_outer_arc, l_side2, l_inner_arc = mapdl.l(k1, k2), mapdl.larc(k2, k3, mapdl.k("", 0,0,0), braking_band_outer_radius), mapdl.l(k3, k4), mapdl.larc(k4, k1, mapdl.k("", 0,0,0), braking_band_inner_radius)
        mapdl.al(l_side1, l_outer_arc, l_side2, l_inner_arc)

    mapdl.aglue('ALL'); mapdl.smrtsize(4); mapdl.amesh('ALL')
    
    # Save input image to the final dataset folder with a unique name
    input_png_path = os.path.join(final_image_dir, f'input_{run_id:04d}.png')
    try: mapdl.eplot(show_bounds=True, cpos='xy', savefig=input_png_path)
    except: pass # Ignore plotting errors in batch runs

    # --- 5. Solution: Applying Loads and Solving ---
    mapdl.finish(); mapdl.slashsolu(); mapdl.antype("TRANSIENT"); mapdl.tunif(initial_temp)
    mapdl.lsel('S', 'EXT'); mapdl.sfl("all", "CONV", convection_coeff, "", ambient_temp); mapdl.allsel()
    
    # ROBUST LOAD APPLICATION v2.0
    mapdl.local(11, 1, 0, 0, 0); mapdl.csys(11)
    mapdl.nsel('S', 'LOC', 'X', braking_band_inner_radius, braking_band_outer_radius)
    mapdl.esln('S', 0)
    mapdl.sfe('ALL', 1, 'HFLUX', '', heat_flux)
    mapdl.csys(0); mapdl.allsel()
    mapdl.time(braking_time); mapdl.nsubst(int(braking_time / time_step)); mapdl.kbc(0); mapdl.outres("ALL", "ALL")
    mapdl.solve()
    
    mapdl.csys(11); mapdl.nsel('S', 'LOC', 'X', braking_band_inner_radius, braking_band_outer_radius)
    mapdl.esln('S', 0); mapdl.sfedele('ALL', 1, 'HFLUX'); mapdl.csys(0); mapdl.allsel()
    mapdl.time(end_time); mapdl.nsubst(int((end_time - braking_time) / time_step))
    mapdl.solve()

    # --- 6. Post-Processing ---
    mapdl.finish(); mapdl.post1(); mapdl.set(time=braking_time)
    peak_temperature = float('nan')
    try:
        mapdl.run('NSORT,TEMP,,1')
        peak_temperature = mapdl.get_value('SORT', item1='MAX')
        # Save output image to the final dataset folder with a unique name
        output_png_path = os.path.join(final_image_dir, f'output_{run_id:04d}.png')
        mapdl.post_processing.plot_nodal_temperature(show_edges=True, cpos='xy', background='white', edge_color='black', show_bounds=True, scalar_bar_args={"title": "Temperature (°C)"}, savefig=output_png_path)
    except Exception as e:
        print(f"Post-processing failed for run {run_id}. Error: {e}")

    # --- 7. Finish ---
    mapdl.exit()
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    # Return all results in a dictionary for the master script to log
    return {
        'run_id': run_id,
        'peak_temp': peak_temperature,
        'status': 'success' if not np.isnan(peak_temperature) else 'post_processing_failed',
        'timestamp': timestamp
    }

