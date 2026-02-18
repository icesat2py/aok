import logging
from typing import Dict, List, Optional

import numpy as np
import pandas as pd
from pyproj import Geod, Proj

from kd_utils.data_processing import convert_wgs_to_utm

logger = logging.getLogger(__name__)


def _get_beam_id_from_track_pair(df: pd.DataFrame) -> pd.Series:
    if 'gt' in df.columns:
        return df['gt'].astype(str)
    if 'track' in df.columns and 'pair' in df.columns:
        suffix = df['pair'].map({0: 'l', 1: 'r'}).fillna('x')
        return 'gt' + df['track'].astype(int).astype(str) + suffix
    return pd.Series(['unknown'] * len(df), index=df.index, dtype='object')


def _infer_strong_beam_suffix(df: pd.DataFrame) -> Optional[str]:
    if 'sc_orient' not in df.columns or df.empty:
        return None
    orient = df['sc_orient'].dropna()
    if orient.empty:
        return None
    # Same logic as your Florida script.
    return 'l' if int(orient.iloc[0]) == 0 else 'r'


def _normalize_signal_conf(values: pd.Series) -> pd.Series:
    def to_scalar(v):
        if isinstance(v, (list, tuple, np.ndarray)):
            if len(v) == 0:
                return np.nan
            return float(v[0])
        try:
            return float(v)
        except Exception:
            return np.nan
    return values.apply(to_scalar)


def _relative_distance_km_per_beam(df: pd.DataFrame) -> pd.Series:
    out = pd.Series(np.nan, index=df.index, dtype=float)
    for beam_id, beam_df in df.groupby('beam_id'):
        beam_df = beam_df.sort_values('delta_time')
        if 'segment_dist' in beam_df.columns:
            rel_km = (beam_df['segment_dist'] - beam_df['segment_dist'].min()) / 1000.0
            out.loc[beam_df.index] = rel_km.values
            continue

        lons = beam_df['longitude'].to_numpy(dtype=float)
        lats = beam_df['latitude'].to_numpy(dtype=float)
        if len(lons) == 0:
            continue
        geod = Geod(ellps='WGS84')
        cumulative_m = np.zeros(len(lons), dtype=float)
        for i in range(1, len(lons)):
            _, _, dist_m = geod.inv(lons[i - 1], lats[i - 1], lons[i], lats[i])
            cumulative_m[i] = cumulative_m[i - 1] + max(dist_m, 0.0)
        out.loc[beam_df.index] = cumulative_m / 1000.0
    return out


def _project_to_utm(df: pd.DataFrame) -> pd.DataFrame:
    projected = df.copy()
    projected['lon'] = np.nan
    projected['lat'] = np.nan
    for beam_id, beam_df in projected.groupby('beam_id'):
        if beam_df.empty:
            continue
        lon0 = float(beam_df['longitude'].iloc[0])
        lat0 = float(beam_df['latitude'].iloc[0])
        epsg = convert_wgs_to_utm(lon0, lat0)
        proj = Proj(epsg)
        x, y = proj(beam_df['longitude'].to_numpy(dtype=float), beam_df['latitude'].to_numpy(dtype=float))
        projected.loc[beam_df.index, 'lon'] = x
        projected.loc[beam_df.index, 'lat'] = y
    return projected


def sliderule_to_framework_dataset(
    atl03_gdf,
    strong_beams_only: bool = True,
) -> pd.DataFrame:
    """
    Convert SlideRule ATL03 photon GeoDataFrame to the framework's sea_photon_dataset schema.
    """
    if atl03_gdf is None or len(atl03_gdf) == 0:
        return pd.DataFrame(columns=[
            'beam_id', 'latitude', 'longitude', 'lat', 'lon', 'photon_height',
            'quality_ph', 'photon_conf', 'ref_elevation', 'ref_azimuth',
            'relative_AT_dist', 'solar_elevation', 'background_rate', 'is_land_label'
        ])

    src = pd.DataFrame(atl03_gdf).copy()
    src['beam_id'] = _get_beam_id_from_track_pair(src)
    if strong_beams_only:
        strong_suffix = _infer_strong_beam_suffix(src)
        if strong_suffix in ('l', 'r'):
            src = src[src['beam_id'].str.endswith(strong_suffix)]

    out = pd.DataFrame({
        'beam_id': src['beam_id'].astype(str),
        'latitude': pd.to_numeric(src.get('lat_ph', np.nan), errors='coerce'),
        'longitude': pd.to_numeric(src.get('lon_ph', np.nan), errors='coerce'),
        'photon_height': pd.to_numeric(src.get('h_ph', np.nan), errors='coerce'),
        'quality_ph': pd.to_numeric(src.get('quality_ph', np.nan), errors='coerce'),
        'ref_elevation': pd.to_numeric(src.get('ref_elev', np.nan), errors='coerce'),
        'ref_azimuth': pd.to_numeric(src.get('ref_azimuth', np.nan), errors='coerce'),
        'solar_elevation': pd.to_numeric(src.get('solar_elevation', np.nan), errors='coerce'),
        'background_rate': pd.to_numeric(src.get('bckgrd_rate', np.nan), errors='coerce'),
        'delta_time': pd.to_numeric(src.get('delta_time', np.nan), errors='coerce'),
        'segment_dist': pd.to_numeric(src.get('segment_dist', np.nan), errors='coerce'),
    })

    if 'signal_conf_ph' in src.columns:
        out['photon_conf'] = _normalize_signal_conf(src['signal_conf_ph'])
    else:
        out['photon_conf'] = np.nan

    out = out.dropna(subset=['latitude', 'longitude', 'photon_height']).copy()
    out = _project_to_utm(out)
    out['relative_AT_dist'] = _relative_distance_km_per_beam(out)
    out['is_land_label'] = 0

    return out.drop(columns=['delta_time', 'segment_dist'], errors='ignore')


def fetch_sliderule_atl03(
    region: List[Dict[str, float]],
    t0: str,
    t1: str,
    rgt: Optional[int] = None,
    ph_fields: Optional[List[str]] = None,
    sliderule_url: str = "slideruleearth.io",
    verbose: bool = False,
):
    """
    Fetch ATL03 photons from SlideRule.
    """
    try:
        from sliderule import sliderule, icesat2
    except Exception as e:
        raise ImportError("sliderule package is required for SlideRule ingestion.") from e

    sliderule.init(sliderule_url, verbose=verbose)
    fields = ph_fields or [
        "delta_time", "lat_ph", "lon_ph", "h_ph", "quality_ph", "signal_conf_ph",
        "segment_dist", "ref_elev", "ref_azimuth", "solar_elevation", "bckgrd_rate",
    ]
    params = {"poly": region, "t0": t0, "t1": t1, "atl03_ph_fields": fields}
    if rgt is not None:
        params["rgt"] = int(rgt)
    return icesat2.atl03sp(params)


def fetch_and_prepare_sliderule_dataset(
    region: List[Dict[str, float]],
    t0: str,
    t1: str,
    rgt: Optional[int] = None,
    strong_beams_only: bool = True,
    sliderule_url: str = "slideruleearth.io",
    verbose: bool = False,
) -> pd.DataFrame:
    """
    One-call helper:
    fetch ATL03 photons from SlideRule and convert to framework dataset schema.
    """
    atl03_gdf = fetch_sliderule_atl03(
        region=region,
        t0=t0,
        t1=t1,
        rgt=rgt,
        sliderule_url=sliderule_url,
        verbose=verbose,
    )
    return sliderule_to_framework_dataset(atl03_gdf, strong_beams_only=strong_beams_only)
