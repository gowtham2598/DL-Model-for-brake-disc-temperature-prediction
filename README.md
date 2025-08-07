# A Deep Learning Surrogate Model for Predicting Brake Disc Temperature

This project develops an end-to-end pipeline to create a deep learning surrogate model. The model is designed to rapidly predict the peak temperature distribution in a ventilated automotive brake disc, replacing slow and computationally expensive Finite Element Analysis (FEA) simulations.

---

## Key Features

- **Automated Geometry Generation:** Programmatically creates 2D designs of ventilated brake discs.
- **High-Fidelity Simulation:** Uses ANSYS MAPDL via the `pyansys` library to run transient thermal analysis for each design.
- **AI-Powered Prediction:** (Future goal) Trains a U-Net Convolutional Neural Network on the simulation data to act as a surrogate model for instant predictions.

---

## Example Simulation Result

Below is an example of the temperature distribution for a hard braking event (Peak Temp: ~450°C) as calculated by the FEA simulation.



---

## Technologies Used

- **Python 3**
- **ANSYS MAPDL** (`pyansys-mapdl-core`)
- **Git & GitHub** for version control
- **NumPy** for numerical operations

---

## How to Run a Simulation

1. Ensure all dependencies are installed in your `venv`.
2. Modify the parameters (like `heat_flux`) inside the main script as needed.
3. Run the primary simulation script from the terminal:
   ```bash
   python test_run_vanes/ansys_test_run_vanes.py