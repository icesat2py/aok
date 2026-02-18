# -*- coding: utf-8 -*-
"""
Created on Sun Feb 16 21:32:51 2025

@author: wayne
"""
import icepyx as ipx

import json
import math
import warnings

import numpy as np
import matplotlib.pyplot as plt
from matplotlib.colors import ListedColormap

from shapely.geometry import shape, GeometryCollection

# Open a geojson of our area of interest
with open("./data/grandmesa.geojson") as f:
    features = json.load(f)["features"]

grandmesa = GeometryCollection([shape(feature["geometry"]).buffer(0) for feature in features])


# Use our search parameters to setup a search Query
short_name = 'ATL03'
spatial_extent = list(grandmesa.bounds)
date_range = ['2019-12-01','2019-12-12']
region = ipx.Query(short_name, spatial_extent, date_range)

# Display if any data files, or granules, matched our search
region.avail_granules(ids=True)

# Download the granules to a into a folder called 'bosque_primavera_ATL08'
region.download_granules('/data/grandmesa_ATL08')
