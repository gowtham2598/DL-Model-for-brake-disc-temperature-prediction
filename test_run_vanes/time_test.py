# time_test.py
# This script is dedicated to running a single simulation to measure its execution time.

import os
import time  # Import Python's standard time module
from simulation_runner import run_single_simulation

# --- 1. Configuration ---
# We'll use separate directories for this test to keep things clean.
BASE_RUN_DIR = "ansys_runs_timetest"
FINAL_IMAGE_DIR = "dataset_images_timetest"

# --- 2. Main Execution Block ---
if __name__ == "__main__":
    print("--- Starting Single Simulation Time Test ---")

    # --- Setup Directories ---
    # Create the necessary folders if they don't already exist.
    os.makedirs(BASE_RUN_DIR, exist_ok=True)
    os.makedirs(FINAL_IMAGE_DIR, exist_ok=True)
    print("Test directories are ready.")

    # --- Define Parameters for One Test Run ---
    # We will use a single, representative set of parameters.
    # Mid-range values are good for getting an average estimate.
    params = {
        'vane_count': 54, # A mid-range value from our 36-72 span
        'vane_thickness_deg': 2.5,
        'heat_flux': 1.9e6
    }
    run_id = 1
    
    print("\nUsing the following parameters for the test run:")
    print(f"  - Vane Count: {params['vane_count']}")
    print(f"  - Vane Thickness: {params['vane_thickness_deg']}°")
    print(f"  - Heat Flux: {params['heat_flux']} W/m²")

    # --- Timing the Simulation ---
    print("\n--- Calling the simulation runner. The timer has started. ---")
    
    # Record the precise time just before we start the simulation
    start_time = time.time()

    # Execute the single simulation using the function from our other script
    results = run_single_simulation(
        run_id=run_id,
        params=params,
        base_run_dir=BASE_RUN_DIR,
        final_image_dir=FINAL_IMAGE_DIR
    )

    # Record the precise time just after the simulation finishes
    end_time = time.time()
    
    print("--- Simulation has finished. ---")

    # --- Calculate and Display the Duration ---
    # The total duration is simply the end time minus the start time.
    duration_seconds = end_time - start_time
    
    # Convert the total seconds into a more readable minutes and seconds format
    minutes = int(duration_seconds // 60)
    seconds = int(duration_seconds % 60)

    print("\n" + "="*25)
    print("   Time Test Complete")
    print("="*25)
    print(f"  Simulation Status: {results.get('status', 'unknown_error')}")
    print(f"  Total execution time: {minutes} minutes and {seconds} seconds.")
    print("="*25)
    print("\nWe can now use this measurement to plan our full dataset generation.")

