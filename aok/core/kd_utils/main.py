import glob
import logging
import os
import re
import sys

import pandas as pd

from config import get_args
from kd_utils.Kd_analysis import process_kd_calculation
from kd_utils.bathy_processing import process_subsurface_photon_filtering
from kd_utils.data_processing import (
    Extract_sea_photons,
    apply_optional_ir_ap_filter,
    apply_optional_solar_background_filter,
    filter_photon_dataset_by_hull_area,
    load_data,
)
from kd_utils.sea_photons_analysis import process_sea_photon_binning
from kd_utils.visualization import plot_convex_hulls, plot_kd_photons


logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


PAIR_ID_MAP = {
    'gt1l': 'gt1_pair',
    'gt1r': 'gt1_pair',
    'gt2l': 'gt2_pair',
    'gt2r': 'gt2_pair',
    'gt3l': 'gt3_pair',
    'gt3r': 'gt3_pair',
}


def get_target_beams(all_beams, beam_attrs, target_beams_arg):
    strong_beams = [
        gtx for gtx in all_beams
        if beam_attrs[gtx]['atlas_beam_type'].decode('utf-8') == 'strong'
    ]
    if not target_beams_arg:
        return strong_beams

    requested = [b.strip() for b in target_beams_arg.split(',') if b.strip()]
    return [b for b in requested if b in strong_beams]


def optionally_combine_paired_beams_for_kd(dataset, horizontal_res, enabled=False):
    """
    Optionally combine left/right beams into pair groups before Kd fitting.
    Uses shared along-track bins from relative_AT_dist when available.
    """
    if (not enabled) or dataset.empty:
        return dataset

    combined = dataset.copy()
    combined['source_beam_id'] = combined['beam_id']
    combined['beam_id'] = combined['beam_id'].map(PAIR_ID_MAP).fillna(combined['beam_id'])

    if 'relative_AT_dist' in combined.columns:
        rel_m = pd.to_numeric(combined['relative_AT_dist'], errors='coerce') * 1000.0
        pair_bins = (rel_m / max(horizontal_res, 1)).astype('Int64')
        pair_bins = pair_bins.fillna(-1).astype(int)
        combined['lat_bins'] = pair_bins

    return combined


def run_pipeline(args):
    atl03_h5_file_path = os.path.join(args.workspace_path, args.atl03_path, args.atl03_file)
    shoreline_data_path = os.path.join(args.workspace_path, args.other_data_path, args.shoreline_data)
    gebco_full_path = os.path.join(args.workspace_path, args.other_data_path, args.gebco_path)
    atl24_file_path = args.atl24_file
    if atl24_file_path and (not os.path.isabs(atl24_file_path)):
        atl24_file_path = os.path.join(args.workspace_path, atl24_file_path)
    output_path = os.path.join(args.workspace_path, args.output_path)
    os.makedirs(output_path, exist_ok=True)

    match = re.search(r"_(\d{14})_", atl03_h5_file_path)
    timestamp = match.group(1) if match else "unknown"

    gebco_pattern = os.path.join(gebco_full_path, "gebco_*.tif")
    gebco_file_path_lists = [p for p in glob.glob(gebco_pattern)]

    is2_mds, is2_attrs, is2_beams = load_data(atl03_h5_file_path, False)
    target_strong_beams = get_target_beams(is2_beams, is2_attrs, args.target_beams)
    if not target_strong_beams:
        logger.error("No target strong beams found. Check input file and --target_beams.")
        sys.exit(1)
    logger.info("Strong beams selected: %s", target_strong_beams)
    plot_target_beam = [target_strong_beams[0]]

    sea_photon_dataset = Extract_sea_photons(is2_mds, target_strong_beams, shoreline_data_path)
    sea_photon_dataset = apply_optional_ir_ap_filter(
        sea_photon_dataset,
        enabled=args.enable_ir_ap_filter,
        quality_max=args.ir_ap_quality_max,
        min_signal_conf=args.ir_ap_min_signal_conf,
    )
    sea_photon_dataset = apply_optional_solar_background_filter(
        sea_photon_dataset,
        enabled=args.enable_solar_background_filter,
        day_threshold=args.solar_elevation_day_threshold,
        background_quantile=args.solar_background_quantile,
        min_signal_conf=args.solar_background_min_signal_conf,
    )

    binned_dataset_sea_surface = process_sea_photon_binning(
        sea_photon_dataset, horizontal_res=args.horizontal_res, vertical_res=args.vertical_res
    )

    post_refraction_refit_enabled = args.enable_post_refraction_refit
    if post_refraction_refit_enabled and (not args.enable_refraction_correction):
        logger.warning(
            "--enable_post_refraction_refit requested without --enable_refraction_correction. "
            "The post-refraction refit step will be skipped."
        )
        post_refraction_refit_enabled = False

    sea_surface_height, sea_surface_label, filtered_seafloor_subsurface_photon_dataset = \
        process_subsurface_photon_filtering(
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

    final_filtered_subsurface_photon_dataset = filtered_seafloor_subsurface_photon_dataset[
        filtered_seafloor_subsurface_photon_dataset['beam_id'].isin(target_strong_beams)
    ].copy()

    if args.enable_convex_hull_filter:
        final_filtered_subsurface_photon_dataset, convex_hull_areas, convex_hulls = \
            filter_photon_dataset_by_hull_area(
                final_filtered_subsurface_photon_dataset,
                hull_area_threshold=args.convex_hull_area_threshold
            )
        if plot_target_beam:
            plot_convex_hulls(
                final_filtered_subsurface_photon_dataset,
                plot_target_beam,
                convex_hulls,
                convex_hull_areas
            )

    subsurface_output_path = os.path.join(
        output_path,
        f"{timestamp}_strongBeam_{'_'.join(target_strong_beams)}_subsurface_photons.csv",
    )
    final_filtered_subsurface_photon_dataset.to_csv(subsurface_output_path, index=False)

    kd_input_dataset = optionally_combine_paired_beams_for_kd(
        final_filtered_subsurface_photon_dataset,
        horizontal_res=args.horizontal_res,
        enabled=args.enable_paired_beam_combine
    )
    subsurface_photon_df_added_kd = process_kd_calculation(kd_input_dataset)
    kd_output_path = os.path.join(output_path, f"{timestamp}_AddedKdDataset_strongBeams_Further.csv")
    subsurface_photon_df_added_kd.to_csv(kd_output_path, index=False)

    if 'relative_AT_dist' in kd_input_dataset.columns:
        unique_photon_dataset = kd_input_dataset[
            ['relative_AT_dist', 'lat_bins', 'photon_height']
        ].drop_duplicates()
        unique_photon_dataset['relative_AT_dist_center'] = unique_photon_dataset.groupby(
            'lat_bins', observed=False
        )['relative_AT_dist'].transform('mean')

        def find_closest(group):
            center = group['relative_AT_dist_center'].iloc[0]
            group = group.copy()
            group['dist_to_center'] = abs(group['relative_AT_dist'] - center)
            return group.loc[[group['dist_to_center'].idxmin()]]

        closest_to_center = unique_photon_dataset.groupby('lat_bins', observed=False).apply(
            find_closest, include_groups=True
        )
        closest_to_center.index = closest_to_center.index.droplevel(0)
        kd_df_merged_distance = closest_to_center.merge(
            subsurface_photon_df_added_kd,
            on='lat_bins',
            how='left'
        ).drop(columns=['relative_AT_dist_center', 'dist_to_center'], errors='ignore')

        plot_kd_photons(
            output_path,
            timestamp,
            plot_target_beam,
            kd_input_dataset,
            kd_df_merged_distance,
        )

    logger.info("SUCCESS! Kd output: %s", kd_output_path)


if __name__ == '__main__':
    cli_args = get_args()
    try:
        run_pipeline(cli_args)
    except Exception as e:
        logger.error("An error occurred: %s", e)
        raise
