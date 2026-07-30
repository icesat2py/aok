# contains classes for data input objects and data output objects after acquisition from the cloud.
from dataclasses import dataclass, field
import logging
from pathlib import Path
from typing import Any

import geopandas as gpd
import pandas as pd
from sliderule import sliderule

# from aok.core.kd_utils.data_processing import

logger = logging.getLogger(__name__)


@dataclass
class DataRequest:
    """
    Backend request object describing what data should be acquired.

    DataRequest stores the user's requested spatial, temporal, product, and
    run options in a shared format. It provides methods for building SlideRule
    request parameters, fetching ATL03 and/or ATL24 data, optionally merging those
    datasets, and storing the final photon table on the request object itself.

    The final acquired dataset is stored in `photons`. If both ATL03 and ATL24 are
    requested, ATL03 is treated as the left-hand photon table and ATL24 attributes
    are merged onto it using `time_ns`. If only one product is requested, that
    product's photon table is stored directly in `photons`.

    Request attributes
    ------------------
    spatial
        Optional spatial region of interest. This may be a bounding box, polygon
        coordinate list, or another geometry-like object accepted by the downstream
        acquisition method.
    date_range
        Optional tuple of start and end date strings in YYYY-MM-DD format.
    time_range
        Optional tuple of start and end time strings in HH:MM:SS format. If not
        provided, the full day is used for each date in `date_range`.
    beams
        Optional set of beams, "strong", "weak", or "all". Defaults to "strong".
        If set to "strong" spot column will be filtered for [1,3,5] (strong beams).
        If set to "weak" spot column will be filtered for [2,4,6] (weak beams).
        If set to "all" no filtering will take place.

    Product flags
    -------------
    need_atl03
        Whether ATL03 photon data should be requested.
    need_atl24
        Whether ATL24 bathymetry-classified photon data should be requested.
    need_gebco
        Whether GEBCO bathymetry samples should be requested with ATL03.
    need_shoreline
        Whether shoreline data should be used for spatial filtering. This behavior
        is not fully implemented yet.
    need_jpl_temperature
        Whether JPL sea surface temperature data should be requested. This behavior
        is not implemented yet.

    Product options
    ---------------
    version_atl03
        Optional ATL03 product version.
    version_atl24
        Optional ATL24 product version.
    variables_atl03
        Optional additional ATL03 parameters or fields.
    variables_atl24
        Optional additional ATL24 fields.
    shoreline_data
        Optional path to shoreline data used for future spatial filtering.
    land_ocean_mask
        Optional path to land-ocean mask used for creating a shoreline mask
    options
        Additional keyword-style options passed through to the relevant acquisition
        parameter builder.

    Result attributes
    -----------------
    photons
        Final acquired photon table. This is usually a pandas DataFrame or
        GeoPandas GeoDataFrame. If both ATL03 and ATL24 are requested, this stores
        the merged photon table.
    metadata
        Dictionary containing acquisition metadata, such as requested products,
        source information, row counts, and column names.
    sources
        List of acquisition sources used to create the final photon table.
    products
        List of products included in the final photon table.
    """

    spatial: Any | None = None
    date_range: tuple[str, str] | None = None
    time_range: tuple[str, str] | None = None
    beams: str | None = None

    need_atl03: bool = True
    need_atl24: bool = True
    need_gebco: bool = True
    need_shoreline: bool = True
    need_jpl_temperature: bool = False

    version_atl03: str | None = None
    version_atl24: str | None = None

    variables_atl03: list[str] | None = None
    variables_atl24: list[str] | None = None

    shoreline_data: Path | None = None
    land_ocean_mask: Path | None = None

    options: dict[str, Any] = field(default_factory=dict)

    # outputs
    photons: gpd.GeoDataFrame | pd.DataFrame | None = None
    metadata: dict[str, Any] = field(default_factory=dict)
    sources: list[str] = field(default_factory=list)
    products: list[str] = field(default_factory=list)

    def _sliderule_time_range(self) -> tuple[str, str]:
        """Build SlideRule time range parameters
            Converts from strings to datetime objects

        Parameters
        ----------
        DataRequest object
            If self.date_range is None an error is thrown.
            If self.time_range is None, the start and end times are set to 00:00:00, and 23:59:59 by default.
            This can be varied by the calling method depending on the data request.
        """
        if self.date_range is None:
            msg = "date_range is required."
            raise ValueError(msg)

        start_date, end_date = self.date_range

        start_time = "00:00:00"
        end_time = "23:59:59"

        if self.time_range is not None:
            start_time, end_time = self.time_range

        t0 = f"{start_date}T{start_time}Z"
        t1 = f"{end_date}T{end_time}Z"
        return t0, t1

    def _cut_spatial_extent(self) -> None:
        """
        follows logic of spatial extent, and provided shapefiles to filter the
        request for only ocean photons. Goal is to replace isolate_sea_land_photons
        which currently filters the data once downloaded.

        This method filters the spatial extent before any request.
        If this filtering fails,try again once data is downloaded using
        isolate_sea_land_photons

        Not implemented yet. Draft implementation is below.

        """
        msg = "_cut_spatial_extent exists but is not implemented yet."
        raise NotImplementedError(msg)
        """
        if self.need_shoreline:
            try:
                shorelines = gpd.read_file(self.shoreline_data, mask = self.spatial)

                shorelines = shorelines.clip(self.spatial)
                shore_cut = shorelines.union_all()
                self.sea_extent = aoi_extent.difference(shore_cut)
                self.sea_extent = self.sea_extent.union_all()

                return None

            except Exception as e:
                print(e)

        print("Error loading shoreline data, original spatial extent will be used, and photons filtered after download")
        """

    def build_atl03_params(self) -> dict[str, Any]:
        """
        Builds the parameters for a sliderule.run request from
        DataRequest object.
        """
        t0, t1 = self._sliderule_time_range()

        """
        # Pause on implementing shoreline data until later;
        if self.need_shoreline:
            # create a region mask with sliderule.toregion
            sliderule.toregion(self.spatial, raster)

            in params:
            "region_mask": region['raster']# <- to store shoreline raster
        """

        params: dict[str, Any] = {
            "poly": self.spatial,
            "t0": t0,  # from time range convert function
            "t1": t1,  # from time range convert function
            "srt": [0, 1, 2, 3, 4],  # -1 for atl24 data; surface type for atl03
            "cnf": [0, 1, 2, 3, 4],
            # "spots": [1, 3, 5], # note, functionality broken, only 1 spot or all can be pulled
            "quality_ph": [0],  # replaces ir/ap filter
        }

        ## Now adding required auxiliary fields
        """
        Note dist_ph_along is possibly already included by
        default in the x_atc which is dist_ph_along +
        segment_distance; ask Chao if his calculations are
        different; note this is used as relative_AT_dist;
        seems that Chao uses distance from first photon.
        """
        atl03_heights = {
            "atl03_ph_fields": [
                "h_ph",  # Photon WGS84 Height; possibly same as "height"
                "delta_time",  # "photon_delta_time" in data_processing.py
                "dist_ph_along",
            ]
        }
        params.update(atl03_heights)

        atl03_geolocation = {
            "atl03_geo_fields": [
                "segment_id",
                "ph_index_beg",
                "segment_ph_cnt",
                "segment_dist_x",  # "Equator_Segment_Distance"
                "segment_length",
                # "delta_time", # "delta_time" in data_processing
                "reference_photon_lat",
                "reference_photon_lon",
                "ref_elev",
                "ref_azimuth",
            ]
        }
        params.update(atl03_geolocation)

        atl03_bckgrd_atlas = {
            "atl03_bckgrd_fields": [  # used to calculate photon_background rate.
                "bckgrd_rate",  # want bckgrd rate flag to false (no atmosphere flag)
                # "delta_time", # called "bckgrd_time"; cannot call multiple delta times
            ],
        }
        params.update(atl03_bckgrd_atlas)

        atl03_geophys_corr = {
            "atl03_cor_fields": ["geoid"],
        }  # height above WGS-84 ref ellipsoid

        params.update(atl03_geophys_corr)

        # per email with atl09 folks, backg_c is the background rate
        params["atl09_fields"] = [
            "high_rate/backg_c",
        ]

        # auxiliary param notes:
        """
        #lat_ph, # already included by default
        #lon_ph, # already included by default
        #signal_conf_ph, # already included as atl03_cnf
        #dist_ph_across, # included by default as y_atc
        #quality_ph, # included by default.
        # solar_elevation, # included by default
        """

        # Add optional call to gebco;
        # returns three columns gebco.fileid, gebco.time_ns
        # and gebco.value
        if self.need_gebco:
            params["samples"] = {"gebco": {"asset": "gebco-s3"}}

        if self.beams is not None:
            params["beams"] = self.beams

        # append extra atl03 parameters
        if self.variables_atl03 is not None:
            params.update(self.variables_atl03)

        return params

    def build_atl24_params(self) -> dict[str, Any]:
        t0, t1 = self._sliderule_time_range()

        params: dict[str, Any] = {
            "poly": self.spatial,
            "t0": t0,
            "t1": t1,
            "atl24": {"class_ph": ["bathymetry", "sea_surface"], "compact": False},
        }

        if self.beams is not None:
            params["beams"] = self.beams

        if self.variables_atl24 is not None:
            params["atl24_fields"] = self.variables_atl24

        params.update(self.options)
        return params

    def get_atl03_data(self) -> pd.DataFrame:
        params = self.build_atl03_params()
        return sliderule.run("atl03x", params)

    def get_atl24_data(self) -> pd.DataFrame:
        """
        Request ATL24 data from SlideRule.

        Returns
        -------
        pd.DataFrame | None
            ATL24 dataframe if available. None if SlideRule cannot return ATL24
            data for the request.
        """
        params = self.build_atl24_params()

        try:
            atl24 = sliderule.run("atl24x", params)
        except Exception as exc:
            logger.warning(
                "ATL24 data could not be retrieved from SlideRule for this request. "
                "Continuing without ATL24 merge. Original error: %s",
                exc,
            )
            return None

        if atl24 is None or atl24.empty:
            logger.warning(
                "SlideRule returned no ATL24 data for this request. "
                "Continuing without ATL24, gebco will be used instead."
            )
            return None

        return atl24

    def _merge_photons(
        self,
        atl03_photons: pd.DataFrame,
        atl24_photons: pd.DataFrame,
    ) -> pd.DataFrame:
        """
        Merge ATL24 photon information onto ATL03 photons using time_ns.

        ATL03 is treated as the left-most dataframe. The merged result preserves
        ATL03 row order and preserves time_ns as the index when ATL03 uses time_ns
        as its index.
        """
        atl03_has_time_ns_index = atl03_photons.index.name == "time_ns"
        atl24_has_time_ns_index = atl24_photons.index.name == "time_ns"

        atl03_has_time_ns_column = "time_ns" in atl03_photons.columns
        atl24_has_time_ns_column = "time_ns" in atl24_photons.columns

        if not atl03_has_time_ns_index and not atl03_has_time_ns_column:
            msg = (
                "Cannot merge photons: ATL03 photons are missing 'time_ns' "
                "as both a column and an index."
            )
            raise ValueError(msg)

        if not atl24_has_time_ns_index and not atl24_has_time_ns_column:
            msg = (
                "Cannot merge photons: ATL24 photons are missing 'time_ns' "
                "as both a column and an index."
            )
            raise ValueError(msg)

        if atl03_has_time_ns_index and atl24_has_time_ns_index:
            merged = atl03_photons.merge(
                atl24_photons,
                left_index=True,
                right_index=True,
                how="left",
                suffixes=("", "_atl24"),
            )

        elif atl03_has_time_ns_index and atl24_has_time_ns_column:
            merged = atl03_photons.merge(
                atl24_photons,
                left_index=True,
                right_on="time_ns",
                how="left",
                suffixes=("", "_atl24"),
            ).set_index("time_ns")

        elif atl03_has_time_ns_column and atl24_has_time_ns_index:
            merged = atl03_photons.merge(
                atl24_photons,
                left_on="time_ns",
                right_index=True,
                how="left",
                suffixes=("", "_atl24"),
            )

        else:
            merged = atl03_photons.merge(
                atl24_photons,
                on="time_ns",
                how="left",
                suffixes=("", "_atl24"),
            )

        if isinstance(atl03_photons, gpd.GeoDataFrame):
            merged = gpd.GeoDataFrame(
                merged,
                geometry=atl03_photons.geometry.name,
                crs=atl03_photons.crs,
            )

        return merged

    def rename_atl03_columns(self, atl03_photons: pd.DataFrame) -> pd.DataFrame:
        """
        Rename ATL03 columns from SlideRule names to the names expected by
        the existing Kd-processing code.

        Rules
        -----
        1. If the SlideRule name and AOK pipeline name are identical, do nothing.
           Example: "latitude" -> "latitude"

        2. If the SlideRule name and AOK pipeline name are different, rename the
           SlideRule column to the AOK pipeline name.
           Example: "height" -> "photon_height"

        3. If the AOK pipeline name already exists in the dataframe, first preserve
           the existing column by renaming it with a "_sr" suffix, then rename the
           SlideRule column to the AOK pipeline name.
           Example:
               existing "background_rate" -> "background_rate_sr"
               "bckgrd_rate" -> "background_rate"

        Columns not listed in ATL03_COLUMN_RENAMES are preserved unchanged.
        """
        ATL03_COLUMN_RENAMES = {
            # SlideRule name: AOK pipeline expected name
            "latitude": "latitude",
            "longitude": "longitude",
            "spot": "beam_id",
            "height": "photon_height",
            "quality_ph": "quality_ph",
            "atl03_cnf": "photon_conf",
            "ref_elevation": "ref_elevation",
            "ref_azimuth": "ref_azimuth",
            # Solar background filter inputs
            "solar_elevation": "solar_elevation",
            "bckgrd_rate": "background_rate",
            # Be cautious: this may not be equivalent to the older relative_AT_dist
            # calculation, which adjusted x_atc by segment distance and converted to km.
            "x_atc": "relative_AT_dist",
        }

        photons = atl03_photons.copy()

        for sliderule_name, pipeline_name in ATL03_COLUMN_RENAMES.items():
            # Column is not present, so there is nothing to rename.
            if sliderule_name not in photons.columns:
                continue

            # Names are already identical, so do not rename.
            if sliderule_name == pipeline_name:
                continue

            # If the target pipeline name already exists, preserve that existing
            # column before renaming the SlideRule column into its place.
            if pipeline_name in photons.columns:
                sr_preserved_name = f"{pipeline_name}_sr"

                # Avoid overwriting an existing *_sr column.
                suffix_number = 2
                while sr_preserved_name in photons.columns:
                    sr_preserved_name = f"{pipeline_name}_sr{suffix_number}"
                    suffix_number += 1

                photons = photons.rename(columns={pipeline_name: sr_preserved_name})

            # Now rename the SlideRule column to the AOK pipeline name.
            photons = photons.rename(columns={sliderule_name: pipeline_name})

        duplicate_columns = (
            photons.columns[photons.columns.duplicated()].unique().tolist()
        )
        if duplicate_columns:
            msg = (
                f"ATL03 column renaming produced duplicate columns: {duplicate_columns}"
            )
            raise ValueError(msg)

        return photons

    def rename_atl24_columns(self, atl24_photons: pd.DataFrame) -> pd.DataFrame:
        """
        Rename ATL24 columns from SlideRule names to the names expected by
        the existing AOK pipeline code.

        Columns not present in the dataframe are ignored. Columns not listed in
        ATL24_COLUMN_RENAMES are preserved unchanged.
        """
        ATL24_COLUMN_RENAMES = {
            # SlideRule ATL24 name: AOK pipeline expected name
            # TBD: Fill in based on actual ATL24 output columns.
        }

        rename_map = {
            sliderule_name: pipeline_name
            for sliderule_name, pipeline_name in ATL24_COLUMN_RENAMES.items()
            if sliderule_name in atl24_photons.columns
        }

        return atl24_photons.rename(columns=rename_map).copy()

    def _filter_by_beam_strength(self, photon_df: pd.DataFrame) -> pd.DataFrame:
        """
        Filter photon dataframe by ICESat-2 beam strength.

        None / "strong" -> keep spots 1, 3, 5
        "weak"          -> keep spots 2, 4, 6
        "all"           -> no filtering
        """
        if "spot" not in photon_df.columns:
            msg = (
                "Cannot filter by beam strength: dataframe is missing a 'spot' column."
            )
            raise ValueError(msg)

        beam_strength = self.beams or "strong"

        if beam_strength == "strong":
            spots = (1, 3, 5)
        elif beam_strength == "weak":
            spots = (2, 4, 6)
        elif beam_strength == "all":
            return photon_df.copy()
        else:
            msg = f"beams must be None, 'strong', 'weak', or 'all'. Got: {self.beams!r}"
            raise ValueError(msg)

        return photon_df.loc[photon_df["spot"].isin(spots)].copy()

    def get_sliderule_data(self) -> "DataRequest":
        """
        Use sliderule to get data from all sources and return
        as a list of acquisition results

        """
        sliderule.init("slideruleearth.io")

        atl03_photons = None
        atl24_photons = None

        self.products = []
        self.sources = []
        self.metadata = {}

        if self.need_atl03:
            atl03_photons = self.get_atl03_data()
            # Filter ATL03 photons by beam strength.
            # Default behavior: None -> "strong" -> keep spots 1, 3, 5.
            atl03_photons = self._filter_by_beam_strength(atl03_photons)
            atl03_photons = self.rename_atl03_columns(atl03_photons)

            self.products.append("ATL03")
            self.sources.append("sliderule")
            self.metadata["ATL03"] = {
                "request_type": "atl03",
                "n_rows": len(atl03_photons),
                "columns": list(atl03_photons.columns),
            }

        if self.need_atl24:
            atl24_photons = self.get_atl24_data()

            if atl24_photons is not None:
                # Filter ATL24 data by beam strength.
                # Default behavior: None -> "strong" -> keep spots 1, 3, 5.
                atl24_photons = self._filter_by_beam_strength(atl24_photons)
                # tbd uncomment when rename atl24 columns works
                # atl24_photons = self.rename_atl24_columns(atl24_photons)

                self.products.append("ATL24")
                self.sources.append("sliderule")
                self.metadata["ATL24"] = {
                    "request_type": "atl24",
                    "n_rows": len(atl24_photons),
                    "columns": list(atl24_photons.columns),
                }
            else:
                self.metadata["ATL24"] = {
                    "request_type": "atl24",
                    "status": "unavailable",
                    "n_rows": 0,
                    "columns": [],
                }

        if atl03_photons is not None and atl24_photons is not None:
            self.photons = self._merge_photons(
                atl03_photons=atl03_photons,
                atl24_photons=atl24_photons,
            )
        elif atl03_photons is not None:
            self.photons = atl03_photons
        elif atl24_photons is not None:
            self.photons = atl24_photons
        else:
            self.photons = None

        return self

    # variables I appear to need for icephotons dataset

    """
    # ATL03
    for each beam in beam list: beams from beam list
    'must-have' attributes
    "altas_beam_type", "atlas_spot_number"

    'good to have'
    geolocation (segment_id, within geolocation)
    heights (delta_time, within heights)
    bckgrd_atlas
    geophys_corr
    orbit_info # orbit orientation at time
    ancillary_data - below is list of keys from ancillary data
        "atlas_sdp_gps_epoch",
        "data_end_utc",
        "data_start_utc",
        "end_cycle",
        "end_geoseg",
        "end_gpssow",
        "end_gpsweek",
        "end_orbit",
        "end_region",
        "end_rgt",
        "granule_end_utc",
        "granule_start_utc",
        "release",
        "start_cycle",
        "start_geoseg",
        "start_gpssow",
        "start_gpsweek",
        "start_orbit",
        "start_region",
        "start_rgt",
        "version",
        "tep"
        "dead_time"
        "first_photon_bias"
    calibrations
        "dead_time"
        "first_photon_bias"
    "atlas_impulse_response"
    "tep_histogram"

    # ATL24
    longitude,
    latitude,
    seafloor_elevation_atl24
    "ortho_h", "class_ph"?? not sure if these are atl24 data
    atl24_raw_bathy

    Actual data needed:
    signal_conf_ph -
    quality_ph - bits 0 are only ones not needed. bit 1 (value 2) = possible impulse response effect
      bit 2 (value 4) = possible TEP


    Gebco - just need raster paths


    """
