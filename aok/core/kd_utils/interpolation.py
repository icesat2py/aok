# utils/interpolation.py

import scipy.interpolate


def interpolate_labels(segment_lat, labels):
    model = scipy.interpolate.interp1d(segment_lat, labels, fill_value="extrapolate")
    return model


def apply_interpolation(model, lat_ph):
    return model(lat_ph)


def geoid_correction(lat_ph, segment_lat, geoid):
    model = interpolate_labels(segment_lat, geoid)
    return apply_interpolation(model, lat_ph)
