from __future__ import annotations

import numpy as np
import pandas as pd

from aok.core.config import KdConfig
from aok.core.surface_processing import ALONG_TRACK_COLUMNS, SURFACE_HEIGHT_COLUMN

ATL24_SEABED_COLUMN = "ortho_h"
GEBCO_COLUMN = "gebco.value"


def histogram_quality_gate(
    photons: pd.DataFrame,
    surface_peaks: pd.DataFrame,
    config: KdConfig,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Return accepted photons and one quality diagnostic row per along-track bin."""
    required = {*ALONG_TRACK_COLUMNS, "orthometric_height_m"}
    missing = required.difference(photons.columns)
    if missing:
        raise ValueError(f"Histogram quality filtering requires: {sorted(missing)}")

    frame = photons.merge(
        surface_peaks[[*ALONG_TRACK_COLUMNS, SURFACE_HEIGHT_COLUMN, "surface_sigma_m"]],
        on=list(ALONG_TRACK_COLUMNS),
        how="left",
        validate="many_to_one",
    )
    frame["depth_below_surface_m"] = pd.to_numeric(
        frame[SURFACE_HEIGHT_COLUMN], errors="coerce"
    ) - pd.to_numeric(frame["orthometric_height_m"], errors="coerce")

    rows: list[dict[str, object]] = []
    for key, group in frame.groupby(
        list(ALONG_TRACK_COLUMNS), sort=False, observed=True
    ):
        if not isinstance(key, tuple):
            key = (key,)
        key_map = dict(zip(ALONG_TRACK_COLUMNS, key, strict=True))
        depths = pd.to_numeric(group["depth_below_surface_m"], errors="coerce")
        valid = depths[np.isfinite(depths)].to_numpy(dtype=np.float64)
        valid = valid[valid >= 0.0]

        ref_mask = (valid >= config.histogram_quality_reference_min_m) & (
            valid <= config.histogram_quality_reference_max_m
        )
        target_mask = (valid >= config.histogram_quality_depth_min_m) & (
            valid <= config.histogram_quality_depth_max_m
        )
        ref_count = float(ref_mask.sum())
        target_count = float(target_mask.sum())
        ref_width = max(
            config.histogram_quality_reference_max_m
            - config.histogram_quality_reference_min_m,
            0.01,
        )
        target_width = max(
            config.histogram_quality_depth_max_m - config.histogram_quality_depth_min_m,
            0.01,
        )
        ratio = (
            (target_count / target_width) / (ref_count / ref_width)
            if ref_count > 0
            else 0.0
        )

        sigma = float(pd.to_numeric(group["surface_sigma_m"], errors="coerce").median())
        accepted = (
            ratio >= config.histogram_quality_min_ratio
            if config.histogram_quality_enabled
            else True
        )
        if np.isfinite(sigma) and sigma > config.surface_sigma_max_m:
            accepted = False
        reason = None
        if not accepted:
            reason = (
                "surface_sigma_exceeded"
                if np.isfinite(sigma) and sigma > config.surface_sigma_max_m
                else "low_histogram_quality"
            )
        rows.append(
            {
                **key_map,
                "hist_quality_ratio": float(ratio),
                "surface_sigma_m": sigma,
                "hist_quality_accepted": bool(accepted),
                "hist_quality_reason": reason,
            }
        )

    diagnostics = pd.DataFrame(rows)
    if diagnostics.empty:
        return photons.iloc[0:0].copy(), diagnostics
    accepted_keys = set(
        diagnostics.loc[diagnostics["hist_quality_accepted"]]
        .set_index(list(ALONG_TRACK_COLUMNS))
        .index
    )
    keep = frame.set_index(list(ALONG_TRACK_COLUMNS)).index.isin(accepted_keys)
    kept = frame.loc[keep].drop(
        columns=[SURFACE_HEIGHT_COLUMN, "surface_sigma_m", "depth_below_surface_m"]
    )
    return kept.reset_index(drop=True), diagnostics


def apply_seabed_filter(
    photons: pd.DataFrame,
    config: KdConfig,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Apply ATL24/GEBCO seabed filtering and shallow-seabed bin rejection."""
    required = {*ALONG_TRACK_COLUMNS, "orthometric_height_m"}
    missing = required.difference(photons.columns)
    if missing:
        raise ValueError(f"Seabed filtering requires: {sorted(missing)}")

    frame = photons.copy()
    seabed = pd.Series(np.nan, index=frame.index, dtype=np.float64)

    if ATL24_SEABED_COLUMN in frame.columns:
        atl24 = pd.to_numeric(frame[ATL24_SEABED_COLUMN], errors="coerce")
        if "class_ph" in frame.columns:
            atl24 = atl24.mask(
                pd.to_numeric(frame["class_ph"], errors="coerce").ne(40), np.nan
            )
        if "low_confidence_flag" in frame.columns:
            atl24 = atl24.mask(
                pd.to_numeric(frame["low_confidence_flag"], errors="coerce").ne(0),
                np.nan,
            )
        seabed = atl24

    if GEBCO_COLUMN in frame.columns:
        gebco = pd.to_numeric(frame[GEBCO_COLUMN], errors="coerce")
        seabed = seabed.fillna(gebco.where(gebco <= 0.0))

    frame["seafloor_height_m"] = seabed
    frame["seabed_depth_m"] = -seabed
    if frame["seafloor_height_m"].notna().sum() == 0:
        raise ValueError(
            "Neither usable ATL24 bathymetry nor GEBCO seabed is available"
        )

    frame = frame.loc[
        frame["orthometric_height_m"].gt(frame["seafloor_height_m"])
        | frame["seafloor_height_m"].isna()
    ].copy()

    rows: list[dict[str, object]] = []
    for key, group in frame.groupby(
        list(ALONG_TRACK_COLUMNS), sort=False, observed=True
    ):
        if not isinstance(key, tuple):
            key = (key,)
        key_map = dict(zip(ALONG_TRACK_COLUMNS, key, strict=True))
        depth = float(pd.to_numeric(group["seabed_depth_m"], errors="coerce").median())
        accepted = bool(np.isfinite(depth) and depth >= config.minimum_seabed_depth_m)
        rows.append(
            {
                **key_map,
                "seabed_depth_m": depth,
                "shallow_seabed_accepted": accepted,
                "seabed_reason": None if accepted else "shallow_seabed",
            }
        )

    diagnostics = pd.DataFrame(rows)
    if diagnostics.empty:
        return frame.iloc[0:0].copy(), diagnostics
    accepted_keys = set(
        diagnostics.loc[diagnostics["shallow_seabed_accepted"]]
        .set_index(list(ALONG_TRACK_COLUMNS))
        .index
    )
    keep = frame.set_index(list(ALONG_TRACK_COLUMNS)).index.isin(accepted_keys)
    return frame.loc[keep].reset_index(drop=True), diagnostics
