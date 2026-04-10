"""
    Placeholder for future request data construction.
"""

from .base import DataRequest # data request class
from .request_builder import build_data_request # function for building the DataRequest class from user input
from .icepyx_download import get_icepyx_data # function for aquiring data via icepyx
from .slide_rule import get_sliderule_data  # function for aquiring data via slide rule

def get_data_from_cloud(request: DataRequest, provider: str = "sliderule", **kwargs):
    """
    Checks the provider specified by the user (sliderule or icepyx) and calls the appropriate get_data backend.
    """
    # Todo: figure out how to integrate build_data_request. Should it go in here or in a different function? if here, need to change arguments above. if other function, how to integrate with main?
    
    if provider == "sliderule":
        return get_sliderule_data(request, **kwargs)
    elif provider == "icepyx":
        return get_icepyx_data(request, **kwargs)
    else:
        raise ValueError(f"Unknown provider: {provider}")

    