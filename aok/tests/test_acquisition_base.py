from datetime import datetime

import pytest

from aok.core.acquisition.base import DataRequest


@pytest.fixture
def basic_request():
    spatial_extent = [39.6, -76.9, 37.3, -75.6]
    srextent = [
        {"lon": spatial_extent[1], "lat": spatial_extent[0]},
        {"lon": spatial_extent[3], "lat": spatial_extent[0]},
        {"lon": spatial_extent[3], "lat": spatial_extent[2]},
        {"lon": spatial_extent[1], "lat": spatial_extent[2]},
        {"lon": spatial_extent[1], "lat": spatial_extent[0]},
    ]
    temporal = [datetime(2020, 3, 15, 6), datetime(2020, 3, 15, 9)]
    return DataRequest(
        spatial=srextent,
    )


def test_data_request_defaults():
    """
    Tests if defaults are correct. Note - should revist default choices.
    """
    req = DataRequest()

    assert req.spatial is None
    assert req.date_range is None
    assert req.time_range is None
    assert req.beams is None
    assert req.output == "dataframe"
    assert req.download_dir is None
    assert req.need_atl03 is True
    assert req.need_atl24 is True
    assert req.need_gebco is True
    assert req.need_shoreline is True
    assert req.need_jpl_temperature is False
    assert req.version_atl03 is None
    assert req.version_atl24 is None
    assert req.variables_atl03 is None
    assert req.variables_atl24 is None
    assert req.options == {}


"""
Checks validation logic for DataRequest
"""
"""
def test_validate_requires_date_range():
    spatial_extent = [39.6, -76.9, 37.3, -75.6]
    request = DataRequest(spatial= spatial_extent)

    with pytest.raises(ValueError, match="date_range is required"):
        request.validate()
"""


def test_validate_accepts_minimal_valid_request():
    spatial_extent = [39.6, -76.9, 37.3, -75.6]
    request = DataRequest(spatial=spatial_extent)

    request.validate()  # should not raise


""" methods tests """


def test_sliderule_output_params_warns_of_no_output_format(basic_request):
    basic_request.output = None
    with pytest.warns(
        UserWarning,
        match="output format was not provided. SlideRule parameters will be built without output.",
    ):
        params = basic_request._sliderule_output_params()


def test_sliderule_output_params_uses_default_filename(basic_request, tmp_path):
    basic_request.output = "geodataframe"
    basic_request.download_dir = tmp_path

    params = basic_request._sliderule_output_params()

    assert params == {
        "path": str(tmp_path / "kdOutputAsGeo.geoparquet"),
        "format": "parquet",
        "as_geo": True,
        "open_on_complete": True,
    }


def test_sliderule_output_params_uses_custom_filename(basic_request, tmp_path):
    basic_request.output = "geodataframe"
    basic_request.download_dir = tmp_path

    params = basic_request._sliderule_output_params("atl03_photons.geoparquet")

    assert params == {
        "path": str(tmp_path / "atl03_photons.geoparquet"),
        "format": "parquet",
        "as_geo": True,
        "open_on_complete": True,
    }


def test_sliderule_time_range_requires_dates(basic_request):
    basic_request.date_range = None
    with pytest.raises(ValueError, match="date_range is required."):
        basic_request._sliderule_time_range()


def test_sliderule_time_range_defaults(basic_request):
    basic_request.date_range = ("2018-10-22", "2018-10-26")
    basic_request.time_range = None
    t0, t1 = basic_request._sliderule_time_range()
    assert t0 == "2018-10-22T00:00:00Z"
    assert t1 == "2018-10-26T23:59:59Z"


def test_sliderule_time_range(basic_request):
    basic_request.date_range = ("2018-10-22", "2018-10-26")
    basic_request.time_range = ("06:00:00", "18:00:00")
    t0, t1 = basic_request._sliderule_time_range()
    assert t0 == "2018-10-22T06:00:00Z"
    assert t1 == "2018-10-26T18:00:00Z"


def test_build_atl03_params_basic(basic_request):
    basic_request.date_range = ("2018-10-22", "2018-10-26")
    basic_request.time_range = None
    basic_request.output = None
    basic_request.beams = None
    basic_request.variables_atl03 = None

    params = basic_request.build_atl03_params()

    assert params["poly"] == basic_request.spatial
    assert params["t0"] == "2018-10-22T00:00:00Z"
    assert params["t1"] == "2018-10-26T23:59:59Z"
    assert params["srt"] == [0, 1, 2, 3, 4]
    assert params["cnf"] == [-2, -1, 0, 1, 2, 3, 4]
    assert params["quality_ph"] == [0]

    assert params["atl03_ph_fields"] == [
        "h_ph",
        "delta_time",
        "dist_ph_along",
    ]

    assert params["atl03_geo_fields"] == [
        "segment_id",
        "ph_index_beg",
        "segment_ph_cnt",
        "segment_dist_x",
        "segment_length",
        "reference_photon_lat",
        "reference_photon_lon",
        "ref_elev",
        "ref_azimuth",
    ]

    assert params["atl03_bckgrd_fields"] == [
        "bckgrd_rate",
    ]

    assert params["atl03_cor_fields"] == [
        "geoid",
    ]
    assert params["atl09_fields"] == [
        "bckgrd_atlas/bckgrd_counts",
        "bckgrd_atlas/bckgrd_counts_reduced",
        "bckgrd_atlas/bckgrd_rate",
    ]

    assert "output" not in params


def test_build_atl03_params_adds_file_output(basic_request, tmp_path):
    basic_request.date_range = ("2018-10-22", "2018-10-26")
    basic_request.time_range = None
    basic_request.output = "geodataframe"
    basic_request.download_dir = tmp_path
    basic_request.beams = None
    basic_request.variables_atl03 = None

    params = basic_request.build_atl03_params()

    assert params["output"] == {
        "path": str(tmp_path / "atl03_output.parquet"),
        "format": "parquet",
        "as_geo": True,
        "open_on_complete": True,
    }


def test_build_atl03_params_adds_gebco(basic_request, tmp_path):
    basic_request.date_range = ("2018-10-22", "2018-10-26")
    basic_request.time_range = None
    basic_request.download_dir = tmp_path
    basic_request.beams = None
    basic_request.variables_atl03 = None
    basic_request.need_gebco = True

    params = basic_request.build_atl03_params()

    assert params["samples"] == {"gebco": {"asset": "gebco-s3"}}


def test_build_atl03_params_does_not_add_gebco(basic_request, tmp_path):
    basic_request.date_range = ("2018-10-22", "2018-10-26")
    basic_request.time_range = None
    basic_request.download_dir = tmp_path
    basic_request.beams = None
    basic_request.variables_atl03 = None
    basic_request.need_gebco = False

    params = basic_request.build_atl03_params()

    assert "samples" not in params
