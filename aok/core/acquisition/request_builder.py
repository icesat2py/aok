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


def _build_request_from_yaml(yaml_path: str | Path) -> DataRequest:
    """Build a DataRequest from a YAML configuration file."""
    yaml_path = Path(yaml_path)

    with yaml_path.open("r") as f:
        config = yaml.safe_load(f) or {}

    return DataRequest(
        spatial=config["spatial"],
        date_range=config.get("date_range"),
        time_range=config.get("time_range"),
        beams=config.get("beams", []),
        output=config.get("output", "dataframe"),
        need_atl03=config.get("need_atl03", True),
        need_atl24=config.get("need_atl24", False),
        need_gebco=config.get("need_gebco", False),
        need_jpl_temperature=config.get("need_jpl_temperature", False),
        need_shoreline=config.get("need_shoreline", False),
        version=config.get("version"),
        filters=config.get("filters", {}),
    )


def _build_request_from_cli(cli_args: Any) -> DataRequest:
    """Build a DataRequest from parsed command-line arguments."""
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