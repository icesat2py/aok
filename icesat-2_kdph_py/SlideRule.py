# -*- coding: utf-8 -*-
"""
Created on Fri Feb 14 12:48:13 2025

@author: wayne
"""

from sliderule import sliderule, icesat2
import geopandas as gpd

sliderule.init(verbose=True)

region = sliderule.toregion("bathy.geojson");