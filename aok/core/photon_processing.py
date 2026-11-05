from __future__ import annotations

from collections.abc import Sequence
from typing import cast

import numpy as np
import pandas as pd

TRACK_COLUMNS = ("srcid", "gt", "spot")


def _single_sample(value: object) -> object:
    if isinstance(value, np.ndarray):
        return cast(object, value.reshape(-1)[0])
    if isinstance(value, (list, tuple)):
        return cast(Sequence[object], value)[0]
    return value


def geoidal_to_orthometric_ht(photons: pd.DataFrame) -> pd.DataFrame:
    """Add orthometric height in meters using the legacy geoid correction.

    Refactors ``create_photon_dataframe`` in ``kd_utils/data_processing.py``;
    retains its ``h_ph - geoid`` calculation for SlideRule dataframe input.
    """
    missing = {"h_ph", "geoid"}.difference(photons.columns)
    if missing:
        msg = f"Photon height correction requires fields: {sorted(missing)}"
        raise ValueError(msg)

    height = pd.to_numeric(photons["h_ph"], errors="coerce")
    geoid = pd.to_numeric(photons["geoid"], errors="coerce")
    photons["orthometric_height_m"] = height - geoid
    return photons


def ht_to_pos_depth(
    photons: pd.DataFrame,
    height_column: str = "orthometric_height_m",
) -> pd.DataFrame:
    """Add positive-down depth in meters from the specified height column."""
    photons["depth_m"] = -pd.to_numeric(photons[height_column], errors="coerce")
    return photons


# AI - are the GEBCO values coming in with arrays of multiple values?
def normalize_gebco_samples(
    photons: pd.DataFrame,
    sample_column: str = "gebco.value",
) -> pd.DataFrame:
    """Convert SlideRule's single GEBCO sample per photon to scalar meters."""
    photons[sample_column] = pd.to_numeric(
        photons[sample_column].map(_single_sample), errors="coerce"
    )
    return photons

def filter_land_photons(
    photons: pd.DataFrame,
    land_mask_column: str = "gebco.value",
) -> pd.DataFrame:
    """Keep ocean photons using a negative-water-depth mask column.

    The default GEBCO convention is supported by
    ``aok/tests/integration/kd_ref.csv``.
    """
    return photons.loc[photons[land_mask_column].lt(0)].copy()


def assign_along_track_bins(photons: pd.DataFrame, xbin: float) -> pd.DataFrame:
    """Add fixed-width along-track bin indices and start distances in meters."""
    distance = pd.to_numeric(photons["x_atc"], errors="coerce")
    track_origin = distance.groupby(
        [photons[column] for column in TRACK_COLUMNS], sort=False
    ).transform("min")
    photons["along_track_bin_index"] = np.floor(
        (distance - track_origin) / xbin
    ).astype("Int64")
    photons["along_track_bin_start_m"] = (
        track_origin + photons["along_track_bin_index"] * xbin
    )
    return photons


def histogram_bin_photon_count(
    photons: pd.DataFrame,
    value_column: str,
    bin_edges: Sequence[float],
) -> pd.DataFrame:
    """Build a histogram per track and along-track bin from photon values.

    Histogram binning is computed here, not stored as per-photon bin indices.
    ``value_column`` and ``bin_edges`` can vary between processing stages.
    This adapts the count grouping in ``get_sea_surface_height_*`` from
    ``kd_utils/sea_photons_analysis.py``.
    """
    histogram_columns = [
        *TRACK_COLUMNS,
        "along_track_bin_index",
        "along_track_bin_start_m",
    ]
    bin_edges_array = np.asarray(bin_edges, dtype=np.float64)
    histogram_rows: list[dict[str, object]] = []
    for histogram_key, group in photons.groupby(
        histogram_columns,
        observed=True,
        sort=False,
    ):
        values = pd.to_numeric(group[value_column], errors="coerce").dropna()
        counts, edges = np.histogram(
            np.asarray(values, dtype=np.float64),
            bins=bin_edges_array,
        )
        histogram_rows.append(
            {
                **dict(zip(histogram_columns, histogram_key, strict=True)),
                "histogram_value_column": value_column,
                "histogram_bin_edges": edges,
                "photon_counts_by_bin": counts,
            }
        )

    return pd.DataFrame(histogram_rows)