"""Integration test for Kd calculation from SlideRule data.

This test verifies that the Kd calculation pipeline produces expected outputs
by comparing calculated results against truth values stored in kd_ref.csv.

The test setup is based on the "Calculate Kd from SlideRule" section of
compare_run_pipelines.ipynb and uses spatial/temporal inputs from test_sites.yaml.
"""

import pytest
import pandas as pd
import numpy as np
from pathlib import Path
from datetime import datetime
from shapely.geometry import Point
import yaml

import aok.main


# Helper functions for loading test site configuration
def load_test_sites(path="./test_sites.yaml"):
    """Load test site configuration from YAML file."""
    with Path(path).open("r") as f:
        return yaml.safe_load(f)


def get_region_by_name(name, sites=None):
    """Get region configuration by name from test sites."""
    if sites is None:
        sites = load_test_sites()
    for site in sites["locations"]:
        if site["name"] == name:
            return site
    raise KeyError(f"Region not found: {name}")


def check_not_null(key):
    """Check if a configuration key is not null."""
    if key is None or all(l is None for l in key):
        return False
    else:
        return True


def get_bbox_shapely(lat, lon, buffer_deg) -> list:
    """Create a bounding box from lat/lon with buffer."""
    point = Point(lon, lat)
    # Creating a 'square' buffer
    bbox_poly = point.buffer(buffer_deg, cap_style=3)
    return list(bbox_poly.bounds)  # Returns [min_lon, min_lat, max_lon, max_lat]


@pytest.fixture
def test_site_config():
    """Load and return test site configuration."""
    site = get_region_by_name("cook_inlet_very_turbid_water")
    return site


@pytest.fixture
def spatial_extent(test_site_config):
    """Extract spatial extent from test site configuration."""
    spatial = test_site_config["spatial_extent"]
    if check_not_null(spatial["bbox"]):
        return spatial["bbox"]
    elif check_not_null(spatial["latlon"]):
        return get_bbox_shapely(
            spatial["latlon"][0],
            spatial["latlon"][1],
            spatial["buffer"]
        )
    else:
        raise ValueError("Missing spatial extent in test site config")


@pytest.fixture
def temporal_extent(test_site_config):
    """Extract temporal extent from test site configuration."""
    if any([
        check_not_null(test_site_config["dates"]["start"]),
        check_not_null(test_site_config["dates"]["end"])
    ]):
        return [
            test_site_config["dates"]["start"],
            test_site_config["dates"]["end"],
        ]
    else:
        raise ValueError("Missing temporal inputs in test site config")


@pytest.fixture
def truth_data():
    """Load truth CSV with expected Kd values."""
    truth_path = Path(__file__).parent / "kd_ref.csv"
    return pd.read_csv(truth_path)



@pytest.fixture
def kd_result(spatial_extent, temporal_extent):
    """Calculate Kd using the pipeline with test site spatial/temporal inputs."""
    # Get configuration from config.yaml
    kd_args = aok.main.get_args()

    # Override spatial and temporal extents with test site values
    kd_args.spatial = spatial_extent
    kd_args.temporal = temporal_extent

    # Run the Kd calculation pipeline
    return aok.main.run_pipeline(kd_args)


def test_kd_calculation(kd_result):
    """Test that Kd calculation pipeline runs successfully with test inputs."""
    result = kd_result
    # Verify we got results
    assert result is not None, "Pipeline returned None"
    assert len(result) > 0, "Pipeline returned empty results"

    # Verify expected columns are present
    expected_columns = ["kd", "height", "reference_photon_lat", "reference_photon_lon"]
    for col in expected_columns:
        assert col in result.columns, f"Missing expected column: {col}"



def test_kd_values_within_range(kd_result):
    """Test that calculated Kd values are within realistic ranges."""
    result = kd_result
    # Check Kd values are within realistic range for water (typically 0.01 to 2.0)
    assert (result["kd"] > 0).all(), "Found non-positive Kd values"
    assert (result["kd"] < 2.0).all(), "Found Kd values > 2.0 (unrealistic)"



def test_kd_matches_truth_values(kd_result, truth_data):
    """Test that calculated Kd values match expected truth values.

    This test compares the calculated Kd output to pre-computed truth values
    stored in kd_ref.csv, with some tolerance for numerical differences.
    """
    result = kd_result
    # Verify result has same number of rows as truth data
    assert len(result) == len(truth_data), (
        f"Row count mismatch: got {len(result)} rows, expected {len(truth_data)}"
    )

    # Compare Kd values with tolerance for floating point differences
    # Allow 5% relative tolerance for Kd values
    np.testing.assert_allclose(
        result["kd"].values,
        truth_data["kd"].values,
        rtol=0.05,
        err_msg="Calculated Kd values do not match truth values within tolerance"
    )

    # Verify photon locations match (should be exact)
    pd.testing.assert_series_equal(
        result["reference_photon_lat"].reset_index(drop=True),
        truth_data["reference_photon_lat"].reset_index(drop=True),
        check_names=False,
        check_dtype=False,
        atol=1e-6,
    )

    pd.testing.assert_series_equal(
        result["reference_photon_lon"].reset_index(drop=True),
        truth_data["reference_photon_lon"].reset_index(drop=True),
        check_names=False,
        check_dtype=False,
        atol=1e-6,
    )
