from __future__ import annotations

import numpy as np
import pandas as pd

from aok.core.config import KdConfig

MIN_DAYTIME_PHOTONS = 10


def estimate_solar_background(
    photons: pd.DataFrame,
    *,
    day_threshold: float = 6.0,
    median_window_deg: float = 10.0,
    solar_elevation_column: str = "solar_elevation",
    background_rate_column: str = "background_rate",
) -> pd.DataFrame:
    """Estimate expected atmospheric background from the legacy rolling median.

    Reuses ``apply_optional_solar_background_filter`` in
    ``aok/core/kd_utils/data_processing.py``. The result is stored in
    ``expected_solar_background`` on the photon table.
    """
    if solar_elevation_column not in photons.columns:
        msg = f"Expected column '{solar_elevation_column}' for solar background."
        raise ValueError(msg)
    if background_rate_column not in photons.columns:
        msg = f"Expected column '{background_rate_column}' for solar background."
        raise ValueError(msg)

    solar_elevation = pd.to_numeric(photons[solar_elevation_column], errors="coerce")
    background_rate = pd.to_numeric(photons[background_rate_column], errors="coerce")
    photons["expected_solar_background"] = np.nan

    daytime_mask = (
        (solar_elevation >= day_threshold)
        & np.isfinite(solar_elevation)
        & np.isfinite(background_rate)
    )
    daytime_positions = np.flatnonzero(daytime_mask.to_numpy(dtype=bool))
    if len(daytime_positions) < MIN_DAYTIME_PHOTONS:
        return photons

    elevation = np.asarray(
        solar_elevation.iloc[daytime_positions].clip(lower=day_threshold, upper=90.0),
        dtype=np.float64,
    )
    bg_rates = np.asarray(background_rate.iloc[daytime_positions], dtype=np.float64)
    valid = np.isfinite(elevation) & np.isfinite(bg_rates)
    daytime_positions = daytime_positions[valid]
    elevation = elevation[valid]
    bg_rates = bg_rates[valid]
    if elevation.size == 0:
        return photons

    order = np.argsort(elevation)
    daytime_positions = daytime_positions[order]
    elevation = elevation[order]
    bg_rates = bg_rates[order]

    half_window = median_window_deg / 2.0
    bin_step = 0.1
    bin_centers = np.arange(elevation[0], elevation[-1] + bin_step, bin_step)
    bin_medians = np.full(len(bin_centers), np.nan, dtype=np.float64)

    for index, center in enumerate(bin_centers):
        low = np.searchsorted(elevation, center - half_window, side="left")
        high = np.searchsorted(elevation, center + half_window, side="right")
        if low < high:
            bin_medians[index] = np.median(bg_rates[low:high])

    bin_indices = np.searchsorted(bin_centers, elevation, side="right") - 1
    bin_indices = np.clip(bin_indices, 0, len(bin_centers) - 1)
    expected_background = bin_medians[bin_indices]

    expected_column = photons.columns.get_loc("expected_solar_background")
    photons.iloc[daytime_positions, expected_column] = expected_background
    return photons


def filter_solar_background_photons(
    photons: pd.DataFrame,
    config: KdConfig,
    *,
    solar_elevation_column: str = "solar_elevation",
    background_rate_column: str = "background_rate",
    signal_confidence_column: str = "atl03_cnf",
) -> pd.DataFrame:
    """Remove noisy daytime photons unless confidence meets the threshold.

    Reuses the keep rule in ``apply_optional_solar_background_filter``:
    keep photons that are not noisy, or whose confidence is at least
    ``min_signal_conf``.
    """
    required = {
        "expected_solar_background",
        solar_elevation_column,
        background_rate_column,
    }
    if signal_confidence_column not in photons.columns:
        if "photon_conf" in photons.columns:
            signal_confidence_column = "photon_conf"
        else:
            msg = "Solar background filtering requires a signal confidence column."
            raise ValueError(msg)
    required.add(signal_confidence_column)
    missing = required.difference(photons.columns)
    if missing:
        msg = f"Solar background filtering requires columns: {sorted(missing)}"
        raise ValueError(msg)

    solar_elevation = pd.to_numeric(photons[solar_elevation_column], errors="coerce")
    background_rate = pd.to_numeric(photons[background_rate_column], errors="coerce")
    expected_background = pd.to_numeric(
        photons["expected_solar_background"], errors="coerce"
    )
    confidence = pd.to_numeric(photons[signal_confidence_column], errors="coerce")

    noisy = (
        (solar_elevation >= config.solar_elev_threshold)
        & np.isfinite(background_rate)
        & np.isfinite(expected_background)
        & (background_rate >= expected_background * config.solar_bg_noise_multiplier)
    )
    keep = (~noisy) | (confidence >= config.solar_bg_min_signal_conf)
    return photons.loc[keep].copy()
