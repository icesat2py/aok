"""
Acquisition backend for SlideRule-based data requests.

This module is a placeholder for future SlideRule integration.
"""

def get_atl03_data(params): #-> statsistics, geodataframe
    """Placeholder for future SlideRule atl03 aquisition."""

    '''

    # Latch Start Time
    perf_start = time.perf_counter()
    
    # https://docs.slideruleearth.io/api_reference/icesat2.html
    # Request ATL03 Data
    yapc_sr = icesat2.atl03sp(parms) #, resources=grans) # returns geodataframe
    
    # Latch Stop Time
    perf_stop = time.perf_counter()

    # Display Statistics
    perf_duration = perf_stop - perf_start
    print("Completed in {:.3f} seconds of wall-clock time".format(perf_duration))
    print("Reference Ground Tracks: {}".format(yapc_sr["rgt"].unique()))
    print("Cycles: {}".format(yapc_sr["cycle"].unique()))
    print("Received {} elevations".format(yapc_sr.shape[0]))



    # this version downloads to location:
    # Execute request (returns file path when output format is specified)
    output_file = sliderule.run("atl03x", parms)
    print(f"Data saved to: {output_file}")
    '''
    raise NotImplementedError("SlideRule acquisition is not tested yet.")

def get_atl24_data(params): #-> statsistics, geodataframe
    """Placeholder for future SlideRule atl24 aquisition."""

    '''
    # similar to get_atl03_data but uses alt24 instead
    sliderule.icesat2.atl24v(parm, resource)

    '''
    raise NotImplementedError("SlideRule acquisition is not tested yet.")



def get_sliderule_data(request) -> AcquisitionResult:
    """Placeholder for future SlideRule acquisition logic."""
    from sliderule import sliderule, icesat2 #, io

    # Initialize SlideRule client # can this be done after building the request?
    sliderule.init("slideruleearth.io")

    # Build ATL03 Request
    # request_builder.atl03(request)
    parms = {
        "poly": srextent,
        "t0": f'{temporal[0]:%Y-%m-%dT%H:%M:%SZ}',
        "t1": f'{temporal[1]:%Y-%m-%dT%H:%M:%SZ}',
        "srt": [0,1,2,3,4],
        "cnf": [-2, -1, 0, 1, 2, 3, 4],
        "output": {
            "path": "kdOutputAsGeo.geoparquet",
            "format": "parquet",
            "as_geo": True,
            "open_on_complete": True
        }
    }

    statstics, geodataframe <- get_atl03_data(parms)

    # Latch Start Time
    perf_start = time.perf_counter()
    
    # https://docs.slideruleearth.io/api_reference/icesat2.html
    # Request ATL03 Data
    yapc_sr = icesat2.atl03sp(parms) #, resources=grans) # returns geodataframe
    
    # Latch Stop Time
    perf_stop = time.perf_counter()

    # Display Statistics
    perf_duration = perf_stop - perf_start
    print("Completed in {:.3f} seconds of wall-clock time".format(perf_duration))
    print("Reference Ground Tracks: {}".format(yapc_sr["rgt"].unique()))
    print("Cycles: {}".format(yapc_sr["cycle"].unique()))
    print("Received {} elevations".format(yapc_sr.shape[0]))
    
    raise NotImplementedError("SlideRule acquisition is not tested yet.")