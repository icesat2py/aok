# # config.py

# path = 'C:/Workstation/ICESat2_HLS/Kd_ComparisionPaper/Dataset/ATL03_ICESat2/'

# #US, Orgon
# # ATL03_h5_file = "processed_ATL03_20181206092124_10500106_005_01.h5"#
# #South America
# # ATL03_h5_file = "processed_ATL03_20220530041141_10391513_005_02.h5"#


# #Alaska Cook Inlet
# # ATL03_h5_file = "processed_ATL03_20210801125753_05941205_005_01.h5"#
# ATL03_20200805175053_06320803_006_01_subsetted
# ATL03_20210828231447_10131203_006_01_subsetted

# # Hawaii line without afterpulses
# # ATL03_h5_file = "processed_ATL03_20220122044818_04721407_006_01.h5"#


# # ChesapeakeBay
# ATL03_h5_file = "processed_ATL03_20230825074121_10102002_006_02.h5"#


# # India
# # ATL03_h5_file = "processed_ATL03_20200331204156_00810707_006_01.h5"#


# #China Bohai
# # ATL03_h5_file = "processed_ATL03_20191128115256_09560502_006_01.h5"#
# # ATL03_h5_file = "processed_ATL03_20190530203316_09560302_006_02.h5"#

# ATL03_h5_file = "processed_ATL03_20190829161305_09560402_006_02.h5"#


# ATL03_h5_file_path = path + ATL03_h5_file

# Current_Path = 'C:/Workstation/ICESat2_HLS/Kd_ComparisionPaper/Dataset/'

# shoreline_data_path = Current_Path + 'Shorelines/GeoPkgGlobalShoreline.gpkg'

# #load the Global bathy dataset
# GEBCO_paths = [
#     Current_Path + "Bathy/gebco_2024_geotiff/gebco_2024_n0.0_s-90.0_w0.0_e90.0.tif",
#     Current_Path + "Bathy/gebco_2024_geotiff/gebco_2024_n0.0_s-90.0_w-90.0_e0.0.tif",
#     Current_Path + "Bathy/gebco_2024_geotiff/gebco_2024_n0.0_s-90.0_w90.0_e180.0.tif",
#     Current_Path + "Bathy/gebco_2024_geotiff/gebco_2024_n0.0_s-90.0_w-180.0_e-90.0.tif",
#     Current_Path + "Bathy/gebco_2024_geotiff/gebco_2024_n90.0_s0.0_w0.0_e90.0.tif",
#     Current_Path + "Bathy/gebco_2024_geotiff/gebco_2024_n90.0_s0.0_w-90.0_e0.0.tif",
#     Current_Path + "Bathy/gebco_2024_geotiff/gebco_2024_n90.0_s0.0_w90.0_e180.0.tif",
#     Current_Path + "Bathy/gebco_2024_geotiff/gebco_2024_n90.0_s0.0_w-180.0_e-90.0.tif",
# ]

# horizontal_res = 500

# vertical_res = 0.25

# # Use calculated sea height to determine photons at 0.5m below peak
# subsurface_thresh = 0.5

# # subsurface distance below the sea surface beginning to account
# Kd_max_depth = -1

# OutputPath='C:/Workstation/ICESat2_HLS/Kd_ComparisionPaper/Results/'

import argparse


def get_args():
    parser = argparse.ArgumentParser(
        description="Configure ICESat-2 HLS analysis script."
    )

    # General paths
    parser.add_argument(
        "--workspace_path",
        type=str,
        default=".",
        help="Root path for all data processing.",
    )

    # parser.add_argument("--atl03_path", type=str, default='Dataset/ATL03_ICESat2/New/',
    #                     help="Base path for ICESat-2 ATL03 data.")

    # # Bohai Sea (v006)
    # parser.add_argument("--atl03_path", type=str, default='Dataset/ATL03_ICESat2/',
    #                     help="Base path for ICESat-2 ATL03 data.")

    # Wax Delta (v007) — required for IR/AP filter sensitivity test
    parser.add_argument(
        "--atl03_path",
        type=str,
        default="Dataset/ATL03_ICESat2/Wax_Delta/",
        help="Base path for ICESat-2 ATL03 data.",
    )

    # #ChesapeakeBay
    # parser.add_argument("--atl03_file", type=str, default="processed_ATL03_20230825074121_10102002_006_02.h5",
    #                     help="Name of the ATL03 H5 file to process.")

    # parser.add_argument("--atl03_file", type=str, default="processed_ATL03_20221001113813_01641706_006_01.h5",
    #                     help="Name of the ATL03 H5 file to process.")

    # # India: processed_ATL03_20200331204156_00810707_006_01.h5
    # parser.add_argument("--atl03_file", type=str, default="processed_ATL03_20200331204156_00810707_006_01.h5",
    #                     help="Name of the ATL03 H5 file to process.")

    # #ATL03_20210628230109_00811207_006_01_subsetted

    # parser.add_argument("--atl03_file", type=str, default="processed_ATL03_20210628230109_00811207_006_01.h5",
    #                     help="Name of the ATL03 H5 file to process.")

    # # WaxDelta
    # parser.add_argument("--atl03_file", type=str, default="ATL03_20231103172707_06982106_006_01_subsetted.h5",
    #                     help="Name of the ATL03 H5 file to process.")

    # # Bohai (v006) — baseline sensitivity test site
    # parser.add_argument("--atl03_file", type=str, default="ATL03_20190829161305_09560402_006_02_subsetted.h5",
    #                     help="Name of the ATL03 H5 file to process.")

    # Wax Delta (v007) — required for IR/AP filter; use with atl03_path = Dataset/ATL03_ICESat2/Wax_Delta/
    parser.add_argument(
        "--atl03_file",
        type=str,
        default="ATL03_20231103172707_06982106_007_01_subsetted.h5",
        help="Name of the ATL03 H5 file to process.",
    )

    # # Cook Inlet
    # parser.add_argument("--atl03_file", type=str, default="ATL03_20220507112145_06931503_006_01_subsetted.h5",
    #                     help="Name of the ATL03 H5 file to process.")

    # #Core Sound
    # parser.add_argument("--atl03_file", type=str, default="105430185_ATL03_20220423191113_04841506_006_02_subsetted.h5",
    #                     help="Name of the ATL03 H5 file to process.")

    # # Pamlico Sound
    # parser.add_argument("--atl03_file", type=str, default="ATL03_20240415083629_04232306_006_01_subsetted.h5",
    #                     help="Name of the ATL03 H5 file to process.")

    #
    # #Cook Inlet: processed_ATL03_20210801125753_05941205_005_01
    # parser.add_argument("--atl03_file", type=str, default="processed_ATL03_20210801125753_05941205_005_01.h5",
    #                     help="Name of the ATL03 H5 file to process.")

    parser.add_argument(
        "--other_data_path",
        type=str,
        default="Dataset/",
        help="Path to the current working directory.",
    )

    parser.add_argument(
        "--output_path",
        type=str,
        default="Results/",
        help="Directory for saving results.",
    )

    # Shoreline data
    parser.add_argument(
        "--shoreline_data",
        type=str,
        # default='Shorelines/GeoPkgGlobalShoreline.gpkg',
        default="Shorelines/ne_10m_land/ne_10m_land.shp",
        help="Path to the global shoreline dataset.",
    )

    # Bathymetry datasets
    parser.add_argument(
        "--gebco_path",
        nargs="+",
        type=str,
        default="Bathy/gebco_2024_geotiff/",
        help="Path to GEBCO bathymetry datasets.",
    )

    # Resolution settings
    parser.add_argument(
        "--horizontal_res",
        type=int,
        default=500,
        help="Horizontal resolution for the analysis (in meters).",
    )

    parser.add_argument(
        "--vertical_res",
        type=float,
        default=0.25,
        help="Vertical resolution for the analysis.",
    )

    # Analysis parameters
    parser.add_argument(
        "--subsurface_thresh",
        type=float,
        default=1.0,
        help="Threshold for photons below the sea surface.",
    )

    parser.add_argument(
        "--ignore_subsurface_height_thres",
        type=float,
        default=-6,
        help="Maximum depth thres for Kd calculations (in meters).",
    )  # 5m

    # Empty string '' auto-selects the first strong beam. Pass comma-separated IDs to override.
    # Valid IDs: gt1l, gt1r, gt2l, gt2r, gt3l, gt3r — only strong beams for the granule are kept.
    # To process all strong beams, use --target_beams "gt1r,gt2r,gt3r".
    parser.add_argument(
        "--target_beams",
        type=str,
        default="",
        help="Comma-separated beam IDs to process. Empty means auto-select first strong beam.",
    )

    parser.add_argument(
        "--disable_solar_background_filter",
        action="store_true",
        help="Disable solar background filtering (enabled by default; "
        "self-gates on solar elevation so has no effect on nighttime passes).",
    )
    parser.add_argument(
        "--solar_elevation_day_threshold",
        type=float,
        default=6.0,
        help="Solar elevation threshold (deg) to define daytime for optional filtering.",
    )
    parser.add_argument(
        "--solar_bg_median_window_deg",
        type=float,
        default=10.0,
        help="Rolling median window width (degrees of solar elevation) for "
        "the solar-elevation-aware background filter.",
    )
    parser.add_argument(
        "--solar_bg_noise_multiplier",
        type=float,
        default=1.5,
        help="Ratio of actual/expected background rate above which a photon "
        "is flagged as noisy by the solar background filter.",
    )
    parser.add_argument(
        "--solar_background_min_signal_conf",
        type=int,
        default=2,
        help="Minimum photon signal confidence kept in high daytime background.",
    )

    parser.add_argument(
        "--enable_ir_ap_filter",
        action="store_true",
        help="Optional: remove photons using IR/afterpulse proxy flags.",
    )
    parser.add_argument(
        "--ir_ap_quality_max",
        type=int,
        default=0,
        help="Maximum allowed quality_ph value when IR/AP filter is enabled.",
    )
    parser.add_argument(
        "--ir_ap_min_signal_conf",
        type=int,
        default=0,
        help="Minimum allowed photon_conf value when IR/AP filter is enabled.",
    )

    parser.add_argument(
        "--enable_gebco_filter",
        action="store_true",
        help="Optional: remove photons below GEBCO seafloor and shallow bins.",
    )
    parser.add_argument(
        "--enable_sea_surface_flattening",
        action="store_true",
        help="Optional: flatten small-bin sea-surface variation using larger along-track windows.",
    )
    parser.add_argument(
        "--sea_surface_flattening_window_m",
        type=int,
        default=5000,
        help="Window size in meters for sea-surface flattening mean level. "
        "Must be larger than horizontal_res to have any effect.",
    )

    parser.add_argument(
        "--enable_convex_hull_filter",
        action="store_true",
        help="Optional: apply convex hull area filtering before Kd fitting.",
    )
    parser.add_argument(
        "--convex_hull_area_threshold",
        type=float,
        default=100,
        help="Minimum convex hull area to keep a horizontal bin when enabled.",
    )

    parser.add_argument(
        "--enable_histogram_quality_filter",
        action="store_true",
        help="Optional: discard along-track bins with weak 6-7 m signal.",
    )
    parser.add_argument(
        "--histogram_quality_min_ratio",
        type=float,
        default=0.05,
        help="Minimum ratio of photons in depth band to keep a bin.",
    )
    parser.add_argument(
        "--histogram_quality_depth_min",
        type=float,
        default=6.0,
        help="Minimum depth (m below surface) of quality-check band.",
    )
    parser.add_argument(
        "--histogram_quality_depth_max",
        type=float,
        default=7.0,
        help="Maximum depth (m below surface) of quality-check band.",
    )
    parser.add_argument(
        "--histogram_quality_ref_depth_min",
        type=float,
        default=0.0,
        help="Min depth (m) of near-surface reference band for decay ratio.",
    )
    parser.add_argument(
        "--histogram_quality_ref_depth_max",
        type=float,
        default=1.0,
        help="Max depth (m) of near-surface reference band for decay ratio.",
    )

    parser.add_argument(
        "--enable_surface_sigma_filter",
        action="store_true",
        help="Optional: discard bins where Gaussian surface sigma is too large.",
    )
    parser.add_argument(
        "--surface_sigma_max",
        type=float,
        default=0.5,
        help="Maximum allowed Gaussian sigma (m) for sea-surface peak.",
    )

    parser.add_argument(
        "--enable_refraction_correction",
        action="store_true",
        help="Optional: apply refraction correction to subsurface photons.",
    )
    parser.add_argument(
        "--refraction_water_temp_c",
        type=float,
        default=20.0,
        help="Water temperature (deg C) used for refraction correction.",
    )
    parser.add_argument(
        "--refraction_wavelength_nm",
        type=float,
        default=532.0,
        help="Laser wavelength (nm) used for refraction correction.",
    )

    parser.add_argument(
        "--enable_post_refraction_refit",
        action="store_true",
        help="Optional: rebuild histograms and re-fit surface after refraction correction.",
    )

    parser.add_argument(
        "--enable_atl24_filter",
        action="store_true",
        help="Optional: use ATL24 bathymetry matching before GEBCO fallback.",
    )
    parser.add_argument(
        "--atl24_file",
        type=str,
        default="",
        help="Path to ATL24 point dataset (CSV/Parquet/GPKG/SHP) for bathymetry matching.",
    )
    parser.add_argument(
        "--atl24_max_match_distance_deg",
        type=float,
        default=0.01,
        help="Maximum lon/lat degree distance for ATL24 nearest-point matching.",
    )

    parser.add_argument(
        "--decay_zone_threshold",
        type=float,
        default=0.0,
        help="Fraction of peak photon count below which depth bins are excluded "
        "in Step 16 decay zone detection. 0.0 = original behaviour (only "
        "zero-count bins removed). E.g. 0.01 removes bins with < 1%% of peak.",
    )

    parser.add_argument(
        "--kd_fit_method",
        type=str,
        default="log_linear",
        choices=["log_linear", "bg_subtract", "breakpoint", "nonlinear", "hybrid"],
        help="Beer's Law fitting strategy for Kd calculation. "
        "log_linear = original log-space linear regression; "
        "bg_subtract = subtract noise floor then log-linear; "
        "breakpoint = segmented regression with breakpoint detection; "
        "nonlinear = fit C(z) = A*exp(-Kd*z) + N directly.",
    )

    parser.add_argument(
        "--enable_wave_adaptive_fit",
        action="store_true",
        help="Optional: trim shallow depth bins by wave amplitude before Beer's Law fit. "
        "Uses per-bin surface sigma to skip the top k*sigma metres in wavy bins.",
    )
    parser.add_argument(
        "--wave_exclusion_multiplier",
        type=float,
        default=4.0,
        help="Number of surface sigmas to skip from the actual water surface when "
        "wave-adaptive fit is enabled. The adaptive surface detection already "
        "removes 3*sigma; this adds (k-3)*sigma additional margin for bubble "
        "injection zone. Default 4.0 adds 1*sigma beyond the 3-sigma cutoff.",
    )
    parser.add_argument(
        "--wave_sigma_calm_threshold",
        type=float,
        default=0.1,
        help="Surface sigma (m) below which a bin is considered calm and no "
        "wave trimming is applied. Default 0.1 m.",
    )

    parser.add_argument(
        "--enable_paired_beam_combine",
        action="store_true",
        help="Optional: combine paired beams (gt1, gt2, gt3) before Kd fitting.",
    )

    parser.add_argument(
        "--no_plot",
        action="store_true",
        help="Suppress all plot generation (useful for batch runs).",
    )

    # switch on consider the coastal water or inland water
    # if Inland water, we should use one mask and for coastal water, it should be another mask

    # consider bathymetry or not manual setting

    # night vs daytime

    # solar elevation determine remove or not for solar background

    # 1-2 hours

    return parser.parse_args()


if __name__ == "__main__":
    args = get_args()
    # Access parameters like this:
    atl03_file_path = args.workspace_path + args.atl03_file

    print("Processing file:", atl03_file_path)
    print("Output path:", args.output_path)
