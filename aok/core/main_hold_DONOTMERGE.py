import glob
import logging
import os
import re
import sys

from config import get_args
from kd_utils.bathy_processing import process_subsurface_photon_filtering
from kd_utils.data_processing import (
    Extract_sea_photons,
    apply_optional_ir_ap_filter,
    apply_optional_solar_background_filter,
    filter_photon_dataset_by_hull_area,
    load_data,
)
from kd_utils.Kd_analysis import process_kd_calculation
from kd_utils.sea_photons_analysis import process_sea_photon_binning
from kd_utils.visualization import (
    plot_convex_hulls,
    plot_kd_photons,
    plot_photon_quality_flags,
)
import pandas as pd

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


PAIR_ID_MAP = {
    "gt1l": "gt1_pair",
    "gt1r": "gt1_pair",
    "gt2l": "gt2_pair",
    "gt2r": "gt2_pair",
    "gt3l": "gt3_pair",
    "gt3r": "gt3_pair",
}


# Changes for slide rule <- should be changed to filter df
def get_target_beams(all_beams, beam_attrs, target_beams_arg):
    strong_beams = [
        gtx
        for gtx in all_beams
        if beam_attrs[gtx]["atlas_beam_type"].decode("utf-8") == "strong"
    ]
    if not target_beams_arg:
        return strong_beams[:1]  # auto-select first strong beam

    requested = [b.strip() for b in target_beams_arg.split(",") if b.strip()]
    return [b for b in requested if b in strong_beams]


def optionally_combine_paired_beams_for_kd(dataset, horizontal_res, enabled=False):
    """
    Optionally combine left/right beams into pair groups before Kd fitting.
    Uses shared along-track bins from relative_AT_dist when available.

    Flowchart step: 15 — Combine data from paired beams if appropriate (not
    recommended in optically complex water).
    """
    if (not enabled) or dataset.empty:
        return dataset

    combined = dataset.copy()
    combined["source_beam_id"] = combined["beam_id"]
    combined["beam_id"] = (
        combined["beam_id"].map(PAIR_ID_MAP).fillna(combined["beam_id"])
    )

    if "relative_AT_dist" in combined.columns:
        rel_m = pd.to_numeric(combined["relative_AT_dist"], errors="coerce") * 1000.0
        pair_bins = (rel_m / max(horizontal_res, 1)).astype("Int64")
        pair_bins = pair_bins.fillna(-1).astype(int)
        combined["lat_bins"] = pair_bins

    return combined


def run_pipeline(args):
    """
    Top-level pipeline orchestrator. Executes all 19 flowchart steps in sequence.

    Flowchart steps directly handled here:
      1  — Load ATL03 data (load_data / Extract_sea_photons).
      2  — Remove afterpulse/impulse-response photons (apply_optional_ir_ap_filter).
      3  — Bin sizes set via args.horizontal_res / args.vertical_res.
      4  — Build histograms (process_sea_photon_binning).
      5  — Solar background filter (apply_optional_solar_background_filter).
      6–14 — Subsurface filtering chain (process_subsurface_photon_filtering).
      15 — Paired beam combine (optionally_combine_paired_beams_for_kd).
      16–17 — Beer's Law Kd fit (process_kd_calculation).
      18 — Save Kd CSV output (subsurface_photon_df_added_kd.to_csv).
      19 — Check data for reasonableness (filter_photon_dataset_by_hull_area +
           plot_kd_photons).
    """
    atl03_h5_file_path = os.path.join(
        args.workspace_path, args.atl03_path, args.atl03_file
    )
    shoreline_data_path = os.path.join(
        args.workspace_path, args.other_data_path, args.shoreline_data
    )
    gebco_full_path = os.path.join(
        args.workspace_path, args.other_data_path, args.gebco_path
    )
    atl24_file_path = args.atl24_file
    if atl24_file_path and (not os.path.isabs(atl24_file_path)):
        atl24_file_path = os.path.join(args.workspace_path, atl24_file_path)
    output_path = os.path.join(args.workspace_path, args.output_path)
    os.makedirs(output_path, exist_ok=True)

    match = re.search(r"_(\d{14})_", atl03_h5_file_path)
    timestamp = match.group(1) if match else "unknown"

    version_match = re.search(
        r"ATL03_\d{14}_\d{8}_(\d{3})_\d{2}", os.path.basename(atl03_h5_file_path)
    )
    atl03_version = int(version_match.group(1)) if version_match else None
    logger.info(
        "ATL03 version detected: %s",
        f"{atl03_version:03d}" if atl03_version else "unknown",
    )

    if args.enable_ir_ap_filter:
        if atl03_version is None or atl03_version < 7:
            logger.error(
                "IR/AP filter requires ATL03 version 007 or later. "
                "Detected version: %s. "
                "Skipping IR/AP filter for this run. "
                "Switch to a version 007 file (e.g., Wax Delta dataset) to enable this step.",
                f"{atl03_version:03d}" if atl03_version else "unknown",
            )
            args.enable_ir_ap_filter = False

    gebco_pattern = os.path.join(gebco_full_path, "gebco_*.tif")
    gebco_file_path_lists = [p for p in glob.glob(gebco_pattern)]

    is2_mds, is2_attrs, is2_beams = load_data(
        atl03_h5_file_path, False
    )  # wrapper around read_granule()
    target_strong_beams = get_target_beams(is2_beams, is2_attrs, args.target_beams)
    if not target_strong_beams:
        logger.error(
            "No target strong beams found. Check input file and --target_beams."
        )
        sys.exit(1)
    logger.info("Strong beams selected: %s", target_strong_beams)
    plot_target_beam = [target_strong_beams[0]]
    
    # Place to insert sliderule into code
    sea_photon_dataset = Extract_sea_photons(
        is2_mds, target_strong_beams, shoreline_data_path
    )

    if args.enable_ir_ap_filter and not args.no_plot:
        plot_photon_quality_flags(
            output_path, timestamp, sea_photon_dataset, plot_target_beam
        )

    sea_photon_dataset = apply_optional_ir_ap_filter(
        sea_photon_dataset,
        enabled=args.enable_ir_ap_filter,
        quality_max=args.ir_ap_quality_max,
        min_signal_conf=args.ir_ap_min_signal_conf,
    )

    # Step 5 — Solar background filter is ON by default.
    # It self-gates on solar_elevation so has zero effect on nighttime passes.
    # Use --disable_solar_background_filter to turn it off.
    solar_bg_enabled = not args.disable_solar_background_filter
    if not solar_bg_enabled:
        if "solar_elevation" in sea_photon_dataset.columns:
            max_solar_elev = sea_photon_dataset["solar_elevation"].max()
            if max_solar_elev > args.solar_elevation_day_threshold:
                logger.warning(
                    "Solar background filter is DISABLED via --disable_solar_background_filter "
                    "but this granule is a daytime pass "
                    "(max solar elevation = %.1f°, daytime threshold = %.1f°). "
                    "This filter is recommended for daytime passes.",
                    max_solar_elev,
                    args.solar_elevation_day_threshold,
                )

    sea_photon_dataset = apply_optional_solar_background_filter(
        sea_photon_dataset,
        enabled=solar_bg_enabled,
        day_threshold=args.solar_elevation_day_threshold,
        median_window_deg=args.solar_bg_median_window_deg,
        noise_multiplier=args.solar_bg_noise_multiplier,
        min_signal_conf=args.solar_background_min_signal_conf,
    )

    binned_dataset_sea_surface = process_sea_photon_binning(
        sea_photon_dataset,
        horizontal_res=args.horizontal_res,
        vertical_res=args.vertical_res,
    )

    post_refraction_refit_enabled = args.enable_post_refraction_refit
    if post_refraction_refit_enabled and (not args.enable_refraction_correction):
        logger.warning(
            "--enable_post_refraction_refit requested without --enable_refraction_correction. "
            "The post-refraction refit step will be skipped."
        )
        post_refraction_refit_enabled = False

    (
        sea_surface_height,
        sea_surface_label,
        filtered_seafloor_subsurface_photon_dataset,
    ) = process_subsurface_photon_filtering(
        binned_dataset_sea_surface,
        gebco_file_path_lists,
        args.subsurface_thresh,
        args.ignore_subsurface_height_thres,
        use_atl24_filter=args.enable_atl24_filter,
        atl24_file_path=atl24_file_path,
        atl24_max_match_distance_deg=args.atl24_max_match_distance_deg,
        use_gebco_filter=args.enable_gebco_filter,
        apply_histogram_quality_filter=args.enable_histogram_quality_filter,
        histogram_quality_min_ratio=args.histogram_quality_min_ratio,
        histogram_quality_depth_min=args.histogram_quality_depth_min,
        histogram_quality_depth_max=args.histogram_quality_depth_max,
        histogram_quality_ref_depth_min=args.histogram_quality_ref_depth_min,
        histogram_quality_ref_depth_max=args.histogram_quality_ref_depth_max,
        apply_surface_sigma_filter=args.enable_surface_sigma_filter,
        surface_sigma_max=args.surface_sigma_max,
        apply_refraction_correction=args.enable_refraction_correction,
        refraction_water_temp_c=args.refraction_water_temp_c,
        refraction_wavelength_nm=args.refraction_wavelength_nm,
        apply_post_refraction_refit=post_refraction_refit_enabled,
        apply_flattening=args.enable_sea_surface_flattening,
        flattening_window_m=args.sea_surface_flattening_window_m,
        horizontal_res=args.horizontal_res,
        vertical_res=args.vertical_res,
    )

    final_filtered_subsurface_photon_dataset = (
        filtered_seafloor_subsurface_photon_dataset[
            filtered_seafloor_subsurface_photon_dataset["beam_id"].isin(
                target_strong_beams
            )
        ].copy()
    )

    if args.enable_convex_hull_filter:
        final_filtered_subsurface_photon_dataset, convex_hull_areas, convex_hulls = (
            filter_photon_dataset_by_hull_area(
                final_filtered_subsurface_photon_dataset,
                hull_area_threshold=args.convex_hull_area_threshold,
            )
        )
        if plot_target_beam and not args.no_plot:
            plot_convex_hulls(
                final_filtered_subsurface_photon_dataset,
                plot_target_beam,
                convex_hulls,
                convex_hull_areas,
            )

    subsurface_output_path = os.path.join(
        output_path,
        f"{timestamp}_strongBeam_{'_'.join(target_strong_beams)}_subsurface_photons.csv",
    )
    final_filtered_subsurface_photon_dataset.to_csv(subsurface_output_path, index=False)

    kd_input_dataset = optionally_combine_paired_beams_for_kd(
        final_filtered_subsurface_photon_dataset,
        horizontal_res=args.horizontal_res,
        enabled=args.enable_paired_beam_combine,
    )
    wave_mult = args.wave_exclusion_multiplier if args.enable_wave_adaptive_fit else 0.0
    subsurface_photon_df_added_kd = process_kd_calculation(
        kd_input_dataset,
        decay_zone_threshold=args.decay_zone_threshold,
        kd_fit_method=args.kd_fit_method,
        wave_exclusion_multiplier=wave_mult,
        wave_sigma_calm_threshold=args.wave_sigma_calm_threshold,
    )
    kd_output_path = os.path.join(
        output_path, f"{timestamp}_AddedKdDataset_strongBeams_Further.csv"
    )
    subsurface_photon_df_added_kd.to_csv(kd_output_path, index=False)

    if not args.no_plot and "relative_AT_dist" in kd_input_dataset.columns:
        unique_photon_dataset = kd_input_dataset[
            ["relative_AT_dist", "lat_bins", "photon_height"]
        ].drop_duplicates()
        unique_photon_dataset["relative_AT_dist_center"] = (
            unique_photon_dataset.groupby(
                "lat_bins", observed=False
            )["relative_AT_dist"].transform("mean")
        )

        _closest_rows = []
        for _lat_bin, _group in unique_photon_dataset.groupby(
            "lat_bins", observed=False
        ):
            if _group.empty:
                continue
            _center = _group["relative_AT_dist_center"].iloc[0]
            _group = _group.copy()
            _group["dist_to_center"] = abs(_group["relative_AT_dist"] - _center)
            _closest_rows.append(_group.loc[[_group["dist_to_center"].idxmin()]])
        if not _closest_rows:
            logger.warning("No along-track bins survived filtering. Skipping plot.")
        else:
            closest_to_center = pd.concat(_closest_rows).reset_index(drop=True)
            kd_df_merged_distance = closest_to_center.merge(
                subsurface_photon_df_added_kd, on="lat_bins", how="left"
            ).drop(
                columns=["relative_AT_dist_center", "dist_to_center"], errors="ignore"
            )

            plot_kd_photons(
                output_path,
                timestamp,
                plot_target_beam,
                kd_input_dataset,
                kd_df_merged_distance,
            )

    logger.info("SUCCESS! Kd output: %s", kd_output_path)


if __name__ == "__main__":
    cli_args = get_args()
    try:
        run_pipeline(cli_args)
    except Exception as e:
        logger.error("An error occurred: %s", e)
        raise
