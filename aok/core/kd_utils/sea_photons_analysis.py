from datetime import datetime

import netCDF4
import numpy as np
import pandas as pd


# Function to apply binning beam-by-beam by calling the function of horizontal_vertical_bin_dataset
def process_sea_photon_binning(sea_photon_dataset, horizontal_res, vertical_res):
    """
    Apply horizontal and vertical binning to each beam.

    Flowchart steps:
      3 — Choose along-track (x) and vertical (z) bin sizes
          (e.g., 500 m in x, 0.25 m in z).
      4 — Build vertical histograms of photon counts using selected x, z bin sizes.
    """
    # Initialize list to store results from each beam
    binned_beam_datasets = []

    # Group the dataset by 'beam_id' and process each group separately
    for beam_id, beam_data in sea_photon_dataset.groupby("beam_id"):
        print(f"Processing binning for beam: {beam_id}")

        # Apply binning to the current beam dataset
        binned_beam_data = horizontal_vertical_bin_dataset(
            beam_data, horizontal_res, vertical_res
        )

        # Append the binned data for the current beam to the list
        binned_beam_datasets.append(binned_beam_data)

    # Combine all binned beam datasets into a single DataFrame
    binned_dataset_sea_surface = pd.concat(binned_beam_datasets, ignore_index=True)

    return binned_dataset_sea_surface


# Bin data along vertical and horizontal scales
def horizontal_vertical_bin_dataset(dataset, lat_res, vertical_res):
    """
    Bin data along vertical and horizontal scales for later segmentation.

    Flowchart steps:
      3 — Choose along-track (x) and vertical (z) bin sizes
          (e.g., 500 m in x, 0.25 m in z).
      4 — Build vertical histograms of photon counts using selected x, z bin sizes.
      10 — Re-build histograms based on corrected depths (called again after
           refraction correction when apply_post_refraction_refit is enabled).
    """

    # Filter values within the range (-50, 10), because photons elevation outside this range will be real noise
    valid_range = (-70, 5)
    valid_mask = (dataset["photon_height"] > valid_range[0]) & (
        dataset["photon_height"] < valid_range[1]
    )

    # Apply the valid_mask to filter unwanted values
    # and create a copy to avoid SettingWithCopyWarning
    filtered_dataset = dataset[valid_mask].copy()

    # Calculate the number of height bins
    height_range = abs(
        filtered_dataset["photon_height"].max()
        - filtered_dataset["photon_height"].min()
    )
    height_bin_number = max(
        1, round(height_range / vertical_res)
    )  # Ensure at least one bin

    # Calculate the number of latitude bins
    lat_range = abs(filtered_dataset["lat"].max() - filtered_dataset["lat"].min())
    lat_bin_number = max(1, round(lat_range / lat_res))  # Ensure at least one bin

    # Create bins for latitude
    lat_bins = pd.cut(
        filtered_dataset["lat"], bins=lat_bin_number, labels=np.arange(lat_bin_number)
    )

    # Create bins for height
    height_bins = pd.cut(
        filtered_dataset["photon_height"],
        bins=height_bin_number,
        labels=np.round(
            np.linspace(
                filtered_dataset["photon_height"].min(),
                filtered_dataset["photon_height"].max(),
                num=height_bin_number,
            ),
            decimals=1,
        ),
    )

    # Add bins to dataframe using .loc to avoid SettingWithCopyWarning
    filtered_dataset.loc[:, "lat_bins"] = lat_bins
    filtered_dataset.loc[:, "height_bins"] = height_bins
    filtered_dataset = filtered_dataset.reset_index(drop=True)

    return filtered_dataset


def get_water_temp(date_year, date_month, date_day, latitude, longitude):
    """
    Pull down surface water temperature along the track from the JPL GHRSST opendap website.

    The GHRSST data are gridded tiles with dimension 17998 x 35999.
    To get the specific grid tile of the SST, you must convert from lat, lon coordinates
    to the gridded tile ratio of the SST data product using the coordinates of the IS2 data.
    """
    # Get date from data filename
    # data_path[-33:-25]
    date = date_year + date_month + date_day
    # date[0:4]
    year = date_year
    # date[4:6]
    month = date_month
    # date[6:8]
    day = date_day
    day_of_year = str(datetime.strptime(date, "%Y%m%d").timetuple().tm_yday)
    # Add zero in front of day of year string
    zero_day_of_year = day_of_year.zfill(3)

    # Calculate ratio of latitude from mid-point of IS2 track
    old_lat = latitude.mean()
    old_lat_min = -90
    old_lat_max = 90
    new_lat_min = 0
    new_lat_max = 17998

    new_lat = round(
        ((old_lat - old_lat_min) / (old_lat_max - old_lat_min))
        * (new_lat_max - new_lat_min)
        + new_lat_min
    )

    # Calculate ratio of longitude from mid-point of IS2 track
    old_lon = longitude.mean()
    old_lon_min = -180
    old_lon_max = 180
    new_lon_min = 0
    new_lon_max = 35999

    new_lon = round(
        ((old_lon - old_lon_min) / (old_lon_max - old_lon_min))
        * (new_lon_max - new_lon_min)
        + new_lon_min
    )

    # Access the SST data using the JPL OpenDap interface
    url = (
        "https://opendap.jpl.nasa.gov/opendap/OceanTemperature/ghrsst/data/GDS2/L4/GLOB/JPL/MUR/v4.1/"
        + str(year)
        + "/"
        + str(zero_day_of_year)
        + "/"
        + str(date)
        + "090000-JPL-L4_GHRSST-SSTfnd-MUR-GLOB-v02.0-fv04.1.nc"
    )

    dataset = netCDF4.Dataset(url)

    # Access the data and convert the temperature from K to C
    water_temp = dataset["analysed_sst"][0, new_lat, new_lon] - 273.15
    return water_temp
