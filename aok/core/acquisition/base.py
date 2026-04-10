# contains classes for data input objects and data output objects after aquisition from the cloud. 
from dataclasses import dataclass
from pathlib import Path
import pandas as pd

OutputType = Literal["dataframe", "geodataframe", "files"]

@dataclass
class DataRequest:
    """
    Backend request that describes what data should be acquired.

    The class stores the user's requested spatial, temporal, and product information in a shared format that can be passed to either the icepyx downloader or the SlideRule aquisition code. 

    spatial
        Spatial region of interest, such as a bounding box or polygon.
    date_range:
        Optional start and end date strings. No default set for None currently.
    time_range: 
        Optional start and end time strings. No default set for None currently.
    beams
        Optional list of beam identifiers to request. # need to check with Jessica if all beams come down, or only some can be selected at a time. might not be necessary to filter at this stage. 
    output
        Preferred output format, such as "dataframe", "geodataframe", or "files". Ideally dataframe for sliderule compatability, but files are allowed for local use. 
    download_dir
        The location to download files to.
    need_atl03
        Whether ATL03 data should be requested. Default: True
    need_atl24
        Whether ATL24 data should be requested. Default: True
    need_gebco
        Whether GEBCO bathymetry data should be requested. Default: True
    need_shoreline
        Whether a simple shoreline spatial shapefile should be aquired. Can make filtering easier. Derault: True
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
    """
    spatial: Any
    date_range: tuple[str, str] | None = None
    time_range: tuple[str, str] | None = None
    beams: list[str] | None = None
    output: OutputType = "dataframe"
    download_dir: str # HANNAH check if properly specified

    need_atl03: bool = True
    need_atl24: bool = True
    need_gebco: bool = True
    need_shoreline: bool = True
    need_jpl_temperature: bool = False


    version_atl03: str | None = None
    version_atl24: str | None = None

    variables_atl03: list[str] | None = None
    variables_atl24: list[str] | None = None

    options: dict[str, Any] = field(default_factory=dict)

@dataclass
class AcquisitionResult:
    source: str                  # "icepyx" or "sliderule"
    product: str
    photons: pd.DataFrame | None = None
    segments: pd.DataFrame | None = None
    local_files: list[Path] | None = None
    metadata: dict | None = None