import pandas as pd
import pytest

from aok.core.datarequest import DataRequest
from aok.tests.column_requirements import (
    REQUIRED_ATL03_COLUMNS,
    REQUIRED_ATL24_COLUMNS,
    REQUIRED_GEBCO_COLUMNS,
)


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
    return DataRequest(
        spatial=srextent,
    )


@pytest.fixture
def fake_atl03_photons():
    photons = pd.DataFrame(
        {column: [None, None, None] for column in REQUIRED_ATL03_COLUMNS}
    )

    photons["time_ns"] = [1, 2, 3]
    photons["x_atc"] = [0.0, 2.0, 3.0]
    photons["height"] = [10.0, 20.0, 30.0]
    photons["atl03_cnf"] = [1, 0, 4]

    return photons.set_index("time_ns")


@pytest.fixture
def fake_atl03_photons_with_gebco(fake_atl03_photons):
    photons = fake_atl03_photons.copy()

    photons["gebco.fileid"] = ["gebco_1", "gebco_1", "gebco_1"]
    photons["gebco.time_ns"] = [1, 2, 3]
    photons["gebco.value"] = [-12.5, -13.0, -11.8]

    return photons


@pytest.fixture
def fake_atl24_photons():
    photons = pd.DataFrame({column: [None, None] for column in REQUIRED_ATL24_COLUMNS})
    photons["time_ns"] = [1, 3]
    photons["x_atc"] = [0.0, 3.0]
    photons["class_ph"] = [40, 40]
    photons["ortho_h"] = [-5.0, 0.2]

    return photons.set_index("time_ns")


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

    assert req.photons is None
    assert req.metadata == {}
    assert req.sources == []
    assert req.products == []


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
    assert params["cnf"] == [0, 1, 2, 3, 4]
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
        "high_rate/backg_c",
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


def test_atl03_photons_with_gebco_have_required_columns(
    fake_atl03_photons_with_gebco,
):
    required_columns = REQUIRED_ATL03_COLUMNS.union(REQUIRED_GEBCO_COLUMNS)

    missing_columns = required_columns.difference(fake_atl03_photons_with_gebco.columns)

    assert not missing_columns, (
        "ATL03 photons with GEBCO are missing required columns: "
        f"{sorted(missing_columns)}"
    )


def test_get_atl03_data_calls_sliderule_run(
    monkeypatch,
    basic_request,
    fake_atl03_photons,
):
    basic_request.date_range = ("2018-10-22", "2018-10-26")

    calls = []

    def fake_run(api, params):
        calls.append({"api": api, "parms": params})
        return fake_atl03_photons

    monkeypatch.setattr(
        "aok.core.datarequest.sliderule.run",
        fake_run,
    )

    photons = basic_request.get_atl03_data()

    assert photons is fake_atl03_photons
    assert len(calls) == 1
    assert calls[0]["api"] == "atl03x"
    assert calls[0]["parms"]["t0"] == "2018-10-22T00:00:00Z"
    assert calls[0]["parms"]["t1"] == "2018-10-26T23:59:59Z"


def test_get_atl24_data_calls_sliderule_run(
    monkeypatch,
    basic_request,
    fake_atl24_photons,
):
    basic_request.date_range = ("2018-10-22", "2018-10-26")
    basic_request.output = None

    calls = []

    def fake_run(api, params):
        calls.append({"api": api, "parms": params})
        return fake_atl24_photons

    monkeypatch.setattr(
        "aok.core.datarequest.sliderule.run",
        fake_run,
    )

    photons = basic_request.get_atl24_data()

    assert photons is fake_atl24_photons
    assert len(calls) == 1
    assert calls[0]["api"] == "atl24x"
    assert calls[0]["parms"]["t0"] == "2018-10-22T00:00:00Z"
    assert calls[0]["parms"]["t1"] == "2018-10-26T23:59:59Z"


# Beam filtering tests
def make_spot_photon_df():
    return pd.DataFrame(
        {
            "spot": [1, 2, 3, 4, 5, 6],
            "height": [-1.0, -2.0, -3.0, -4.0, -5.0, -6.0],
        }
    )


def test_filter_by_beam_strength_none_defaults_to_strong():
    request = DataRequest(beams=None)

    result = request._filter_by_beam_strength(make_spot_photon_df())

    assert list(result["spot"]) == [1, 3, 5]


def test_filter_by_beam_strength_strong_keeps_strong_spots():
    request = DataRequest(beams="strong")

    result = request._filter_by_beam_strength(make_spot_photon_df())

    assert list(result["spot"]) == [1, 3, 5]


def test_filter_by_beam_strength_weak_keeps_weak_spots():
    request = DataRequest(beams="weak")

    result = request._filter_by_beam_strength(make_spot_photon_df())

    assert list(result["spot"]) == [2, 4, 6]


def test_filter_by_beam_strength_all_keeps_all_spots():
    request = DataRequest(beams="all")

    result = request._filter_by_beam_strength(make_spot_photon_df())

    pd.testing.assert_frame_equal(
        result.reset_index(drop=True),
        make_spot_photon_df(),
    )


def test_get_sliderule_data_filters_atl03_by_beam_strength(monkeypatch):
    request = DataRequest(
        spatial=[-70, 42, -69, 43],
        date_range=("2024-01-01", "2024-01-02"),
        need_atl03=True,
        need_atl24=False,
        beams="weak",
    )

    raw_atl03 = pd.DataFrame(
        {
            "spot": [1, 2, 3, 4, 5, 6],
            "height": [-1.0, -2.0, -3.0, -4.0, -5.0, -6.0],
        }
    )

    monkeypatch.setattr(request, "get_atl03_data", lambda: raw_atl03)

    result_request = request.get_sliderule_data()

    assert list(result_request.photons["spot"]) == [2, 4, 6]
    assert result_request.metadata["ATL03"]["n_rows"] == 3


def test_filter_by_beam_strength_rejects_invalid_value():
    request = DataRequest(beams="medium")

    with pytest.raises(ValueError, match="beams must be"):
        request._filter_by_beam_strength(make_spot_photon_df())


def test_merge_photons_left_joins_atl24_to_atl03(
    basic_request,
    fake_atl03_photons,
    fake_atl24_photons,
):
    merged = basic_request._merge_photons(
        atl03_photons=fake_atl03_photons,
        atl24_photons=fake_atl24_photons,
    )

    assert merged.index.name == "time_ns"
    assert list(merged.index) == [1, 2, 3]
    assert list(merged["height"]) == [10.0, 20.0, 30.0]
    assert list(merged["atl03_cnf"]) == [1, 0, 4]
    assert merged.loc[1, "ortho_h"] == -5.0
    assert merged.loc[3, "ortho_h"] == 0.2
    assert "x_atc_atl24" in merged.columns


def test_merge_photons_requires_time_ns_in_atl03(
    basic_request,
    fake_atl24_photons,
):
    atl03 = pd.DataFrame({"height": [10.0, 20.0]})

    with pytest.raises(
        ValueError,
        match="ATL03 photons are missing 'time_ns'",
    ):
        basic_request._merge_photons(
            atl03_photons=atl03,
            atl24_photons=fake_atl24_photons,
        )


def test_merge_photons_requires_time_ns_in_atl24(
    basic_request,
    fake_atl03_photons,
):
    atl24 = pd.DataFrame({"class_ph": [40, 41]})

    with pytest.raises(
        ValueError,
        match="ATL24 photons are missing 'time_ns'",
    ):
        basic_request._merge_photons(
            atl03_photons=fake_atl03_photons,
            atl24_photons=atl24,
        )


def test_get_sliderule_data_fetches_and_merges_atl03_and_atl24(
    monkeypatch,
    basic_request,
    fake_atl03_photons,
    fake_atl24_photons,
):
    basic_request.date_range = ("2018-10-22", "2018-10-26")
    basic_request.output = None
    basic_request.need_atl03 = True
    basic_request.need_atl24 = True
    basic_request.beams = "all"  # so filtering does not occur in merge test

    init_calls = []
    run_calls = []

    def fake_init(slidrule_url):
        init_calls.append(slidrule_url)

    def fake_run(api, params):
        run_calls.append({"api": api, "parms": params})

        if api == "atl03x":
            return fake_atl03_photons

        if api == "atl24x":
            return fake_atl24_photons

        raise AssertionError(f"Unexpected SlideRule API: {api}")

    monkeypatch.setattr(
        "aok.core.datarequest.sliderule.init",
        fake_init,
    )
    monkeypatch.setattr(
        "aok.core.datarequest.sliderule.run",
        fake_run,
    )

    result = basic_request.get_sliderule_data()

    assert result is basic_request

    assert init_calls == ["slideruleearth.io"]
    assert [call["api"] for call in run_calls] == ["atl03x", "atl24x"]

    assert basic_request.photons is not None
    assert list(basic_request.photons.index) == [1, 2, 3]
    assert "x_atc" in basic_request.photons.columns
    assert "height" in basic_request.photons.columns
    assert "class_ph" in basic_request.photons.columns
    assert "x_atc_atl24" in basic_request.photons.columns
    assert list(basic_request.photons["class_ph"].isna()) == [False, True, False]

    assert basic_request.products == ["ATL03", "ATL24"]
    assert basic_request.sources == ["sliderule", "sliderule"]

    assert basic_request.metadata["ATL03"]["request_type"] == "atl03"
    assert basic_request.metadata["ATL03"]["n_rows"] == 3
    assert set(basic_request.metadata["ATL03"]["columns"]) == set(
        fake_atl03_photons.columns
    )
    assert basic_request.metadata["ATL24"]["request_type"] == "atl24"
    assert basic_request.metadata["ATL24"]["n_rows"] == 2
    assert set(basic_request.metadata["ATL24"]["columns"]) == set(
        fake_atl24_photons.columns
    )
