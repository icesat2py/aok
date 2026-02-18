# icesat-2_kdph_py


This repository contains Python code developed in collaboration to replicate the functionality of the original MATLAB scripts (https://github.com/emilyeidam/icesat-2_kdph
) by Dr. Emily Eidam (emily.eidam@oregonstate.edu). The code facilitates processing ICESat-2 data to calculate the diffuse attenuation coefficient (Kd) based on space-based lidar photon profiles, following methods described in the original MATLAB code. Please cite appropriately both Python and the MATLAB version under the GNU GPLv3 license if you use this code in your research.

## Repository Structure

Current structure:

```text
icesat-2_kdph_py/
+-- main.py
+-- config.py
+-- requirements.txt
+-- README.md
+-- kd_utils/
    +-- __init__.py
    +-- data_processing.py
    +-- sea_photons_analysis.py
    +-- bathy_processing.py
    +-- Kd_analysis.py
    +-- interpolation.py
    +-- visualization.py
    +-- sliderule_adapter.py
    +-- SeaSurfaceFlattening.py
    +-- SolarBckgrd/
```

Key modules:

- `main.py`: End-to-end pipeline entrypoint for local ATL03 workflows.
- `config.py`: All CLI switches, paths, and thresholds.
- `kd_utils/data_processing.py`: ATL03 ingestion, land/sea masking, optional pre-filters.
- `kd_utils/sea_photons_analysis.py`: Binning and sea-surface detection.
- `kd_utils/bathy_processing.py`: Subsurface filtering and optional gap steps (GEBCO/ATL24/refraction/etc.).
- `kd_utils/Kd_analysis.py`: Kd fitting.
- `kd_utils/sliderule_adapter.py`: SlideRule ATL03 fetch + conversion to framework schema for notebook/script imports.

### Getting Started

### Prerequisites

- Python 3.x
- Libraries: `numpy`, `pandas`, `scipy`, `h5py`, `matplotlib`
- Ensure you have ICESat-2 ATL03 `.h5` files available in the appropriate directory, as specified in `config.py`, and also refers to the original MATLAB code.

### Installation

1. Clone the repository:

   ```bash
   git clone https://github.com/ChaoEcohydroRS/icesat-2_kdph_py.git
   cd IS2_Kd_Proj
   ```


2. Install the required packages:
   ```
   pip install -r requirements.txt
   ```

3. Ensure .h5 files are placed in the appropriate default folder structure.

### Usage
1. Edit the config.py file to set up file paths and any parameters.
2. Run the entire workflow through main.py:

   ```bash
   python main.py
   ```

### SlideRule Ingestion (Notebook Import Path)

You can reuse the same framework without local ATL03 `.h5` files by importing the SlideRule adapter:

```python
from kd_utils.sliderule_adapter import fetch_and_prepare_sliderule_dataset
from kd_utils.sea_photons_analysis import process_sea_photon_binning
from kd_utils.bathy_processing import process_subsurface_photon_filtering
from kd_utils.Kd_analysis import process_kd_calculation

region = [
    {"lon": -84.029, "lat": 29.732},
    {"lon": -84.029, "lat": 29.954},
    {"lon": -83.969, "lat": 29.954},
    {"lon": -83.969, "lat": 29.732},
    {"lon": -84.029, "lat": 29.732},
]

sea_photon_dataset = fetch_and_prepare_sliderule_dataset(
    region=region,
    t0="2025-05-22T00:00:00Z",
    t1="2025-05-24T00:00:00Z",
    rgt=1033,
    strong_beams_only=True,
)

binned = process_sea_photon_binning(sea_photon_dataset, horizontal_res=500, vertical_res=0.25)
sea_h, sea_lbl, subsurface = process_subsurface_photon_filtering(
    binned, GEBCO_paths=[], subsurface_thresh=1.0, Ignore_Subsurface_Height_Thres=-6
)
kd_df = process_kd_calculation(subsurface)
```

This path reuses your existing processing framework; only ingestion switches from local HDF5 to SlideRule API.

### Optional Gap Steps (Sensitivity On/Off)

All extra processing steps are optional and disabled by default.

- IR/AP proxy photon filtering:
  ```bash
  python main.py --enable_ir_ap_filter
  ```
- Solar background filtering:
  ```bash
  python main.py --enable_solar_background_filter
  ```
- GEBCO seafloor filtering:
  ```bash
  python main.py --enable_gebco_filter
  ```
- ATL24-first with GEBCO fallback:
  ```bash
  python main.py --enable_atl24_filter --atl24_file path/to/atl24_points.csv --enable_gebco_filter
  ```
- Sea surface flattening:
  ```bash
  python main.py --enable_sea_surface_flattening
  ```
- Convex hull reasonableness filter:
  ```bash
  python main.py --enable_convex_hull_filter
  ```
- Paired-beam combine before Kd fit:
  ```bash
  python main.py --enable_paired_beam_combine
  ```
- Histogram quality filter (<5% signal at 6-7 m depth band):
  ```bash
  python main.py --enable_histogram_quality_filter
  ```
- Surface Gaussian sigma filter:
  ```bash
  python main.py --enable_surface_sigma_filter
  ```
- Refraction correction:
  ```bash
  python main.py --enable_refraction_correction
  ```
- Post-refraction rebuild + re-fit:
  ```bash
  python main.py --enable_refraction_correction --enable_post_refraction_refit
  ```

### Gap Implementation Progress

The flowchart gaps are being implemented one-by-one with optional switches.

- [x] Gap 1: Remove photons flagged as IR/AP (proxy implementation via `quality_ph` and `photon_conf`)
  - Switch: `--enable_ir_ap_filter`
  - Tuning: `--ir_ap_quality_max`, `--ir_ap_min_signal_conf`
- [x] Gap 2: Histogram quality review (<5% signal at 6-7 m)
  - Switch: `--enable_histogram_quality_filter`
  - Tuning:
    - `--histogram_quality_min_ratio` (default `0.05`)
    - `--histogram_quality_depth_min` (default `6.0`)
    - `--histogram_quality_depth_max` (default `7.0`)
- [x] Gap 3: Discard bins with high surface Gaussian std dev
  - Switch: `--enable_surface_sigma_filter`
  - Tuning: `--surface_sigma_max` (default `0.5`)
- [x] Gap 4: Refraction correction integration
  - Switch: `--enable_refraction_correction`
  - Tuning:
    - `--refraction_water_temp_c` (default `20.0`)
    - `--refraction_wavelength_nm` (default `532.0`)
- [x] Gap 5: Rebuild histogram and re-fit after refraction
  - Switch: `--enable_post_refraction_refit` (requires `--enable_refraction_correction`)
- [x] Gap 6: ATL24 query + fallback orchestration
  - Switch: `--enable_atl24_filter`
  - Note: current implementation uses local ATL24 point files provided via `--atl24_file`.
  - Inputs:
    - `--atl24_file` (CSV/Parquet/GPKG/SHP with lon/lat + bathymetry field)
    - `--atl24_max_match_distance_deg` (default `0.01`)
  - Fallback: if ATL24 has no usable matches and `--enable_gebco_filter` is on, GEBCO filtering is used.
- [x] Gap 7: Combine paired beams
  - Switch: `--enable_paired_beam_combine`
  - Method: maps left/right beams to `gt1_pair`, `gt2_pair`, `gt3_pair` and re-bins by `relative_AT_dist` using `horizontal_res`.

### Citation
If you use this code, please cite:

Eidam, E.F., K. Bisson, C. Wang, C. Walker, and A. Gibbons (2024). ICESat-2 and ocean particulates: A roadmap for calculating Kd from space-based lidar photon profiles. Remote Sensing of Environment. Vol. 311. https://doi.org/10.1016/j.rse.2024.114222

### License
This project is licensed under the GNU GPLv3 license.

