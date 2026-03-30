# utils/bathy_processing.py
import os
import logging
import pandas as pd
import rasterio
import numpy as np
from kd_utils.sea_photons_analysis import (
    get_sea_surface_height_adaptive,
    get_sea_surface_height_static,
    horizontal_vertical_bin_dataset,
)
from rtree import index
from shapely.geometry import box, Point
from scipy.spatial import cKDTree
from scipy.stats import norm


def apply_optional_histogram_quality_filter(
    binned_dataset_sea_surface,
    subsurface_photon_dataset,
    sea_surface_height,
    min_ratio=0.05,
    depth_min=6.0,
    depth_max=7.0,
    reference_depth_min=0.0,
    reference_depth_max=1.0
):
    """
    Optional histogram quality check: keep along-track bins only if enough
    signal remains at the target depth band relative to near-surface signal.

    Flowchart step: 6 — Review histograms for quality: if <5% of signal remains
    at an uncorrected water depth of 6-7 m below the surface, quality-flag this
    along-track bin as low confidence and exclude it from further analyses
    (Possible discard).

    The decay ratio is computed as:
        photon_count_in_depth_band / photon_count_in_reference_band

    This measures how much signal has decayed at depth compared to near the
    surface, consistent with Beer's Law attenuation.

    Parameters
    ----------
    binned_dataset_sea_surface : pd.DataFrame
        Full binned photon dataset with 'lat_bins' and 'photon_height'.
    subsurface_photon_dataset : pd.DataFrame
        Subsurface photon dataset to filter.
    sea_surface_height : list
        Sea surface height per along-track bin.
    min_ratio : float
        Minimum decay ratio to keep a bin (default 0.05 = 5%).
    depth_min : float
        Minimum depth of the quality-check band (default 6.0 m).
    depth_max : float
        Maximum depth of the quality-check band (default 7.0 m).
    reference_depth_min : float
        Minimum depth of the near-surface reference band (default 0.0 m).
    reference_depth_max : float
        Maximum depth of the near-surface reference band (default 1.0 m).
    """
    if subsurface_photon_dataset.empty:
        return subsurface_photon_dataset

    grouped = binned_dataset_sea_surface.groupby(['lat_bins'], observed=False)
    lat_bin_keys = list(grouped.groups.keys())
    if len(lat_bin_keys) != len(sea_surface_height):
        return subsurface_photon_dataset

    quality_df = pd.DataFrame({
        'lat_bins': lat_bin_keys,
        'sea_surface_height': sea_surface_height
    }).dropna(subset=['sea_surface_height']).copy()
    if quality_df.empty:
        return subsurface_photon_dataset.iloc[0:0].copy()

    ratios = []
    for _, row in quality_df.iterrows():
        lat_bin = row['lat_bins']
        surface = row['sea_surface_height']
        bin_data = binned_dataset_sea_surface[binned_dataset_sea_surface['lat_bins'] == lat_bin]
        if bin_data.empty:
            ratios.append(0.0)
            continue

        depth = surface - bin_data['photon_height']
        underwater_mask = depth > 0

        # Reference band: near-surface photon count (incoming signal)
        ref_mask = underwater_mask & (depth >= reference_depth_min) & (depth <= reference_depth_max)
        ref_count = float(ref_mask.sum())
        if ref_count == 0:
            ratios.append(0.0)
            continue

        # Target band: photon count at the check depth
        band_mask = underwater_mask & (depth >= depth_min) & (depth <= depth_max)
        band_count = float(band_mask.sum())

        # Normalize by band width so bands of different sizes are comparable
        ref_width = max(reference_depth_max - reference_depth_min, 0.01)
        band_width = max(depth_max - depth_min, 0.01)
        decay_ratio = (band_count / band_width) / (ref_count / ref_width)

        ratios.append(decay_ratio)

    quality_df['hist_quality_ratio'] = ratios
    valid_bins = set(quality_df.loc[quality_df['hist_quality_ratio'] >= min_ratio, 'lat_bins'].tolist())
    return subsurface_photon_dataset[subsurface_photon_dataset['lat_bins'].isin(valid_bins)].copy()


def compute_surface_sigma(binned_dataset_sea_surface, sea_surface_height):
    """Compute per-bin Gaussian surface sigma from photons near the surface peak.

    Uses a two-pass fit: initial ±1 m window, then expands to ±min(2.5σ, 3 m)
    if the initial sigma > 0.4 m (indicating the ±1 m window truncates the
    distribution).  Returns a dict mapping lat_bin -> sigma (float or NaN).
    Bins with fewer than 10 surface photons get NaN.
    """
    grouped = binned_dataset_sea_surface.groupby(['lat_bins'], observed=False)
    lat_bin_keys = list(grouped.groups.keys())
    if len(lat_bin_keys) != len(sea_surface_height):
        return {}

    sigma_map = {}
    for lat_bin, surface in zip(lat_bin_keys, sea_surface_height):
        if pd.isna(surface):
            continue
        bin_data = binned_dataset_sea_surface[binned_dataset_sea_surface['lat_bins'] == lat_bin]
        if bin_data.empty:
            continue
        peak_data = bin_data[
            (bin_data['photon_height'] > surface - 1.0) &
            (bin_data['photon_height'] < surface + 1.0)
        ]
        if len(peak_data) > 10:
            mu, sigma = norm.fit(peak_data['photon_height'])
            if sigma > 0.4:
                half_win2 = min(2.5 * sigma, 3.0)
                peak_data2 = bin_data[
                    (bin_data['photon_height'] > mu - half_win2) &
                    (bin_data['photon_height'] < mu + half_win2)
                ]
                if len(peak_data2) > 10:
                    _, sigma = norm.fit(peak_data2['photon_height'])
        else:
            sigma = np.nan
        sigma_map[lat_bin] = sigma

    return sigma_map


def apply_optional_surface_sigma_filter(
    binned_dataset_sea_surface,
    subsurface_photon_dataset,
    sea_surface_height,
    sigma_max=0.5
):
    """
    Optional Gaussian surface sigma filter: discard along-track bins if the
    fitted surface Gaussian sigma exceeds sigma_max.

    Flowchart step: 8 — If standard deviation of Gaussian peak is >X m,
    quality-flag this along-track bin as low confidence and discard it
    (addresses surface waves) (Possible discard).
    """
    if subsurface_photon_dataset.empty:
        return subsurface_photon_dataset

    sigma_map = compute_surface_sigma(binned_dataset_sea_surface, sea_surface_height)
    if not sigma_map:
        return subsurface_photon_dataset

    sigma_df = pd.DataFrame(
        list(sigma_map.items()), columns=['lat_bins', 'surface_sigma']
    )
    valid_bins = set(sigma_df.loc[sigma_df['surface_sigma'] <= sigma_max, 'lat_bins'].tolist())
    return subsurface_photon_dataset[subsurface_photon_dataset['lat_bins'].isin(valid_bins)].copy()


def apply_optional_refraction_correction(
    binned_dataset_sea_surface,
    subsurface_photon_dataset,
    sea_surface_height,
    water_temp_c=20.0,
    wavelength_nm=532.0
):
    """
    Optional refraction correction for subsurface photons.
    Updates photon positions/heights using Snell-based geometry.

    Flowchart step: 9 — Compute water depths (distance below surface) and
    correct depths for refraction.
    """
    required_cols = {'lat_bins', 'photon_height', 'ref_elevation', 'ref_azimuth', 'lon', 'lat'}
    if subsurface_photon_dataset.empty or (not required_cols.issubset(set(subsurface_photon_dataset.columns))):
        return subsurface_photon_dataset

    grouped = binned_dataset_sea_surface.groupby(['lat_bins'], observed=False)
    lat_bin_keys = list(grouped.groups.keys())
    if len(lat_bin_keys) != len(sea_surface_height):
        return subsurface_photon_dataset

    surface_df = pd.DataFrame({'lat_bins': lat_bin_keys, 'sea_surface_height': sea_surface_height})
    corrected = subsurface_photon_dataset.merge(surface_df, on='lat_bins', how='left').copy()
    if corrected['sea_surface_height'].isna().all():
        return subsurface_photon_dataset

    corrected['photon_height_pre_refraction'] = corrected['photon_height']
    corrected['lon_pre_refraction'] = corrected['lon']
    corrected['lat_pre_refraction'] = corrected['lat']

    # Refraction index parameterization from legacy module.
    a = -0.000001501562500
    b = 0.000000107084865
    c = -0.000042759374989
    d = -0.000160475520686
    e = 1.398067112092424
    n1 = 1.00029
    n2 = (a * water_temp_c ** 2) + (b * wavelength_nm ** 2) + (c * water_temp_c) + (d * wavelength_nm) + e

    ref_elev = pd.to_numeric(corrected['ref_elevation'], errors='coerce').to_numpy(dtype=float)
    ref_az = pd.to_numeric(corrected['ref_azimuth'], errors='coerce').to_numpy(dtype=float)
    z = pd.to_numeric(corrected['photon_height'], errors='coerce').to_numpy(dtype=float)
    ws = pd.to_numeric(corrected['sea_surface_height'], errors='coerce').to_numpy(dtype=float)
    x = pd.to_numeric(corrected['lon'], errors='coerce').to_numpy(dtype=float)
    y = pd.to_numeric(corrected['lat'], errors='coerce').to_numpy(dtype=float)

    # Convert to radians if values look like degrees.
    if np.nanmax(np.abs(ref_elev)) > (2 * np.pi):
        ref_elev = np.deg2rad(ref_elev)
    if np.nanmax(np.abs(ref_az)) > (2 * np.pi):
        ref_az = np.deg2rad(ref_az)

    valid_mask = np.isfinite(ref_elev) & np.isfinite(ref_az) & np.isfinite(z) & np.isfinite(ws) & (z <= ws)
    if not np.any(valid_mask):
        return subsurface_photon_dataset

    theta1 = (np.pi / 2.0) - ref_elev[valid_mask]
    theta2_arg = (n1 * np.sin(theta1)) / n2
    theta2_arg = np.clip(theta2_arg, -1.0, 1.0)
    theta2 = np.arcsin(theta2_arg)

    D = ws[valid_mask] - z[valid_mask]
    cos_theta1 = np.cos(theta1)
    cos_theta1 = np.where(np.abs(cos_theta1) < 1e-6, np.nan, cos_theta1)
    S = D / cos_theta1
    R = (S * n1) / n2
    Gamma = (np.pi / 2.0) - theta1
    phi = theta1 - theta2
    P_sq = np.maximum(R ** 2 + S ** 2 - 2 * R * S * np.cos(phi), 0.0)
    P = np.sqrt(P_sq)
    alpha_arg = np.divide(R * np.sin(phi), P, out=np.zeros_like(P), where=(P != 0))
    alpha_arg = np.clip(alpha_arg, -1.0, 1.0)
    alpha = np.arcsin(alpha_arg)
    Beta = Gamma - alpha

    DY = P * np.cos(Beta)
    DZ = P * np.sin(Beta)
    DE = DY * np.sin(ref_az[valid_mask])
    DN = DY * np.cos(ref_az[valid_mask])

    x_corr = x[valid_mask] + DE
    y_corr = y[valid_mask] + DN
    z_corr = z[valid_mask] + DZ

    corrected.loc[valid_mask, 'lon'] = x_corr
    corrected.loc[valid_mask, 'lat'] = y_corr
    corrected.loc[valid_mask, 'photon_height'] = z_corr
    return corrected


def apply_sea_surface_flattening(
    subsurface_photon_dataset,
    sea_surface_height,
    lat_bin_keys,
    horizontal_res,
    flattening_window_m=500
):
    """
    Flatten small-bin sea-surface variations to the mean sea level of larger along-track windows.
    This follows the standalone SeaSurfaceFlattening module logic, but is optional.
    """
    if subsurface_photon_dataset.empty:
        return subsurface_photon_dataset

    if len(sea_surface_height) != len(lat_bin_keys):
        return subsurface_photon_dataset

    surface_df = pd.DataFrame({
        'lat_bins': lat_bin_keys,
        'sea_surface_height_local': sea_surface_height
    }).dropna(subset=['sea_surface_height_local']).copy()
    if surface_df.empty:
        return subsurface_photon_dataset

    surface_df['lat_bins_num'] = pd.to_numeric(surface_df['lat_bins'], errors='coerce')
    surface_df = surface_df.dropna(subset=['lat_bins_num'])
    if surface_df.empty:
        return subsurface_photon_dataset

    big_bin_size = max(1, int(round(flattening_window_m / max(horizontal_res, 1))))
    if big_bin_size <= 1:
        logging.warning(
            "Sea surface flattening window (%d m) <= horizontal_res (%d m) → "
            "big_bin_size=1, flattening has no effect. "
            "Use --sea_surface_flattening_window_m > --horizontal_res.",
            flattening_window_m, horizontal_res
        )
    surface_df['big_bin'] = (surface_df['lat_bins_num'].astype(int) // big_bin_size).astype(int)
    mean_surface = (
        surface_df.groupby('big_bin', observed=False)['sea_surface_height_local']
        .mean()
        .rename('sea_surface_height_bigbin_mean')
        .reset_index()
    )
    surface_df = surface_df.merge(mean_surface, on='big_bin', how='left')
    surface_df['sea_surface_flattening_offset'] = (
        surface_df['sea_surface_height_bigbin_mean'] - surface_df['sea_surface_height_local']
    )

    flattened = subsurface_photon_dataset.copy()
    flattened['lat_bins_num'] = pd.to_numeric(flattened['lat_bins'], errors='coerce')
    flattened['big_bin'] = (flattened['lat_bins_num'].fillna(-1).astype(int) // big_bin_size).astype(int)
    flattened = flattened.merge(
        surface_df[['lat_bins', 'sea_surface_height_local', 'sea_surface_height_bigbin_mean', 'sea_surface_flattening_offset']],
        on='lat_bins',
        how='left'
    )
    flattened['photon_height_original'] = flattened['photon_height']
    flattened['photon_height'] = (
        flattened['photon_height'] - flattened['sea_surface_flattening_offset'].fillna(0.0)
    )

    # Re-bin height_bins from flattened photon_height so that downstream
    # Kd calculation (which reads height_bins) uses the corrected depths.
    if 'height_bins' in flattened.columns:
        vertical_res_actual = horizontal_res  # not used; infer from existing bins
        # Infer the vertical resolution from the original height_bins spacing
        orig_bins = pd.to_numeric(flattened['height_bins'], errors='coerce').dropna().unique()
        if len(orig_bins) >= 2:
            sorted_bins = np.sort(orig_bins)
            diffs = np.diff(sorted_bins)
            v_res = float(np.median(diffs[diffs > 0])) if np.any(diffs > 0) else 0.25
        else:
            v_res = 0.25
        h_min = flattened['photon_height'].min()
        h_max = flattened['photon_height'].max()
        n_hbins = max(1, int(round((h_max - h_min) / v_res)))
        bin_edges = np.linspace(h_min, h_max, n_hbins + 1)
        bin_labels = np.round((bin_edges[:-1] + bin_edges[1:]) / 2, decimals=1)
        flattened['height_bins'] = pd.cut(
            flattened['photon_height'], bins=bin_edges, labels=bin_labels,
            include_lowest=True
        )

    return flattened.drop(columns=['lat_bins_num', 'big_bin'], errors='ignore')

# 1. Function to create an R-tree spatial index for raster bounds
def create_spatial_index(gebco_paths):
    """
    Create an R-tree spatial index for raster bounds to quickly find relevant rasters.
    
    Parameters:
        gebco_paths (list): List of paths to GEBCO raster files.
    
    Returns:
        raster_data_dict (dict): Dictionary containing loaded rasters and their respective data.
        spatial_index (rtree.index.Index): R-tree spatial index for raster bounds.
    """
    idx = index.Index()
    raster_data_dict = {}
    for i, path in enumerate(gebco_paths):
        with rasterio.Env(GTIFF_SRS_SOURCE='EPSG'):
            gebco_raster = rasterio.open(path)
            raster_data = gebco_raster.read(1)
            raster_data_dict[path] = (gebco_raster, raster_data)
            bounds = gebco_raster.bounds
            idx.insert(i, (bounds.left, bounds.bottom, bounds.right, bounds.top), obj=path)
    return raster_data_dict, idx

# 2. Function to determine which rasters are needed for a given set of coordinates using spatial index in a batch manner
def get_relevant_rasters_using_index(lons, lats, raster_data_dict, spatial_index):
    """
    Determine which raster datasets are relevant for the given coordinates using spatial index.
    This function uses a more efficient approach by performing a bounding box query for batches of points.
    
    Parameters:
        lons (numpy.ndarray): Array of longitudes.
        lats (numpy.ndarray): Array of latitudes.
        raster_data_dict (dict): Dictionary containing raster datasets and their data.
        spatial_index (rtree.index.Index): R-tree spatial index for raster bounds.
    
    Returns:
        relevant_rasters (list): List of relevant raster datasets and their respective data.
    """
    # Create a bounding box that covers all points
    min_lon, max_lon = lons.min(), lons.max()
    min_lat, max_lat = lats.min(), lats.max()
    bounding_box = box(min_lon, min_lat, max_lon, max_lat)

    # Get all rasters that intersect with the bounding box
    matches = list(spatial_index.intersection((bounding_box.bounds), objects=True))
    relevant_paths = {match.object for match in matches}
    relevant_rasters = [(raster_data_dict[path][0], raster_data_dict[path][1]) for path in relevant_paths]
    return relevant_rasters


# 3. Function to get seafloor elevation from the relevant rasters in a vectorized manner
def get_seafloor_elevation(lons, lats, relevant_rasters):
    """
    Get seafloor elevations for a batch of points based on longitude and latitude from relevant rasters.
    
    Parameters:
        lons (numpy.ndarray): Array of longitudes.
        lats (numpy.ndarray): Array of latitudes.
        relevant_rasters (list): List of relevant raster datasets and their respective data.
    
    Returns:
        seafloor_elevations (numpy.ndarray): Array of seafloor elevations.
    """
    points = np.vstack((lons, lats)).T
    seafloor_elevations = np.full(len(lons), np.nan)
    
    for gebco_raster, raster_data in relevant_rasters:
        # Use rasterio.sample to get values for multiple points in a batch
        values = list(gebco_raster.sample(points))
        for idx, value in enumerate(values):
            if np.isnan(seafloor_elevations[idx]) and value is not None:
                seafloor_elevations[idx] = value[0]
    
    return seafloor_elevations


def query_gebco_seafloor_elevation(sea_photon_dataset, gebco_paths):
    """
    Query GEBCO raster tiles and attach a 'seafloor_elevation' column to the
    photon dataset. Does not remove any rows.

    Flowchart step: 12 — Retrieve GEBCO data (or other regional raster
    bathymetry data) for the region when ATL24 is unavailable or returns no
    matching points.

    Parameters
    ----------
    sea_photon_dataset : pd.DataFrame
        Must contain 'longitude' and 'latitude' columns.
    gebco_paths : list
        Paths to GEBCO GeoTIFF raster files.

    Returns
    -------
    pd.DataFrame
        Input dataset with 'seafloor_elevation' column added (negative = below
        sea level).
    """
    dataset = sea_photon_dataset.copy()
    raster_data_dict, spatial_index = create_spatial_index(gebco_paths)
    lons = dataset['longitude'].values
    lats = dataset['latitude'].values
    relevant_rasters = get_relevant_rasters_using_index(lons, lats, raster_data_dict, spatial_index)
    dataset['seafloor_elevation'] = get_seafloor_elevation(lons, lats, relevant_rasters)
    return dataset


def remove_photons_below_seafloor(sea_photon_dataset):
    """
    Remove photons whose height is at or below the seabed elevation.

    Flowchart step: 13 — Remove data below seabed (seabed defined by ATL24 or
    GEBCO).

    Parameters
    ----------
    sea_photon_dataset : pd.DataFrame
        Must contain 'photon_height' and 'seafloor_elevation' columns.

    Returns
    -------
    pd.DataFrame
        Only rows where photon_height > seafloor_elevation.
    """
    return sea_photon_dataset[
        sea_photon_dataset['photon_height'] > sea_photon_dataset['seafloor_elevation']
    ].copy()


def discard_shallow_seabed_bins(sea_photon_dataset, min_depth_m):
    """
    Discard all along-track bins where the seabed is shallower than the minimum
    depth threshold. Kd is not calculated for these bins; they are labelled as
    low confidence by exclusion.

    Flowchart step: 14 — Discard all photon data in horizontal bins where the
    seabed is <5 m deep; Kd is not calculated for these bins — label discarded
    bins as low confidence.

    Parameters
    ----------
    sea_photon_dataset : pd.DataFrame
        Must contain a 'depth' column (= -seafloor_elevation, positive downward).
    min_depth_m : float
        Minimum seabed depth to retain (e.g., 5.0 m). Bins shallower than this
        are discarded.

    Returns
    -------
    pd.DataFrame
        Only rows where depth >= min_depth_m.
    """
    return sea_photon_dataset[
        sea_photon_dataset['depth'] >= min_depth_m
    ].copy()


# 4. The main process function that ties everything together
def process_seafloor_data(sea_photon_dataset, gebco_paths, Ignore_Subsurface_Height_Thres):
    """
    Query GEBCO bathymetry then apply seabed and shallow-water filters.

    Delegates to three single-step helpers:
      query_gebco_seafloor_elevation  → step 12
      remove_photons_below_seafloor   → step 13
      discard_shallow_seabed_bins     → step 14

    Parameters:
        gebco_paths (list): List of path to GEBCO raster files.
        sea_photon_dataset (pandas.DataFrame): Dataset containing longitude,
            latitude, and photon height.

    Returns:
        filtered_sea_photon_dataset (pandas.DataFrame): Filtered dataset
            containing points above the seafloor in water deeper than threshold.
    """
    dataset = query_gebco_seafloor_elevation(sea_photon_dataset, gebco_paths)  # step 12
    dataset['depth'] = -dataset['seafloor_elevation']
    dataset = remove_photons_below_seafloor(dataset)                           # step 13
    return discard_shallow_seabed_bins(dataset, abs(Ignore_Subsurface_Height_Thres))  # step 14


def load_atl24_points(atl24_file_path):
    """
    Load ATL24 point dataset and normalize to columns: longitude, latitude,
    seafloor_elevation_atl24.

    Flowchart step: 12 — Query ATL24 data for bathymetry match; if no match,
    retrieve GEBCO data (or other regional raster bathymetry data) for region.
    """
    if (not atl24_file_path) or (not os.path.exists(atl24_file_path)):
        return pd.DataFrame(columns=['longitude', 'latitude', 'seafloor_elevation_atl24'])

    lower_path = atl24_file_path.lower()
    if lower_path.endswith(('.h5', '.hdf5')):
        try:
            import h5py
            beams = ['gt1l', 'gt1r', 'gt2l', 'gt2r', 'gt3l', 'gt3r']
            frames = []
            with h5py.File(atl24_file_path, 'r') as f:
                for beam in beams:
                    if beam not in f:
                        continue
                    grp = f[beam]
                    if not all(k in grp for k in ('lon_ph', 'lat_ph', 'ortho_h', 'class_ph')):
                        continue
                    class_ph = grp['class_ph'][:]
                    bathy_mask = class_ph == 40  # ATL24 bathymetry class
                    # Apply low_confidence_flag filter if available
                    if 'low_confidence_flag' in grp:
                        bathy_mask = bathy_mask & (grp['low_confidence_flag'][:] == 0)
                    if bathy_mask.sum() == 0:
                        continue
                    frames.append(pd.DataFrame({
                        'longitude': grp['lon_ph'][:][bathy_mask].astype(float),
                        'latitude':  grp['lat_ph'][:][bathy_mask].astype(float),
                        'seafloor_elevation_atl24': grp['ortho_h'][:][bathy_mask].astype(float),
                    }))
            if not frames:
                return pd.DataFrame(columns=['longitude', 'latitude', 'seafloor_elevation_atl24'])
            return pd.concat(frames, ignore_index=True).dropna()
        except Exception:
            return pd.DataFrame(columns=['longitude', 'latitude', 'seafloor_elevation_atl24'])
    elif lower_path.endswith(('.csv', '.txt')):
        atl24_df = pd.read_csv(atl24_file_path)
    elif lower_path.endswith('.parquet'):
        atl24_df = pd.read_parquet(atl24_file_path)
    elif lower_path.endswith(('.gpkg', '.shp', '.geojson')):
        try:
            import geopandas as gpd
            atl24_gdf = gpd.read_file(atl24_file_path)
            atl24_df = pd.DataFrame(atl24_gdf)
            if ('longitude' not in atl24_df.columns or 'latitude' not in atl24_df.columns) and ('geometry' in atl24_gdf.columns):
                atl24_df['longitude'] = atl24_gdf.geometry.x
                atl24_df['latitude'] = atl24_gdf.geometry.y
        except Exception:
            return pd.DataFrame(columns=['longitude', 'latitude', 'seafloor_elevation_atl24'])
    else:
        return pd.DataFrame(columns=['longitude', 'latitude', 'seafloor_elevation_atl24'])

    lon_candidates = ['longitude', 'lon', 'x', 'LONGITUDE', 'LON']
    lat_candidates = ['latitude', 'lat', 'y', 'LATITUDE', 'LAT']
    elev_candidates = [
        'seafloor_elevation', 'bottom_elevation', 'bathymetry', 'elevation', 'z',
        'depth', 'water_depth'
    ]

    lon_col = next((c for c in lon_candidates if c in atl24_df.columns), None)
    lat_col = next((c for c in lat_candidates if c in atl24_df.columns), None)
    elev_col = next((c for c in elev_candidates if c in atl24_df.columns), None)
    if lon_col is None or lat_col is None or elev_col is None:
        return pd.DataFrame(columns=['longitude', 'latitude', 'seafloor_elevation_atl24'])

    out_df = pd.DataFrame({
        'longitude': pd.to_numeric(atl24_df[lon_col], errors='coerce'),
        'latitude': pd.to_numeric(atl24_df[lat_col], errors='coerce'),
        'atl24_raw_bathy': pd.to_numeric(atl24_df[elev_col], errors='coerce')
    }).dropna(subset=['longitude', 'latitude', 'atl24_raw_bathy']).copy()

    if 'depth' in elev_col.lower() and ('elev' not in elev_col.lower()):
        out_df['seafloor_elevation_atl24'] = -out_df['atl24_raw_bathy'].abs()
    else:
        out_df['seafloor_elevation_atl24'] = out_df['atl24_raw_bathy']

    return out_df[['longitude', 'latitude', 'seafloor_elevation_atl24']]


def process_seafloor_data_atl24(
    sea_photon_dataset,
    atl24_file_path,
    Ignore_Subsurface_Height_Thres,
    max_match_distance_deg=0.01
):
    """
    Match ATL24 bathymetry points to photons, then filter below seafloor and
    shallow bins. Returns filtered dataset and number of matched photons.

    Flowchart steps:
      12 — Query ATL24 data for bathymetry match; if no match, retrieve GEBCO data.
      13 — Remove data below seabed (seabed defined by ATL24 or GEBCO).
      14 — Discard all photon data in horizontal bins where the seabed is <5 m
           deep; Kd is not calculated for these bins — label discarded bins as
           low confidence.
    """
    atl24_points = load_atl24_points(atl24_file_path)
    if atl24_points.empty:
        return sea_photon_dataset, 0

    photon_coords = sea_photon_dataset[['longitude', 'latitude']].to_numpy(dtype=float)
    atl24_coords = atl24_points[['longitude', 'latitude']].to_numpy(dtype=float)
    if len(photon_coords) == 0 or len(atl24_coords) == 0:
        return sea_photon_dataset, 0

    tree = cKDTree(atl24_coords)
    distances, indices = tree.query(photon_coords, k=1, distance_upper_bound=max_match_distance_deg)
    valid_match = np.isfinite(distances) & (indices < len(atl24_points))
    matched_count = int(valid_match.sum())
    if matched_count == 0:
        return sea_photon_dataset, 0

    matched_dataset = sea_photon_dataset.copy()
    matched_dataset['seafloor_elevation'] = np.nan
    matched_dataset.loc[valid_match, 'seafloor_elevation'] = atl24_points['seafloor_elevation_atl24'].to_numpy()[indices[valid_match]]
    matched_dataset = matched_dataset.dropna(subset=['seafloor_elevation']).copy()
    matched_dataset['depth'] = -matched_dataset['seafloor_elevation']

    above_floor = remove_photons_below_seafloor(matched_dataset)                          # step 13
    filtered_dataset = discard_shallow_seabed_bins(above_floor, abs(Ignore_Subsurface_Height_Thres))  # step 14
    return filtered_dataset, matched_count


def rebuild_and_refit_surface_after_refraction(
    binned_dataset_sea_surface,
    sea_surface_height,
    water_temp_c,
    wavelength_nm,
    horizontal_res,
    vertical_res,
):
    """
    Apply refraction correction to the full binned dataset, rebuild histograms
    on the corrected depths, and re-fit the Gaussian surface peak.

    Flowchart steps:
      10 — Re-build histograms based on corrected depths
           (apply_optional_refraction_correction → horizontal_vertical_bin_dataset).
      11 — Re-fit Gaussian curve to surface to identify surface peak; compute
           standard deviation and remove histogram data within three standard
           deviations (get_sea_surface_height_adaptive on the rebinned data).

    Parameters
    ----------
    binned_dataset_sea_surface : pd.DataFrame
        Full binned photon dataset before refraction correction.
    sea_surface_height : list
        Per-bin surface heights from step 7.
    water_temp_c : float
        Water temperature for the refraction index calculation.
    wavelength_nm : float
        Laser wavelength (nm) for the refraction index calculation.
    horizontal_res : float
        Along-track bin size (m) for histogram rebuild.
    vertical_res : float
        Vertical bin size (m) for histogram rebuild.

    Returns
    -------
    tuple
        (sea_surface_height, sea_surface_height_abnormal_label,
         solo_sea_surface_label, subsurface_photon_dataset) — same 4-tuple as
        get_sea_surface_height_adaptive.
    """
    corrected_full_dataset = apply_optional_refraction_correction(
        binned_dataset_sea_surface,
        binned_dataset_sea_surface.copy(),
        sea_surface_height,
        water_temp_c=water_temp_c,
        wavelength_nm=wavelength_nm,
    )
    rebinned_corrected = horizontal_vertical_bin_dataset(   # step 10
        corrected_full_dataset, horizontal_res, vertical_res
    )
    return get_sea_surface_height_adaptive(rebinned_corrected)  # step 11


# 5. The function to get the subsurface photon dataset
def get_subsurface_photon(
    binned_dataset_sea_surface,
    GEBCO_paths,
    subsurface_thresh,
    Ignore_Subsurface_Height_Thres,
    use_atl24_filter=False,
    atl24_file_path='',
    atl24_max_match_distance_deg=0.01,
    use_gebco_filter=False,
    apply_histogram_quality_filter=False,
    histogram_quality_min_ratio=0.05,
    histogram_quality_depth_min=6.0,
    histogram_quality_depth_max=7.0,
    histogram_quality_ref_depth_min=0.0,
    histogram_quality_ref_depth_max=1.0,
    apply_surface_sigma_filter=False,
    surface_sigma_max=0.5,
    apply_refraction_correction=False,
    refraction_water_temp_c=20.0,
    refraction_wavelength_nm=532.0,
    apply_post_refraction_refit=False,
    apply_flattening=False,
    flattening_window_m=500,
    horizontal_res=500,
    vertical_res=0.25
):
    """
    Orchestrate per-beam subsurface photon extraction and all optional quality filters.

    Flowchart steps executed in order:
      7  — Fit Gaussian curve to identify surface elevation; compute std dev of
           Gaussian peak (via get_sea_surface_height_adaptive).
      6  — Review histograms for quality; quality-flag low-confidence bins and
           exclude (optional, apply_histogram_quality_filter).
      8  — If Gaussian std dev > X m, quality-flag and discard bin (optional,
           apply_surface_sigma_filter).
      9  — Compute water depths and correct for refraction (optional,
           apply_refraction_correction).
      10 — Re-build histograms based on corrected depths (optional,
           apply_post_refraction_refit → rebuild_and_refit_surface_after_refraction).
      11 — Re-fit Gaussian curve to identify surface peak; remove histogram data
           within three standard deviations (optional,
           rebuild_and_refit_surface_after_refraction).
      12 — Query ATL24 / retrieve GEBCO bathymetry data (optional,
           use_atl24_filter / use_gebco_filter).
      13 — Remove data below seabed (optional).
      14 — Discard bins where seabed < 5 m deep; label as low confidence
           (applied unconditionally via Ignore_Subsurface_Height_Thres).
    """
    # adaptive threshold
    sea_surface_height, sea_surface_label, solo_sea_surface_label, subsurface_photon_dataset = \
        get_sea_surface_height_adaptive(binned_dataset_sea_surface)

    # Always compute per-bin surface sigma for quality flagging and wave-adaptive fit
    sigma_map = compute_surface_sigma(binned_dataset_sea_surface, sea_surface_height)

    if apply_histogram_quality_filter:
        subsurface_photon_dataset = apply_optional_histogram_quality_filter(
            binned_dataset_sea_surface,
            subsurface_photon_dataset,
            sea_surface_height,
            min_ratio=histogram_quality_min_ratio,
            depth_min=histogram_quality_depth_min,
            depth_max=histogram_quality_depth_max,
            reference_depth_min=histogram_quality_ref_depth_min,
            reference_depth_max=histogram_quality_ref_depth_max
        )

    if apply_surface_sigma_filter:
        subsurface_photon_dataset = apply_optional_surface_sigma_filter(
            binned_dataset_sea_surface,
            subsurface_photon_dataset,
            sea_surface_height,
            sigma_max=surface_sigma_max
        )

    if apply_refraction_correction:
        subsurface_photon_dataset = apply_optional_refraction_correction(
            binned_dataset_sea_surface,
            subsurface_photon_dataset,
            sea_surface_height,
            water_temp_c=refraction_water_temp_c,
            wavelength_nm=refraction_wavelength_nm
        )
        if apply_post_refraction_refit:
            sea_surface_height, sea_surface_label, solo_sea_surface_label, subsurface_photon_dataset = \
                rebuild_and_refit_surface_after_refraction(   # steps 10 & 11
                    binned_dataset_sea_surface,
                    sea_surface_height,
                    water_temp_c=refraction_water_temp_c,
                    wavelength_nm=refraction_wavelength_nm,
                    horizontal_res=horizontal_res,
                    vertical_res=vertical_res,
                )

    # Apply minimum depth threshold unconditionally — keeps photons at height
    # >= Ignore_Subsurface_Height_Thres regardless of whether GEBCO/ATL24 is on.
    # Without this, deep noise photons (down to -70 m) contaminate the Beer's Law fit
    # and produce near-zero Kd values, especially at shallow turbid sites.
    subsurface_photon_dataset = subsurface_photon_dataset[
        subsurface_photon_dataset['photon_height'] >= Ignore_Subsurface_Height_Thres
    ].copy()

    if use_atl24_filter:
        atl24_filtered, atl24_match_count = process_seafloor_data_atl24(
            subsurface_photon_dataset,
            atl24_file_path,
            abs(Ignore_Subsurface_Height_Thres),
            max_match_distance_deg=atl24_max_match_distance_deg
        )
        if atl24_match_count > 0:
            filtered_seafloor_subsurface_photon_dataset = atl24_filtered
        elif use_gebco_filter:
            filtered_seafloor_subsurface_photon_dataset = process_seafloor_data(
                subsurface_photon_dataset, GEBCO_paths, abs(Ignore_Subsurface_Height_Thres)
            )
        else:
            filtered_seafloor_subsurface_photon_dataset = subsurface_photon_dataset
    elif use_gebco_filter:
        filtered_seafloor_subsurface_photon_dataset = process_seafloor_data(
            subsurface_photon_dataset, GEBCO_paths, abs(Ignore_Subsurface_Height_Thres)
        )
    else:
        filtered_seafloor_subsurface_photon_dataset = subsurface_photon_dataset

    if apply_flattening:
        lat_bin_keys = list(
            binned_dataset_sea_surface.groupby(['lat_bins'], observed=False).groups.keys()
        )
        filtered_seafloor_subsurface_photon_dataset = apply_sea_surface_flattening(
            filtered_seafloor_subsurface_photon_dataset,
            sea_surface_height,
            lat_bin_keys,
            horizontal_res=horizontal_res,
            flattening_window_m=flattening_window_m
        )
    # Attach per-bin surface_sigma as a quality flag column
    filtered_seafloor_subsurface_photon_dataset = filtered_seafloor_subsurface_photon_dataset.copy()
    if sigma_map:
        filtered_seafloor_subsurface_photon_dataset['surface_sigma'] = \
            filtered_seafloor_subsurface_photon_dataset['lat_bins'].map(sigma_map)
    else:
        filtered_seafloor_subsurface_photon_dataset['surface_sigma'] = np.nan

    return sea_surface_height, sea_surface_label, filtered_seafloor_subsurface_photon_dataset


# Main processing function to apply the subsurface photon filtering beam-by-beam
def process_subsurface_photon_filtering(
    binned_dataset_sea_surface,
    GEBCO_paths,
    subsurface_thresh,
    Ignore_Subsurface_Height_Thres,
    use_atl24_filter=False,
    atl24_file_path='',
    atl24_max_match_distance_deg=0.01,
    use_gebco_filter=False,
    apply_histogram_quality_filter=False,
    histogram_quality_min_ratio=0.05,
    histogram_quality_depth_min=6.0,
    histogram_quality_depth_max=7.0,
    histogram_quality_ref_depth_min=0.0,
    histogram_quality_ref_depth_max=1.0,
    apply_surface_sigma_filter=False,
    surface_sigma_max=0.5,
    apply_refraction_correction=False,
    refraction_water_temp_c=20.0,
    refraction_wavelength_nm=532.0,
    apply_post_refraction_refit=False,
    apply_flattening=False,
    flattening_window_m=500,
    horizontal_res=500,
    vertical_res=0.25
):
    """
    Beam-by-beam wrapper that calls get_subsurface_photon for every beam and
    concatenates the results.

    Flowchart steps 6–14 are all executed inside this function (delegated to
    get_subsurface_photon per beam). See get_subsurface_photon for the
    step-by-step breakdown.
    """
    # Initialize lists to store results for each beam
    sea_surface_heights = []
    sea_surface_labels = []
    filtered_beam_datasets = []

    # Group the binned dataset by 'beam_id' and process each group separately
    for beam_id, beam_data in binned_dataset_sea_surface.groupby('beam_id'):
        print(f'Processing subsurface filtering for beam: {beam_id}')

        # Apply get_subsurface_photon to the current beam's dataset
        sea_surface_height, sea_surface_label, filtered_seafloor_subsurface_photon_dataset = \
            get_subsurface_photon(
                beam_data,
                GEBCO_paths,
                subsurface_thresh,
                Ignore_Subsurface_Height_Thres,
                use_atl24_filter=use_atl24_filter,
                atl24_file_path=atl24_file_path,
                atl24_max_match_distance_deg=atl24_max_match_distance_deg,
                use_gebco_filter=use_gebco_filter,
                apply_histogram_quality_filter=apply_histogram_quality_filter,
                histogram_quality_min_ratio=histogram_quality_min_ratio,
                histogram_quality_depth_min=histogram_quality_depth_min,
                histogram_quality_depth_max=histogram_quality_depth_max,
                histogram_quality_ref_depth_min=histogram_quality_ref_depth_min,
                histogram_quality_ref_depth_max=histogram_quality_ref_depth_max,
                apply_surface_sigma_filter=apply_surface_sigma_filter,
                surface_sigma_max=surface_sigma_max,
                apply_refraction_correction=apply_refraction_correction,
                refraction_water_temp_c=refraction_water_temp_c,
                refraction_wavelength_nm=refraction_wavelength_nm,
                apply_post_refraction_refit=apply_post_refraction_refit,
                apply_flattening=apply_flattening,
                flattening_window_m=flattening_window_m,
                horizontal_res=horizontal_res,
                vertical_res=vertical_res
            )

        # Append each result to the lists
        sea_surface_heights.append(sea_surface_height)
        sea_surface_labels.append(sea_surface_label)
        filtered_beam_datasets.append(filtered_seafloor_subsurface_photon_dataset)

    # Combine all filtered beam datasets into a single DataFrame
    combined_filtered_dataset = pd.concat(filtered_beam_datasets, ignore_index=True)
    
    return sea_surface_heights, sea_surface_labels, combined_filtered_dataset
