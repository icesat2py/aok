from __future__ import annotations

import numpy as np
import pandas as pd
from scipy.signal import find_peaks
from scipy.stats import norm

from aok.core.config import KdConfig

TRACK_COLUMNS = ("srcid", "gt", "spot")
ALONG_TRACK_COLUMNS = (*TRACK_COLUMNS, "along_track_bin_index")
SURFACE_HEIGHT_COLUMN = "surface_height_m"
SURFACE_SIGMA_COLUMN = "surface_sigma_m"
MIN_SURFACE_PHOTONS = 20
MIN_PEAK_PHOTONS = 10
TRUNCATED_SIGMA_M = 0.4
MIN_OUTLIER_BINS = 2
COS_THETA_TOLERANCE = 1e-6


def _fit_surface_values(
    bin_values: np.ndarray,
    histogram_bins: int,
) -> tuple[float, float]:
    if len(bin_values) < MIN_SURFACE_PHOTONS:
        return float("nan"), float("nan")

    hist, edges = np.histogram(
        bin_values,
        bins=histogram_bins,
        density=True,
        range=(float(np.min(bin_values)), float(np.max(bin_values))),
    )
    centers = (edges[:-1] + edges[1:]) / 2.0
    peaks, _properties = find_peaks(
        hist,
        height=np.max(hist) * 0.3,
        distance=10,
        prominence=np.max(hist) * 0.1,
    )
    if len(peaks) == 0:
        return float("nan"), float("nan")

    surface_peak = centers[int(peaks[np.argmax(hist[peaks])])]
    peak_values = bin_values[
        (bin_values > surface_peak - 1.0) & (bin_values < surface_peak + 1.0)
    ]
    if len(peak_values) <= MIN_PEAK_PHOTONS:
        return float(surface_peak), 0.2

    mu, sigma = norm.fit(peak_values)
    if sigma > TRUNCATED_SIGMA_M:
        half_window = min(2.5 * sigma, 3.0)
        wide_values = bin_values[
            (bin_values > mu - half_window) & (bin_values < mu + half_window)
        ]
        if len(wide_values) > MIN_PEAK_PHOTONS:
            mu, sigma = norm.fit(wide_values)
    return float(mu), float(sigma)


def fit_surface_peaks(
    photons: pd.DataFrame,
    along_track_bins: pd.DataFrame,
    *,
    height_column: str = "orthometric_height_m",
    histogram_bins: int = 100,
) -> pd.DataFrame:
    """Fit the surface Gaussian peak for each along-track bin.

    Reuses ``get_sea_surface_height_adaptive`` in
    ``aok/core/kd_utils/sea_photons_analysis.py``. Returns one row per
    along-track bin with fitted surface height and sigma.
    """
    required = {"along_track_bin_index", "along_track_bin_start_m", *TRACK_COLUMNS}
    missing = required.difference(along_track_bins.columns)
    if missing:
        msg = f"Along-track bins are missing fields: {sorted(missing)}"
        raise ValueError(msg)
    if height_column not in photons.columns:
        msg = f"Photon surface fitting requires '{height_column}'."
        raise ValueError(msg)

    values = pd.to_numeric(photons[height_column], errors="coerce").to_numpy(
        dtype=np.float64
    )
    surface_rows: list[dict[str, object]] = []

    bin_columns = [
        *TRACK_COLUMNS,
        "along_track_bin_index",
        "along_track_bin_start_m",
    ]
    for row in along_track_bins.itertuples(index=False, name=None):
        bin_key = row[: len(bin_columns)]
        photon_row_indices = np.asarray(row[len(bin_columns)], dtype=np.intp)
        bin_values = values[photon_row_indices]
        bin_values = bin_values[np.isfinite(bin_values)]

        surface_height, surface_sigma = _fit_surface_values(
            bin_values,
            histogram_bins,
        )

        surface_row = dict(zip(bin_columns, bin_key, strict=True))
        surface_row[SURFACE_HEIGHT_COLUMN] = surface_height
        surface_row[SURFACE_SIGMA_COLUMN] = surface_sigma
        surface_row["height_column"] = height_column
        surface_rows.append(surface_row)

    surface_peaks = pd.DataFrame(surface_rows)
    if surface_peaks.empty:
        return surface_peaks

    valid = surface_peaks[SURFACE_HEIGHT_COLUMN].dropna()
    if len(valid) >= MIN_OUTLIER_BINS:
        mean = float(valid.mean())
        std = float(valid.std())
        if np.isfinite(std):
            outlier = (surface_peaks[SURFACE_HEIGHT_COLUMN] - mean).abs() > 2.0 * std
            surface_peaks.loc[outlier, SURFACE_HEIGHT_COLUMN] = np.nan
            surface_peaks.loc[outlier, SURFACE_SIGMA_COLUMN] = np.nan

    return surface_peaks


def calculate_depth_below_surface(
    photons: pd.DataFrame,
    surface_peaks: pd.DataFrame,
    *,
    height_column: str = "orthometric_height_m",
) -> pd.DataFrame:
    """Add positive-down depth below the fitted surface for each photon."""
    if height_column not in photons.columns:
        msg = f"Depth calculation requires '{height_column}'."
        raise ValueError(msg)

    required = {*ALONG_TRACK_COLUMNS, SURFACE_HEIGHT_COLUMN}
    missing = required.difference(surface_peaks.columns)
    if missing:
        msg = f"Surface peaks are missing fields: {sorted(missing)}"
        raise ValueError(msg)

    surface_columns = [*ALONG_TRACK_COLUMNS, SURFACE_HEIGHT_COLUMN]
    corrected = photons.merge(
        surface_peaks[surface_columns],
        on=list(ALONG_TRACK_COLUMNS),
        how="left",
        validate="many_to_one",
    )
    height = pd.to_numeric(corrected[height_column], errors="coerce")
    surface = pd.to_numeric(corrected[SURFACE_HEIGHT_COLUMN], errors="coerce")
    corrected["depth_below_surface_m"] = surface - height
    return corrected


def remove_surface_and_wave_photons(
    photons: pd.DataFrame,
    surface_peaks: pd.DataFrame,
    config: KdConfig,
) -> pd.DataFrame:
    """Remove photons within the configured surface/wave exclusion layer."""
    required = {*ALONG_TRACK_COLUMNS, SURFACE_HEIGHT_COLUMN, SURFACE_SIGMA_COLUMN}
    missing = required.difference(surface_peaks.columns)
    if missing:
        msg = f"Surface peaks are missing fields: {sorted(missing)}"
        raise ValueError(msg)

    columns = [*ALONG_TRACK_COLUMNS, SURFACE_HEIGHT_COLUMN, SURFACE_SIGMA_COLUMN]
    filtered = photons.merge(
        surface_peaks[columns],
        on=list(ALONG_TRACK_COLUMNS),
        how="left",
        validate="many_to_one",
    )
    surface = pd.to_numeric(filtered[SURFACE_HEIGHT_COLUMN], errors="coerce")
    sigma = pd.to_numeric(filtered[SURFACE_SIGMA_COLUMN], errors="coerce")
    height = pd.to_numeric(filtered["orthometric_height_m"], errors="coerce")

    trim_depth = np.maximum(2.0 * sigma, config.surface_wave_trim_min_m)
    trim_depth = np.where(
        np.isfinite(trim_depth),
        trim_depth,
        config.surface_wave_trim_min_m,
    )
    keep = (height < surface - trim_depth) & np.isfinite(surface)
    return filtered.loc[keep].copy()


def _water_refractive_index(config: KdConfig) -> tuple[float, float]:
    coefficient_a = -0.000001501562500
    coefficient_b = 0.000000107084865
    coefficient_c = -0.000042759374989
    coefficient_d = -0.000160475520686
    coefficient_e = 1.398067112092424
    n1 = 1.00029
    n2 = (
        coefficient_a * config.refraction_water_temp_c**2
        + coefficient_b * config.refraction_wavelength_nm**2
        + coefficient_c * config.refraction_water_temp_c
        + coefficient_d * config.refraction_wavelength_nm
        + coefficient_e
    )
    return float(n1), float(n2)


def apply_refraction_correction(
    photons: pd.DataFrame,
    surface_peaks: pd.DataFrame,
    config: KdConfig,
) -> pd.DataFrame:
    """Apply the legacy Snell-based refraction geometry correction.

    Reuses ``apply_optional_refraction_correction`` in
    ``aok/core/kd_utils/bathy_processing.py``.
    """
    required_photon = {
        *ALONG_TRACK_COLUMNS,
        "orthometric_height_m",
        "ref_elev",
        "ref_azimuth",
        "reference_photon_lon",
        "reference_photon_lat",
    }
    missing = required_photon.difference(photons.columns)
    if missing:
        msg = f"Refraction correction requires fields: {sorted(missing)}"
        raise ValueError(msg)

    required_surface = {*ALONG_TRACK_COLUMNS, SURFACE_HEIGHT_COLUMN}
    missing = required_surface.difference(surface_peaks.columns)
    if missing:
        msg = f"Surface peaks are missing fields: {sorted(missing)}"
        raise ValueError(msg)

    surface_columns = [*ALONG_TRACK_COLUMNS, SURFACE_HEIGHT_COLUMN]
    corrected = photons.merge(
        surface_peaks[surface_columns],
        on=list(ALONG_TRACK_COLUMNS),
        how="left",
        validate="many_to_one",
    )
    corrected["orthometric_height_m_pre_refraction"] = corrected["orthometric_height_m"]

    n1, n2 = _water_refractive_index(config)

    ref_elev = pd.to_numeric(corrected["ref_elev"], errors="coerce").to_numpy(
        dtype=np.float64
    )
    ref_azimuth = pd.to_numeric(corrected["ref_azimuth"], errors="coerce").to_numpy(
        dtype=np.float64
    )
    height = pd.to_numeric(corrected["orthometric_height_m"], errors="coerce").to_numpy(
        dtype=np.float64
    )
    surface = pd.to_numeric(corrected[SURFACE_HEIGHT_COLUMN], errors="coerce").to_numpy(
        dtype=np.float64
    )
    longitude = pd.to_numeric(
        corrected["reference_photon_lon"], errors="coerce"
    ).to_numpy(dtype=np.float64)
    latitude = pd.to_numeric(
        corrected["reference_photon_lat"], errors="coerce"
    ).to_numpy(dtype=np.float64)

    if np.nanmax(np.abs(ref_elev)) > 2.0 * np.pi:
        ref_elev = np.deg2rad(ref_elev)
    if np.nanmax(np.abs(ref_azimuth)) > 2.0 * np.pi:
        ref_azimuth = np.deg2rad(ref_azimuth)

    valid = (
        np.isfinite(ref_elev)
        & np.isfinite(ref_azimuth)
        & np.isfinite(height)
        & np.isfinite(surface)
        & (height <= surface)
    )

    if np.any(valid):
        theta1 = (np.pi / 2.0) - ref_elev[valid]
        theta2_arg = np.clip((n1 * np.sin(theta1)) / n2, -1.0, 1.0)
        theta2 = np.arcsin(theta2_arg)

        distance = surface[valid] - height[valid]
        cos_theta1 = np.cos(theta1)
        cos_theta1 = np.where(
            np.abs(cos_theta1) < COS_THETA_TOLERANCE,
            np.nan,
            cos_theta1,
        )
        slant = distance / cos_theta1
        surface_range = (slant * n1) / n2
        gamma = (np.pi / 2.0) - theta1
        phi = theta1 - theta2
        path_squared = np.maximum(
            surface_range**2 + slant**2 - 2.0 * surface_range * slant * np.cos(phi),
            0.0,
        )
        path = np.sqrt(path_squared)
        alpha_arg = np.divide(
            surface_range * np.sin(phi),
            path,
            out=np.zeros_like(path),
            where=(path != 0),
        )
        alpha = np.arcsin(np.clip(alpha_arg, -1.0, 1.0))
        beta = gamma - alpha

        horizontal = path * np.cos(beta)
        vertical = path * np.sin(beta)
        east = horizontal * np.sin(ref_azimuth[valid])
        north = horizontal * np.cos(ref_azimuth[valid])

        corrected.loc[valid, "reference_photon_lon"] = longitude[valid] + east
        corrected.loc[valid, "reference_photon_lat"] = latitude[valid] + north
        corrected.loc[valid, "orthometric_height_m"] = height[valid] + vertical

    return corrected


def rebuild_and_refit_surface_after_refraction(
    photons: pd.DataFrame,
    along_track_bins: pd.DataFrame,
    config: KdConfig,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Correct refraction, rebuild histograms, and refit surface peaks."""
    first_pass = fit_surface_peaks(photons, along_track_bins)
    corrected = apply_refraction_correction(photons, first_pass, config)
    corrected_peaks = fit_surface_peaks(
        corrected,
        along_track_bins,
        height_column="orthometric_height_m",
    )
    return corrected, corrected_peaks
