# contains classes for data input objects and data output objects after aquisition from the cloud.
from dataclasses import dataclass, field
from pathlib import Path
from typing import Literal
import warnings

import pandas as pd
<<<<<<< Updated upstream
=======
import geopandas as gpd
from sliderule import sliderule, icesat2 
from aok.core.kd_utils.data_processing import isolate_sea_land_photons
>>>>>>> Stashed changes

OutputType = Literal["dataframe", "geodataframe", "files"]


@dataclass
class AcquisitionResult:
    source: str  # "icepyx" or "sliderule"
    product: str
    photons: pd.DataFrame | None = None
    segments: pd.DataFrame | None = None
    local_files: list[Path] | None = None
    metadata: dict | None = None


@dataclass
class DataRequest:
    """
    Backend request that describes what data should be acquired.

    The class stores the user's requested spatial, temporal, and product information in a shared format with methods that call either icepyx downloader or the SlideRule aquisition code.

    spatial
        Optional spatial region of interest, such as a bounding box or polygon.
        If not set, pull whole Earth. Optional spatial extent of interest,
        provided as a bounding box, list of polygon coordinates, or
        geospatial polygon file.

    date_range:
        Optional start and end date strings.
    time_range:
        Optional start and end time strings.
    beams
        Optional list of beam identifiers to request. # need to check with Jessica if all beams come down, or only some can be selected at a time. might not be necessary to filter at this stage.
    output
        Preferred output format, such as "dataframe", "geodataframe".
    download_dir
        The location to download  files to
    need_atl03
        Whether ATL03 data should be requested. Default: True
    need_atl24
        Whether ATL24 data should be requested. Default: True
    need_gebco
        Whether GEBCO bathymetry data should be requested. Default: True
    need_shoreline
        Whether a simple shoreline spatial shapefile should be aquired. Can make filtering easier. Default: True
    need_jpl_temperature
        Whether sea surface temperature dataset from JPL should be requested. Likely to not need this. Default: False
    version_atl03:
        Optional version of atl03 data that should be requested.
    version_atl03:
        Optional version of atl24 data that should be requested.
    variables_atl03:
        Other variables to pass for atl03 acquisition #unsure if this is necessary
    variables_atl24:
        Other variables to pass for atl24 acquisition  #unsure if this is necessary

    shoreline_data:
        Path to the global shoreline dataset.
    """

    spatial: Any | None = None
    date_range: tuple[str, str] | None = None
    time_range: tuple[str, str] | None = None
    beams: list[str] | None = None
    output: OutputType = "dataframe"
    download_dir: Path | None = None  # HANNAH check if properly specified

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

    options: dict[str, Any] = field(default_factory=dict)

    def validate(self) -> None:
        """
        Placeholder validation for datarequest structure.
        TODO:
        - validate that spatial extent is specified correctly
        - validate that time is specified correctly
        - validate that download paths are coercible to type Path
        - validate that specification is correct for either a sliderule request or icepyx request

        """
        return

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
            raise ValueError("date_range is required.")

        start_date, end_date = self.date_range

        start_time = "00:00:00"
        end_time = "23:59:59"

        if self.time_range is not None:
            start_time, end_time = self.time_range

        t0 = f"{start_date}T{start_time}Z"
        t1 = f"{end_date}T{end_time}Z"
        return t0, t1

    def _query_icepyx(self, product: str) -> ipx.Query:
        """
        Queries icepyx using the DataRequest product.
        Not implemented yet. Draft implementation is below.
        """

        raise NotImplementedError("_query_icepyx exists but is not implemented yet.")
        """
        if product is None:
            raise ValueError("IceSat2 product must be specified.")

        return(ipx.Query(product, self.spatial, self.date_range, self.time_range))
        """

    def _sliderule_output_params(
        self,
        geoparquet_name: str | Path | None = None,
    ) -> dict[str, Any] | None:
        """Build the parameter dictionary for sliderule output location.

        Parameters
        ----------
        geoparquet_name
            Name of the output GeoParquet file. If None, a default filename
            (kdOutputAsGeo.geoparquet) is used.
            This can be varied by the calling method depending on the data
            request.
        """
        if self.output is None:
            warnings.warn(
                "output format was not provided. SlideRule parameters will be built without output.",
                UserWarning,
                stacklevel=2,
            )
            return None

        if self.output in {"dataframe", "geodataframe"}:
            if self.download_dir is None:
                raise ValueError(
                    "download_dir is required when output format is specified."
                )
            if geoparquet_name is None:
                geoparquet_name = "kdOutputAsGeo.geoparquet"
            return {
                "path": str(Path(self.download_dir) / geoparquet_name),
                "format": "parquet",
                "as_geo": True,
                "open_on_complete": True,
            }

        if self.output is not None:
            raise ValueError(f"Unsupported output type: {self.output}")

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
        raise NotImplementedError(
            "_cut_spatial_extent exists but is not implemented yet."
        )
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
        if self.shoreline is :
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
            "quality_ph": [0],
        }

        ## Now adding required auxillary fields
        """
        Note dist_ph_along is possibly already included by
        default in the x_atc which is dist_ph_along +
        segment_distance; ask Chao if his calculations are
        different; note this is used as relative_AT_dist;
        seems that Chao uses distance from first photon.
        """
        atl03_heights = {
            "atl03_ph_fields": [
                "h_ph",  # Photon WGS84 Height; possilby same as "height"
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

        params["atl09_fields"] = [
            "bckgrd_atlas/bckgrd_counts",
            "bckgrd_atlas/bckgrd_counts_reduced",
            "bckgrd_atlas/bckgrd_rate",
        ]

        # auxillary param notes:
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

        # Define user-sepcified output parameters

        if self.output is not None:
            output_params = self._sliderule_output_params("atl03_output.parquet")
            params["output"] = output_params

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
            "atl24": {"class_ph": ["bathymetry", "sea_surface"]},
        }

        output_params = self._sliderule_output_params("atl24_output.parquet")
        if output_params is not None:
            params["output"] = output_params

        if self.beams is not None:
            params["beams"] = self.beams

        if self.variables_atl24 is not None:
            params["atl24_fields"] = self.variables_atl24

        params.update(self.options)
        return params

    def get_atl03_data(self) -> AcquisitionResult:
        params = self.build_atl03_params()
        photons = sliderule.run("atl03x", params)

        metadata = {
            "request_type": "atl03",
            "n_rows": len(photons),
            "columns": list(photons.columns),
        }

        return AcquisitionResult(
            source="sliderule",
            product="ATL03",
            photons=photons,
            metadata=metadata,
        )

    def get_atl24_data(self) -> AcquisitionResult:
        from sliderule import icesat2

        params = self.build_atl24_params()
        segments = icesat2.atl24g(params)

        metadata = {
            "request_type": "atl24",
            "n_rows": len(segments),
            "columns": list(segments.columns),
        }

        return AcquisitionResult(
            source="sliderule",
            product="ATL24",
            segments=segments,
            metadata=metadata,
        )

    def get_sliderule_data(self) -> list[AcquisitionResult]:
        from sliderule import sliderule

        self.validate()
        sliderule.init("slideruleearth.io")

        results: list[AcquisitionResult] = []

        if self.need_atl03:
            results.append(self.get_atl03_data())

        if self.need_atl24:
            results.append(self.get_atl24_data())

        return results

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
