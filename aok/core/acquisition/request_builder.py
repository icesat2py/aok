"""
Functions for building DataRequest objects from either user-supplied command line arguments or
a user-supplied file (yml, at the moement).
"""

from pathlib import Path
from typing import Any
import yaml

from .base import DataRequest


def build_data_request(cli_args: Any = None, yaml_path: str | Path | None = None) -> DataRequest:
    """
    Build a DataRequest from either command-line arguments or a YAML file.

    Parameters
    ----------
    cli_args
        Parsed command-line arguments, called by main.py - need to figure out how to implement.
    yaml_path
        Path to a YAML file containing DataRequest-compatible fields.

    Returns
    -------
    DataRequest
        Normalized acquisition request object, suitable for passing to request_data.py

    Raises
    ------
    ValueError
        If neither or both input sources are provided, or if required fields
        are missing.
    """
    if (cli_args is None and yaml_path is None) or (cli_args is not None and yaml_path is not None):
        raise ValueError("Provide exactly one of cli_args or yaml_path.")

    if yaml_path is not None:
        return _build_request_from_yaml(yaml_path)

    return _build_request_from_cli(cli_args)


def _coerce_optional_path(value: str | Path | None) -> Path | None:
    """Convert a provided path-like value to Path, or return None."""
    if value is None:
        return None

    try:
        return Path(value)
    except TypeError as e:
        raise TypeError(
            "download_dir must be a path-like string, Path, or None."
        ) from e

def _build_request_from_yaml(yaml_path: str | Path) -> DataRequest:
    """Build a DataRequest from a YAML configuration file."""
    yaml_path = Path(yaml_path)

    with yaml_path.open("r") as f:
        config = yaml.safe_load(f) or {}
    
    kwargs = {
        "spatial": config["spatial"],
    }

    optional_fields = [
        "date_range",
        "time_range",
        "beams",
        "output",
        "need_atl03",
        "need_atl24",
        "need_gebco",
        "need_shoreline",
        "need_jpl_temperature",
        "version_atl03",
        "version_atl24",
        "variables_atl03",
        "variables_atl24",
        "options",
    ]

    for field_name in optional_fields:
        if field_name in config:
            kwargs[field_name] = config[field_name]

    if "download_dir" in config:
        kwargs["download_dir"] = _coerce_optional_path(config["download_dir"])

    return DataRequest(**kwargs)


def _build_request_from_cli(cli_args: Any) -> DataRequest:
    """Build a DataRequest from parsed command-line arguments."""

    """
    return DataRequest(
        spatial=cli_args.spatial,
        date_range=getattr(cli_args, "date_range", None),
        time_range=getattr(cli_args, "time_range", None),
        beams=getattr(cli_args, "beams", []),
        output=getattr(cli_args, "output", "dataframe"),
        need_atl03=getattr(cli_args, "need_atl03", True),
        need_atl24=getattr(cli_args, "need_atl24", False),
        need_gebco=getattr(cli_args, "need_gebco", False),
        need_jpl_temperature=getattr(cli_args, "need_jpl_temperature", False),
        need_shoreline=getattr(cli_args, "need_shoreline", False),
        version=getattr(cli_args, "version", None),
        filters=getattr(cli_args, "filters", {}),
    )
    """
    '''

    CLI_TO_REQUEST_FIELDS = {
    # data paths
    ""
    "target_beams": "beams",
    "atl24_file": "atl24_file",
    }
    '''

    raise NotImplementedError("_build_request_from_cli exists but the logic is not fully implemented yet.")