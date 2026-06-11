"""Utility functions for AOK pipeline."""

from datetime import datetime
from pathlib import Path
from typing import Any

from shapely.geometry import Point
import yaml


def load_test_sites(path: str = "./test_sites.yaml") -> dict[str, Any]:
    """Load test sites from YAML file.

    Parameters
    ----------
    path : str, optional
        Path to the test sites YAML file, by default "./test_sites.yaml"

    Returns
    -------
    dict
        Dictionary containing test site configurations
    """
    with Path(path).open("r") as f:
        return yaml.safe_load(f)


def get_region_by_name(
    name: str, sites: dict[str, Any] | None = None
) -> dict[str, Any]:
    """Retrieve a region configuration by name.

    Parameters
    ----------
    name : str
        Name of the region to retrieve
    sites : dict, optional
        Loaded sites configuration. If None, loads from default path

    Returns
    -------
    dict
        Region configuration dictionary

    Raises
    ------
    KeyError
        If region name is not found in sites
    """
    if sites is None:
        sites = load_test_sites()
    for site in sites["locations"]:
        if site["name"] == name:
            return site
    msg = f"Region not found: {name}"
    raise KeyError(msg)


def check_not_null(key: Any) -> bool:
    """Check if a key or list of keys is not None/empty.

    Parameters
    ----------
    key : str or list
        Single value or list to check

    Returns
    -------
    bool
        True if key is not None and not empty, False otherwise
    """
    return not (key is None or all(elem is None for elem in key))


def get_bbox_shapely(
    lat: float, lon: float, buffer_deg: float
) -> tuple[float, float, float, float]:
    """Create a bounding box around a point using Shapely.

    Parameters
    ----------
    lat : float
        Latitude coordinate
    lon : float
        Longitude coordinate
    buffer_deg : float
        Buffer distance in degrees

    Returns
    -------
    tuple
        Bounding box bounds as (min_lon, min_lat, max_lon, max_lat)
    """
    point = Point(lon, lat)
    # Creating a 'square' buffer
    bbox_poly = point.buffer(buffer_deg, cap_style=3)
    return bbox_poly.bounds  # Returns (min_lon, min_lat, max_lon, max_lat)


def get_spatial_extent(site: dict[str, Any]) -> tuple[float, float, float, float]:
    """Extract spatial extent from site configuration.

    Checks for bbox first, then falls back to lat/lon with buffer.

    Parameters
    ----------
    site : dict
        Site configuration dictionary containing spatial_extent

    Returns
    -------
    tuple
        Bounding box as (min_lon, min_lat, max_lon, max_lat)

    Raises
    ------
    ValueError
        If no valid spatial extent is found
    """
    spatial = site["spatial_extent"]
    if check_not_null(spatial["bbox"]):
        return spatial["bbox"]
    if check_not_null(spatial["latlon"]):
        return get_bbox_shapely(
            spatial["latlon"][0], spatial["latlon"][1], spatial["buffer"]
        )
    msg = "Missing spatial extent"
    raise ValueError(msg)


def get_temporal_extent(site: dict[str, Any]) -> list[datetime]:
    """Extract temporal extent from site configuration.

    Parameters
    ----------
    site : dict[str, Any]
        Site configuration dictionary containing dates

    Returns
    -------
    list[datetime]
        List of [start_datetime, end_datetime]

    Raises
    ------
    ValueError
        If no valid temporal inputs are found
    """
    if any(
        [check_not_null(site["dates"]["start"]), check_not_null(site["dates"]["end"])]
    ):
        return [
            datetime.fromisoformat(site["dates"]["start"]),
            datetime.fromisoformat(site["dates"]["end"]),
        ]
    msg = "Missing temporal inputs"
    raise ValueError(msg)
