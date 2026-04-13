"""
Acquisition backend for icepyx-based data requests.

This module is a placeholder for future icepyx integration.
"""

# should we first use an optional query to verify data is there? or simply handle the error gracefully?

def construct_query(request):
    """
    Placeholder for future icepyx query construction.

    This function will take the a request of class DataRequest and translate it into an icepyx query. 
    that icepyx can 
    """

    raise NotImplementedError("construct_query exists but is not implemented yet.")

def test_query(request):
    """

    This will test if the data is available and will raise an error if it is not. 
    """
    raise NotImplementedError("test_query exists but is not implemented yet.")

def get_icepyx_data(request):
    """Placeholder for future icepyx acquisition logic."""
    try:
        import icepyx as ipx
    except ImportError as e:
        raise ImportError(
            "icepyx is required for icepyx_download but is not installed."
        ) from e

    # 1: construct query
    # 2: test query
    # 3: request data


    raise NotImplementedError("Icepyx_download exists but the download logic is not fully implemented yet.")