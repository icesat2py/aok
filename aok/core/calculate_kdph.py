from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd
from scipy.stats import linregress

from aok.core.config import KdConfig

TRACK_COLUMNS = ("srcid", "gt", "spot")


class CalculateKdph:
    """Checkpoint F stage for decay-zone selection and Beer's Law fitting."""

    def __init__(self, config: KdConfig):
        self.config = config

    def find_decay_zone(self, histogram: pd.DataFrame) -> pd.DataFrame:
        frame = histogram.copy().sort_values("zdepth")
        if self.config.decay_zone_threshold > 0:
            peak = float(frame["photon_counts"].max())
            if peak > 0:
                frame.loc[
                    frame["photon_counts"] < self.config.decay_zone_threshold * peak,
                    "photon_counts",
                ] = 0
        frame["log_photon_counts"] = np.log(frame["photon_counts"].replace(0, np.nan))
        return frame.dropna(subset=["zdepth", "log_photon_counts"])

    def fit_beers_law(self, decay_zone: pd.DataFrame) -> dict[str, float | int]:
        if decay_zone.empty or len(decay_zone) < 4:
            return {
                "kd": float("nan"),
                "e0": float("nan"),
                "r_squared": float("nan"),
                "rmse": float("nan"),
                "n_decay_bins": len(decay_zone),
            }

        depths = decay_zone["zdepth"].to_numpy(dtype=np.float64)
        logs = decay_zone["log_photon_counts"].to_numpy(dtype=np.float64)
        fit = linregress(depths, logs)
        kd = float(-fit.slope)
        intercept = float(fit.intercept)
        predicted = intercept - kd * depths
        rmse = float(np.sqrt(np.mean((logs - predicted) ** 2)))
        r_squared = float(fit.rvalue**2) if np.isfinite(fit.rvalue) else float("nan")
        return {
            "kd": kd,
            "e0": float(np.exp(intercept)),
            "r_squared": r_squared,
            "rmse": rmse,
            "n_decay_bins": len(decay_zone),
        }

    def find_breakpoint(self, histogram: pd.DataFrame) -> dict[str, Any]:
        frame = self.find_decay_zone(histogram)
        frame = frame.loc[
            frame["photon_counts"] >= self.config.minimum_photons_per_decay_bin
        ]
        total_photons = int(frame["photon_counts"].sum())
        if total_photons < self.config.minimum_column_photons:
            reason = "insufficient_photons"
        elif len(frame) < self.config.minimum_decay_zone_bins:
            reason = "too_few_decay_bins"
        else:
            reason = None

        if reason:
            return {
                "kd": float("nan"),
                "e0": float("nan"),
                "breakpoint_depth_m": float("nan"),
                "noise_floor": float("nan"),
                "reason": reason,
                "n_decay_bins": len(frame),
            }

        depths = frame["zdepth"].to_numpy(dtype=np.float64)
        logs = frame["log_photon_counts"].to_numpy(dtype=np.float64)
        counts = frame["photon_counts"].to_numpy(dtype=np.float64)
        best_rss = np.inf
        best_index: int | None = None

        for index in range(self.config.minimum_decay_zone_bins, len(frame)):
            if depths[index] < self.config.minimum_breakpoint_depth_m:
                continue
            if depths[index - 1] - depths[0] < self.config.minimum_decay_range_m:
                continue
            if int(counts[:index].sum()) < self.config.minimum_column_photons:
                continue

            decay_fit = linregress(depths[:index], logs[:index])
            predicted = decay_fit.intercept + decay_fit.slope * depths[:index]
            rss_decay = float(np.sum((predicted - logs[:index]) ** 2))
            tail_mean = float(logs[index:].mean())
            rss_tail = float(np.sum((logs[index:] - tail_mean) ** 2))
            rss = rss_decay + rss_tail
            if rss < best_rss:
                best_rss = rss
                best_index = index

        if best_index is None:
            return {
                "kd": float("nan"),
                "e0": float("nan"),
                "breakpoint_depth_m": float("nan"),
                "noise_floor": float("nan"),
                "reason": "no_breakpoint_found",
                "n_decay_bins": len(frame),
            }

        decay_zone = frame.iloc[:best_index]
        fit = self.fit_beers_law(decay_zone)
        kd = float(fit["kd"])
        reason = None
        if not np.isfinite(kd):
            reason = "invalid_fit"
        elif kd < 0:
            reason = "negative_slope"
        elif kd < self.config.minimum_kd:
            reason = "kd_below_reasonableness_minimum"
        elif kd > self.config.maximum_kd:
            reason = "kd_above_reasonableness_maximum"

        tail = frame.iloc[best_index:]
        noise_floor = (
            float(np.exp(float(tail["log_photon_counts"].mean())))
            if not tail.empty
            else float("nan")
        )
        return {
            **fit,
            "kd": float("nan") if reason else kd,
            "breakpoint_depth_m": float(depths[best_index]),
            "noise_floor": noise_floor,
            "reason": reason,
        }

    def fit_bins(
        self,
        photons: pd.DataFrame,
        surface_peaks: pd.DataFrame,
    ) -> pd.DataFrame:
        required = {*TRACK_COLUMNS, "along_track_bin_index", "orthometric_height_m"}
        missing = required.difference(photons.columns)
        if missing:
            raise ValueError(f"Kd fitting requires fields: {sorted(missing)}")

        peak_columns = [*TRACK_COLUMNS, "along_track_bin_index", "surface_height_m"]
        missing_peaks = set(peak_columns).difference(surface_peaks.columns)
        if missing_peaks:
            raise ValueError(f"Surface peaks require fields: {sorted(missing_peaks)}")

        frame = photons.merge(
            surface_peaks[peak_columns],
            on=[*TRACK_COLUMNS, "along_track_bin_index"],
            how="left",
            validate="many_to_one",
        )
        frame["zdepth"] = pd.to_numeric(
            frame["surface_height_m"], errors="coerce"
        ) - pd.to_numeric(frame["orthometric_height_m"], errors="coerce")

        rows: list[dict[str, object]] = []
        for key, group in frame.groupby(
            [*TRACK_COLUMNS, "along_track_bin_index"], observed=True, sort=False
        ):
            key_values = key if isinstance(key, tuple) else (key,)
            key_map = dict(
                zip((*TRACK_COLUMNS, "along_track_bin_index"), key_values, strict=True)
            )
            depths = pd.to_numeric(group["zdepth"], errors="coerce")
            depths = depths[np.isfinite(depths) & (depths >= 0)].copy()
            if depths.empty:
                result: dict[str, object] = {
                    "kd": float("nan"),
                    "e0": float("nan"),
                    "breakpoint_depth_m": float("nan"),
                    "noise_floor": float("nan"),
                    "reason": "insufficient_photons",
                    "n_decay_bins": 0,
                }
            else:
                edges = np.arange(
                    0.0,
                    float(depths.max()) + self.config.vertical_res,
                    self.config.vertical_res,
                )
                counts, edges = np.histogram(depths, bins=edges)
                histogram = pd.DataFrame(
                    {
                        "zdepth": (edges[:-1] + edges[1:]) / 2,
                        "photon_counts": counts,
                    }
                )
                result = self.find_breakpoint(histogram)
            rows.append({**key_map, **result})
        return pd.DataFrame(rows)
