"""
    Placeholder for future request data construction.
"""

from .base import DataRequest # data request class
from .request_builder import build_data_request # function for building the DataRequest class from user input
from .icepyx_download import get_icepyx_data # function for aquiring data via icepyx
from .sliderule_download import get_sliderule_data  # function for aquiring data via slide rule

def get_data_from_cloud(request: DataRequest | None = None, 
                        provider: str = "sliderule", 
                        **kwargs):
    """
    Parameters
    ----------
    request
        A preconstructed DataRequest object. If None, request-building inputs
        such as cli_args or yaml_path will be read from kwargs and passed to
        build_data_request().
    provider
        Backend to use for acquisition.
    **kwargs
        Additional keyword arguments. If request is None, these may include
        cli_args or yaml_path for request building. Remaining kwargs are passed
        to the selected backend function.

    Returns
    -------
    AcquisitionResult
        Result returned by the selected acquisition backend.
    """

    # construct request object   
    if request is None:
        cli_args = kwargs.pop("cli_args", None)
        yaml_path = kwargs.pop("yaml_path", None)
        
        if cli_args is None and yaml_path is None:
            raise ValueError("A DataRequest, cli_args, or yaml_path must be provided.")
            
        request = build_data_request(cli_args=cli_args, yaml_path=yaml_path)
    
    if provider == "sliderule":
        return get_sliderule_data(request, **kwargs)
    elif provider == "icepyx":
        return get_icepyx_data(request, **kwargs)
    else:
        raise ValueError(f"Unknown provider: {provider}")