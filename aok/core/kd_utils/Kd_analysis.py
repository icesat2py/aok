# utils/Kd_analysis.py
# updated to perform a linear fit in log-space, just like MATLAB's polyfitn(zdepth, y, 1) for a first-order polynomial.

import logging

import numpy as np
import pandas as pd
from scipy.optimize import curve_fit
from sklearn.linear_model import LinearRegression

# def log_model(z, kd, e0):
#     return np.log(e0) - kd * z

## This is wrong because the input is already a bined data,
## it is not necessary to do a histogram again
# def CalculateKdFromFilteredSubsurfacePhoton(df, vertical_res=0.8):
#     if df.empty or 'lat_bins' not in df.columns:
#         return pd.DataFrame({'lat_bins': [np.nan], 'kd': [np.nan], 'e0': [np.nan], 'latitude': [np.nan], 'longitude': [np.nan]})

#     # Get the latitude bin value
#     lat_bin_value = df['lat_bins'].iloc[0] if not df['lat_bins'].empty else np.nan
#     latitude = df['latitude'].mean() if 'latitude' in df.columns else df['lat'].mean() if 'lat' in df.columns else np.nan
#     longitude = df['longitude'].mean() if 'longitude' in df.columns else df['lon'].mean() if 'lon' in df.columns else np.nan

#     # Calculate photon height range
#     photon_height_min = df['photon_height'].min()
#     photon_height_max = df['photon_height'].max()

#     # Check for sufficient data range
#     if np.isnan(photon_height_min) or np.isnan(photon_height_max) or photon_height_min == photon_height_max:
#         return pd.DataFrame({'lat_bins': [lat_bin_value], 'kd': [np.nan], 'e0': [np.nan]})

#     height_bins_range = abs(photon_height_max - photon_height_min)
#     height_bins_number = round(height_bins_range / vertical_res)

#     # Ensure there are enough bins
#     if height_bins_number < 5:
#         return pd.DataFrame({'lat_bins': [lat_bin_value], 'kd': [np.nan], 'e0': [np.nan]})

#     # Create histogram of photon heights
#     bin_edges = np.linspace(photon_height_min, photon_height_max, num=height_bins_number)
#     counts, _ = np.histogram(df['photon_height'], bins=bin_edges)
#     bin_centers = (bin_edges[:-1] + bin_edges[1:]) / 2

#     # Store histogram data
#     hist_df = pd.DataFrame({'zdepth': bin_centers, 'photon_counts': counts})

#     # x value for model
#     # Reverse zdepth to align with the MATLAB approach
#     hist_df['zdepth'] = hist_df['zdepth'].max() - hist_df['zdepth']

#     # Log-transform photon counts, replacing zeros with NaN
#     # y value for model
#     hist_df['log_photon_counts'] = np.log(hist_df['photon_counts'].replace(0, np.nan))
#     hist_df.loc[np.isinf(hist_df['log_photon_counts']), 'log_photon_counts'] = np.nan

#     # Filter out rows with NaNs in either column for regression
#     valid_data = hist_df.dropna(subset=['zdepth', 'log_photon_counts'])

#     # Check for enough valid data points
#     # Skip the regression if there are fewer than 5 datapoints
#     if valid_data['log_photon_counts'].notna().sum() > 3:
#         # Drop NaNs for regression
#         zdepth_valid = valid_data['zdepth'].values.reshape(-1, 1)
#         log_counts_valid = valid_data['log_photon_counts'].values

#         # Perform linear regression
#         model = LinearRegression()
#         model.fit(zdepth_valid, log_counts_valid)

#         # Extract kd as the negative of the slope and e0 from the intercept
#         kd = -model.coef_[0]

#         print('zdepth_valid:',zdepth_valid)
#         print('photon_counts:',hist_df['photon_counts'])
#         print('kd:',kd)

#         e0 = np.exp(model.intercept_)

#         # Set kd to NaN if negative
#         if kd < 0:
#             kd = np.nan
#     else:
#         kd, e0 = np.nan, np.nan

#     return pd.DataFrame({
#         'lat_bins': [lat_bin_value],
#         'kd': [kd],
#         'e0': [e0],
#         'latitude': [latitude],
#         'longitude': [longitude]
#     })


# # one solution is to adjust the vertical_res to 0.25
# def CalculateKdFromFilteredSubsurfacePhoton(df, vertical_res=0.25):
#     if df.empty or 'lat_bins' not in df.columns:
#         return pd.DataFrame({'lat_bins': [np.nan], 'kd': [np.nan], 'e0': [np.nan], 'latitude': [np.nan], 'longitude': [np.nan]})

#     # Get the latitude bin value
#     lat_bin_value = df['lat_bins'].iloc[0] if not df['lat_bins'].empty else np.nan
#     latitude = df['latitude'].mean() if 'latitude' in df.columns else df['lat'].mean() if 'lat' in df.columns else np.nan
#     longitude = df['longitude'].mean() if 'longitude' in df.columns else df['lon'].mean() if 'lon' in df.columns else np.nan

#     # Calculate photon height range
#     photon_height_min = df['photon_height'].min()
#     photon_height_max = df['photon_height'].max()

#     # Check for sufficient data range
#     if np.isnan(photon_height_min) or np.isnan(photon_height_max) or photon_height_min == photon_height_max:
#         return pd.DataFrame({'lat_bins': [lat_bin_value], 'kd': [np.nan], 'e0': [np.nan]})

#     height_bins_range = abs(photon_height_max - photon_height_min)
#     height_bins_number = round(height_bins_range / vertical_res)

#     # Ensure there are enough bins
#     if height_bins_number < 5:
#         return pd.DataFrame({'lat_bins': [lat_bin_value], 'kd': [np.nan], 'e0': [np.nan]})

#     # Create histogram of photon heights
#     bin_edges = np.linspace(photon_height_min, photon_height_max, num=height_bins_number)
#     counts, _ = np.histogram(df['photon_height'], bins=bin_edges)
#     bin_centers = (bin_edges[:-1] + bin_edges[1:]) / 2

#     # Store histogram data
#     hist_df = pd.DataFrame({'zdepth': bin_centers, 'photon_counts': counts})

#     # x value for model
#     # Reverse zdepth to align with the MATLAB approach
#     hist_df['zdepth'] = hist_df['zdepth'].max() - hist_df['zdepth']

#     # Log-transform photon counts, replacing zeros with NaN
#     # y value for model
#     hist_df['log_photon_counts'] = np.log(hist_df['photon_counts'].replace(0, np.nan))
#     hist_df.loc[np.isinf(hist_df['log_photon_counts']), 'log_photon_counts'] = np.nan

#     # Filter out rows with NaNs in either column for regression
#     valid_data = hist_df.dropna(subset=['zdepth', 'log_photon_counts'])

#     # Check for enough valid data points
#     # Skip the regression if there are fewer than 5 datapoints
#     if valid_data['log_photon_counts'].notna().sum() > 3:
#         # Drop NaNs for regression
#         zdepth_valid = valid_data['zdepth'].values.reshape(-1, 1)
#         log_counts_valid = valid_data['log_photon_counts'].values

#         # Perform linear regression
#         model = LinearRegression()
#         model.fit(zdepth_valid, log_counts_valid)

#         # Extract kd as the negative of the slope and e0 from the intercept
#         kd = -model.coef_[0]

#         print('zdepth_valid:',zdepth_valid)
#         print('photon_counts:',hist_df['photon_counts'])
#         print('kd:',kd)

#         e0 = np.exp(model.intercept_)

#         # Set kd to NaN if negative
#         if kd < 0:
#             kd = np.nan
#     else:
#         kd, e0 = np.nan, np.nan

#     return pd.DataFrame({
#         'lat_bins': [lat_bin_value],
#         'kd': [kd],
#         'e0': [e0],
#         'latitude': [latitude],
#         'longitude': [longitude]
#     })


def find_exponential_decay_zone(hist_df, decay_threshold=0.0):
    """
    Identify the depth bins that lie within the exponential decay zone.

    Flowchart step: 16 — Determine depth where signal decays to 1% of incoming
    signal or where photon decay is no longer exponential. Bins with zero photon
    counts (log undefined) are excluded; the remaining contiguous non-zero bins
    define the exponential decay zone.

    Parameters
    ----------
    hist_df : pd.DataFrame
        Columns: 'zdepth' (depth from surface, ascending), 'photon_counts'.
    decay_threshold : float, optional
        Fraction of peak photon count below which bins are excluded.
        0.0 (default) preserves original behaviour (only zero-count bins removed).
        E.g. 0.01 removes bins with < 1% of the peak signal.

    Returns
    -------
    pd.DataFrame
        Filtered rows with a 'log_photon_counts' column added; only bins inside
        the exponential decay zone are kept (photon_counts > 0 and log finite).
    """
    df = hist_df.copy()

    # Apply decay threshold: exclude bins below threshold fraction of peak signal
    if decay_threshold > 0.0:
        peak_count = df["photon_counts"].max()
        if peak_count > 0:
            df.loc[
                df["photon_counts"] < decay_threshold * peak_count, "photon_counts"
            ] = 0

    df["log_photon_counts"] = np.log(df["photon_counts"].replace(0, np.nan))
    df.loc[np.isinf(df["log_photon_counts"]), "log_photon_counts"] = np.nan
    return df.dropna(subset=["zdepth", "log_photon_counts"])


def fit_beers_law(valid_data):
    """
    Fit Beer's Law exponential decay curve to the identified decay zone.

    Flowchart step: 17 — Fit exponential decay curve (Beer's Law) to data
    within the zone of exponential decay. Implemented as linear regression on
    log(photon_counts) vs depth; kd = -slope, e0 = exp(intercept).

    Parameters
    ----------
    valid_data : pd.DataFrame
        Output of find_exponential_decay_zone; columns 'zdepth' and
        'log_photon_counts'.

    Returns
    -------
    tuple[float, float]
        (kd, e0). kd is set to np.nan if negative or if fewer than 4 points.
    """
    if valid_data["log_photon_counts"].notna().sum() <= 3:
        return np.nan, np.nan

    zdepth_valid = valid_data["zdepth"].values.reshape(-1, 1)
    log_counts_valid = valid_data["log_photon_counts"].values

    model = LinearRegression()
    model.fit(zdepth_valid, log_counts_valid)

    kd = -model.coef_[0]
    e0 = np.exp(model.intercept_)

    if kd < 0:
        kd = np.nan
    return kd, e0


# ---------------------------------------------------------------------------
#  Strategy A: Background subtraction + log-linear fit
# ---------------------------------------------------------------------------
def fit_beers_law_bg_subtract(hist_df, bg_fraction=0.2):
    """
    Estimate the noise floor from the deepest bins, subtract it, then fit
    Beer's Law in log-space on the noise-subtracted counts.

    Parameters
    ----------
    hist_df : pd.DataFrame
        Columns: 'zdepth' (ascending from surface), 'photon_counts'.
    bg_fraction : float
        Fraction of the deepest bins used to estimate the background level.

    Returns
    -------
    tuple[float, float, float]
        (kd, e0, noise_floor).
    """
    df = hist_df.copy().sort_values("zdepth")
    n_bins = len(df)
    if n_bins < 5:
        return np.nan, np.nan, np.nan

    # Estimate noise floor from the deepest bg_fraction of bins
    n_bg = max(int(n_bins * bg_fraction), 2)
    noise_floor = float(df.tail(n_bg)["photon_counts"].median())

    # Subtract noise and keep only positive residuals
    df["signal"] = df["photon_counts"] - noise_floor
    df = df[df["signal"] > 0].copy()
    if len(df) < 4:
        return np.nan, np.nan, noise_floor

    df["log_signal"] = np.log(df["signal"])

    zdepth = df["zdepth"].values.reshape(-1, 1)
    log_signal = df["log_signal"].values

    model = LinearRegression()
    model.fit(zdepth, log_signal)

    kd = -model.coef_[0]
    e0 = np.exp(model.intercept_)

    if kd < 0:
        kd = np.nan
    return kd, e0, noise_floor


# ---------------------------------------------------------------------------
#  Strategy B: Breakpoint / segmented regression
# ---------------------------------------------------------------------------
def fit_beers_law_breakpoint(hist_df):
    """
    Find the optimal breakpoint between exponential decay and noise floor,
    then fit Beer's Law only to the decay segment.

    The breakpoint is chosen by testing every candidate position and selecting
    the one that minimises total residual sum of squares of a two-segment
    model: linear slope above the breakpoint, flat constant below.

    Parameters
    ----------
    hist_df : pd.DataFrame
        Columns: 'zdepth' (ascending from surface), 'photon_counts'.

    Returns
    -------
    tuple[float, float, float, float]
        (kd, e0, breakpoint_depth, noise_floor).
    """
    df = hist_df.copy().sort_values("zdepth")
    df = df[df["photon_counts"] > 0].copy()
    if len(df) < 5:
        return np.nan, np.nan, np.nan, np.nan

    df["log_counts"] = np.log(df["photon_counts"])
    depths = df["zdepth"].values
    log_counts = df["log_counts"].values
    n = len(depths)

    best_rss = np.inf
    best_bp_idx = None

    # Try each candidate breakpoint (need >= 4 points in decay segment,
    # >= 1 in noise segment)
    for bp_idx in range(4, n - 1):
        # Decay segment: linear fit on bins 0..bp_idx-1
        z_decay = depths[:bp_idx].reshape(-1, 1)
        lc_decay = log_counts[:bp_idx]
        model = LinearRegression()
        model.fit(z_decay, lc_decay)
        rss_decay = float(np.sum((model.predict(z_decay) - lc_decay) ** 2))

        # Noise segment: flat at the mean of bins bp_idx..end
        lc_noise = log_counts[bp_idx:]
        noise_mean = lc_noise.mean()
        rss_noise = float(np.sum((lc_noise - noise_mean) ** 2))

        total_rss = rss_decay + rss_noise
        if total_rss < best_rss:
            best_rss = total_rss
            best_bp_idx = bp_idx

    if best_bp_idx is None:
        return np.nan, np.nan, np.nan, np.nan

    # Final fit on the decay segment
    z_decay = depths[:best_bp_idx].reshape(-1, 1)
    lc_decay = log_counts[:best_bp_idx]
    model = LinearRegression()
    model.fit(z_decay, lc_decay)

    kd = -model.coef_[0]
    e0 = np.exp(model.intercept_)
    breakpoint_depth = float(depths[best_bp_idx])
    noise_floor = float(np.exp(log_counts[best_bp_idx:].mean()))

    if kd < 0:
        kd = np.nan
    return kd, e0, breakpoint_depth, noise_floor


# ---------------------------------------------------------------------------
#  Strategy C: Nonlinear fit  C(z) = A * exp(-Kd * z) + N
# ---------------------------------------------------------------------------
def _beer_plus_noise(z, A, kd, N):
    """Model: signal = A * exp(-kd * z) + N."""
    return A * np.exp(-kd * z) + N


def fit_beers_law_nonlinear(hist_df):
    """
    Fit the physically correct model C(z) = A·exp(-Kd·z) + N directly
    to raw photon counts using nonlinear least-squares (no log transform).

    Parameters
    ----------
    hist_df : pd.DataFrame
        Columns: 'zdepth' (ascending from surface), 'photon_counts'.

    Returns
    -------
    tuple[float, float, float]
        (kd, e0, noise_floor).
    """
    df = hist_df.copy().sort_values("zdepth")
    depths = df["zdepth"].values
    counts = df["photon_counts"].values.astype(float)

    if len(depths) < 5:
        return np.nan, np.nan, np.nan

    # Initial guesses
    A0 = float(counts.max())
    N0 = float(np.median(counts[len(counts) * 3 // 4 :]))  # deepest 25%
    # Quick log-linear Kd estimate for initial guess (ignore noise)
    pos = counts > 0
    if pos.sum() >= 2:
        log_c = np.log(counts[pos])
        z_pos = depths[pos]
        kd0 = max(float(-(log_c[-1] - log_c[0]) / (z_pos[-1] - z_pos[0] + 1e-9)), 0.01)
    else:
        kd0 = 0.1

    try:
        popt, _ = curve_fit(
            _beer_plus_noise,
            depths,
            counts,
            p0=[A0, kd0, N0],
            bounds=([0, 0, 0], [np.inf, np.inf, np.inf]),
            maxfev=5000,
        )
        A_fit, kd_fit, N_fit = popt
        if kd_fit <= 0:
            kd_fit = np.nan
        return float(kd_fit), float(A_fit), float(N_fit)
    except (RuntimeError, ValueError):
        return np.nan, np.nan, np.nan


# ---------------------------------------------------------------------------
#  Hybrid: Stabilised breakpoint zone detection + log-linear fit on decay only
# ---------------------------------------------------------------------------
def fit_beers_law_hybrid(
    hist_df,
    min_breakpoint_depth=2.0,
    expected_noise_floor=None,
    noise_floor_tolerance=3.0,
):
    """
    Two-stage approach matching the flowchart intent:
      Step 16 — Find where exponential decay transitions to noise floor
                (stabilised breakpoint with BIC selection).
      Step 17 — Fit Beer's Law log-linear ONLY on the decay segment.

    Stabilisation constraints:
      * Minimum breakpoint depth prevents shallow breakpoints that yield
        unstable regression from too few decay bins.
      * Decay segment slope must be negative (Kd > 0).
      * BIC model selection penalises over-fitting, preventing the breakpoint
        from drifting too deep (where the decay segment gets long and noisy).
      * When expected_noise_floor is provided (from beam-level median),
        candidate breakpoints whose noise segment deviates too far from the
        expected value are penalised.
      * Falls back to full log-linear if no valid breakpoint improves BIC
        over a single-line model.

    Parameters
    ----------
    hist_df : pd.DataFrame
        Columns: 'zdepth' (ascending from surface), 'photon_counts'.
    min_breakpoint_depth : float
        Minimum depth (m) below surface for a valid breakpoint.  Prevents
        breakpoints landing in the first few bins where regression is
        unstable.  Default 2.0 m.
    expected_noise_floor : float or None
        If provided, the beam-level median noise floor (photon counts).
        Candidate breakpoints whose noise segment mean deviates by more
        than ``noise_floor_tolerance`` times from the expected value
        receive a BIC penalty.
    noise_floor_tolerance : float
        Factor controlling how far the candidate noise segment mean may
        deviate from ``expected_noise_floor`` before a penalty is applied.
        Default 3.0 (allow 3x variation).

    Returns
    -------
    tuple[float, float, float, float]
        (kd, e0, breakpoint_depth, noise_floor).
        breakpoint_depth and noise_floor are np.nan if fallback to full fit.
    """
    df = hist_df.copy().sort_values("zdepth")
    df = df[df["photon_counts"] > 0].copy()
    n = len(df)
    if n < 6:
        return np.nan, np.nan, np.nan, np.nan

    df["log_counts"] = np.log(df["photon_counts"])
    depths = df["zdepth"].values
    log_counts = df["log_counts"].values

    # ------------------------------------------------------------------
    # Reference: BIC for a single-line model (no breakpoint)
    # ------------------------------------------------------------------
    model_full = LinearRegression()
    model_full.fit(depths.reshape(-1, 1), log_counts)
    rss_full = float(
        np.sum((model_full.predict(depths.reshape(-1, 1)) - log_counts) ** 2)
    )
    k_full = 2  # slope + intercept
    bic_full = n * np.log(rss_full / n + 1e-10) + k_full * np.log(n)

    # ------------------------------------------------------------------
    # Search: best breakpoint using BIC
    # ------------------------------------------------------------------
    best_bic = bic_full  # must beat the single-line model
    best_bp_idx = None
    best_model = None

    for bp_idx in range(4, n - 1):
        # -- Minimum breakpoint depth constraint --
        if depths[bp_idx] < min_breakpoint_depth:
            continue

        # -- Decay segment (surface to breakpoint) --
        z_decay = depths[:bp_idx].reshape(-1, 1)
        lc_decay = log_counts[:bp_idx]
        model = LinearRegression()
        model.fit(z_decay, lc_decay)

        # Physical constraint: slope must be negative
        if model.coef_[0] >= 0:
            continue

        pred_decay = model.predict(z_decay)
        rss_decay = float(np.sum((pred_decay - lc_decay) ** 2))

        # -- Noise segment (breakpoint to bottom) --
        lc_noise = log_counts[bp_idx:]
        noise_mean = float(lc_noise.mean())
        rss_noise = float(np.sum((lc_noise - noise_mean) ** 2))

        # -- BIC for piecewise model (3 params: slope, intercept, noise level)
        rss_total = rss_decay + rss_noise
        k_bp = 3
        bic_bp = n * np.log(rss_total / n + 1e-10) + k_bp * np.log(n)

        # -- Noise floor consistency penalty --
        # When we have a beam-level expected noise floor, penalise
        # candidates whose noise segment deviates substantially.
        if expected_noise_floor is not None and expected_noise_floor > 0:
            candidate_nf = float(np.exp(noise_mean))
            ratio = candidate_nf / expected_noise_floor
            if ratio > noise_floor_tolerance or ratio < 1.0 / noise_floor_tolerance:
                # Add a penalty proportional to log-deviation
                bic_bp += n * abs(np.log(ratio))

        if bic_bp < best_bic:
            best_bic = bic_bp
            best_bp_idx = bp_idx
            best_model = model

    # ------------------------------------------------------------------
    # Result
    # ------------------------------------------------------------------
    if best_bp_idx is None:
        # No breakpoint beats the single-line model — fall back
        kd = -model_full.coef_[0]
        e0 = np.exp(model_full.intercept_)
        if kd < 0:
            kd = np.nan
        return kd, e0, np.nan, np.nan

    kd = -best_model.coef_[0]
    e0 = np.exp(best_model.intercept_)
    breakpoint_depth = float(depths[best_bp_idx])
    noise_floor = float(np.exp(log_counts[best_bp_idx:].mean()))

    if kd < 0:
        kd = np.nan
    return kd, e0, breakpoint_depth, noise_floor


# ---------------------------------------------------------------------------
#  Dispatcher: select fitting strategy by name
# ---------------------------------------------------------------------------
KD_FIT_METHODS = ("log_linear", "bg_subtract", "breakpoint", "nonlinear", "hybrid")


def _fit_kd_with_method(
    hist_df, method="log_linear", decay_threshold=0.0, expected_noise_floor=None
):
    """
    Run the requested fitting strategy on a single histogram.

    Returns
    -------
    tuple[float, float, float]
        (kd, e0, noise_floor).  noise_floor is np.nan for log_linear.
    """
    if method == "log_linear":
        valid = find_exponential_decay_zone(hist_df, decay_threshold=decay_threshold)
        kd, e0 = fit_beers_law(valid)
        return kd, e0, np.nan

    if method == "bg_subtract":
        return fit_beers_law_bg_subtract(hist_df)

    if method == "breakpoint":
        kd, e0, bp, nf = fit_beers_law_breakpoint(hist_df)
        return kd, e0, nf

    if method == "nonlinear":
        return fit_beers_law_nonlinear(hist_df)

    if method == "hybrid":
        kd, e0, bp, nf = fit_beers_law_hybrid(
            hist_df, expected_noise_floor=expected_noise_floor
        )
        return kd, e0, nf

    raise ValueError(f"Unknown kd_fit_method: {method!r}. Choose from {KD_FIT_METHODS}")


# another solution is to calculate kd without hist
def CalculateKdFromFilteredSubsurfacePhoton(
    df,
    vertical_res=0.8,
    decay_zone_threshold=0.0,
    kd_fit_method="log_linear",
    expected_noise_floor=None,
    surface_sigma=None,
    wave_exclusion_multiplier=0.0,
    wave_sigma_calm_threshold=0.1,
):
    """
    Calculate Kd for a single along-track bin by fitting Beer's Law in log-space.

    Orchestrates steps 16 and 17 by calling find_exponential_decay_zone and
    fit_beers_law in sequence.

    Flowchart steps:
      16 — find_exponential_decay_zone: determine depth range of exponential decay.
      17 — fit_beers_law: fit Beer's Law curve; kd = -slope, e0 = exp(intercept).
    """
    # Early exit if DataFrame is empty or missing required column
    if df.empty or "lat_bins" not in df.columns:
        return pd.DataFrame(
            {
                "lat_bins": [np.nan],
                "kd": [np.nan],
                "e0": [np.nan],
                "noise_floor": [np.nan],
                "surface_sigma": [np.nan],
                "latitude": [np.nan],
                "longitude": [np.nan],
            }
        )

    # Retrieve latitude and longitude
    lat_bin_value = df["lat_bins"].iloc[0] if not df["lat_bins"].empty else np.nan
    latitude = (
        df["latitude"].mean()
        if "latitude" in df.columns
        else df["lat"].mean()
        if "lat" in df.columns
        else np.nan
    )
    longitude = (
        df["longitude"].mean()
        if "longitude" in df.columns
        else df["lon"].mean()
        if "lon" in df.columns
        else np.nan
    )

    # Use value_counts to get photon counts in each height bin
    height_counts = df["height_bins"].value_counts().sort_index()
    bin_centers = height_counts.index.astype(float)

    # Create a DataFrame for the height bins and counts
    hist_df = pd.DataFrame(
        {"zdepth": bin_centers, "photon_counts": height_counts.values}
    )

    # Reverse zdepth for model alignment
    hist_df["zdepth"] = hist_df["zdepth"].max() - hist_df["zdepth"]

    # Wave-adaptive fit: skip shallow bins contaminated by wave smearing/bubbles.
    # zdepth=0 in the histogram corresponds to the adaptive surface detection
    # threshold: max(3*sigma, 1.0 m) below the Gaussian surface peak
    # (set by get_sea_surface_height_adaptive).  The wave-adaptive trim adds
    # an additional margin of (k - 3)*sigma beyond the 3-sigma cutoff to
    # cover bubble injection beneath wave troughs and compensate for sigma
    # underestimation from the truncated ±1 m Gaussian fit window.
    if surface_sigma is not None and wave_exclusion_multiplier > 0:
        if not np.isnan(surface_sigma) and surface_sigma > wave_sigma_calm_threshold:
            adaptive_offset = max(3.0 * surface_sigma, 1.0)
            wave_skip = max(
                0.0, wave_exclusion_multiplier * surface_sigma - adaptive_offset
            )
            trimmed = hist_df[hist_df["zdepth"] >= wave_skip]
            if len(trimmed) >= 4:
                logging.info(
                    "Wave-adaptive trim: sigma=%.3f, adaptive_offset=%.2f m, "
                    "skip=%.2f m, %d->%d bins",
                    surface_sigma,
                    adaptive_offset,
                    wave_skip,
                    len(hist_df),
                    len(trimmed),
                )
                hist_df = trimmed
            # else: keep original hist_df (too few bins after trim)

    kd, e0, noise_floor = _fit_kd_with_method(
        hist_df,
        method=kd_fit_method,
        decay_threshold=decay_zone_threshold,
        expected_noise_floor=expected_noise_floor,
    )

    return pd.DataFrame(
        {
            "lat_bins": [lat_bin_value],
            "kd": [kd],
            "e0": [e0],
            "noise_floor": [noise_floor],
            "surface_sigma": [surface_sigma if surface_sigma is not None else np.nan],
            "latitude": [latitude],
            "longitude": [longitude],
        }
    )


# Original kd calculation function remains unchanged
def calculate_kd(
    filtered_seafloor_subsurface_photon_dataset,
    decay_zone_threshold=0.0,
    kd_fit_method="log_linear",
    wave_exclusion_multiplier=0.0,
    wave_sigma_calm_threshold=0.1,
):
    """
    Loop over along-track bins and call CalculateKdFromFilteredSubsurfacePhoton
    for each bin.

    For the 'hybrid' method, a two-pass approach is used:
      Pass 1 — Fit each bin independently to estimate per-bin noise floors.
      Pass 2 — Compute the beam-level median noise floor, then re-fit each
               bin with the expected noise floor as a stabilisation constraint.

    After fitting, IQR-based outlier filtering removes extreme Kd values
    (for hybrid method only).

    Flowchart steps:
      16 — Determine depth of exponential decay zone (per bin, inside
           CalculateKdFromFilteredSubsurfacePhoton).
      17 — Fit Beer's Law exponential decay curve (per bin).
      18 — Save K_dph attenuation coefficient value and statistical terms
           (kd, e0 columns in the returned DataFrame).
    """
    logging.info(
        "Calculating Kd from filtered subsurface photon dataset (method=%s)",
        kd_fit_method,
    )

    empty_df = pd.DataFrame(
        {
            "lat_bins": [],
            "kd": [],
            "e0": [],
            "noise_floor": [],
            "surface_sigma": [],
            "latitude": [],
            "longitude": [],
        }
    )

    groups = list(
        filtered_seafloor_subsurface_photon_dataset.groupby("lat_bins", observed=False)
    )
    if not groups:
        return empty_df

    if kd_fit_method == "hybrid":
        # ------------------------------------------------------------------
        # Pass 1: estimate per-bin noise floors (no expected_noise_floor)
        # ------------------------------------------------------------------
        logging.info("Hybrid pass 1: estimating per-bin noise floors")
        pass1_results = []
        for _, group in groups:
            sigma = (
                float(group["surface_sigma"].iloc[0])
                if ("surface_sigma" in group.columns and len(group) > 0)
                else None
            )
            pass1_results.append(
                CalculateKdFromFilteredSubsurfacePhoton(
                    group,
                    decay_zone_threshold=decay_zone_threshold,
                    kd_fit_method=kd_fit_method,
                    surface_sigma=sigma,
                    wave_exclusion_multiplier=wave_exclusion_multiplier,
                    wave_sigma_calm_threshold=wave_sigma_calm_threshold,
                )
            )
        if not pass1_results:
            return empty_df
        pass1_df = pd.concat(pass1_results, ignore_index=True)

        # ------------------------------------------------------------------
        # Compute sliding-window noise floor for pass 2
        # ------------------------------------------------------------------
        # 10 km window = ±10 bins at 500 m resolution (20 bins total).
        # Each bin's expected noise floor = median of valid noise floors
        # within ±half_window bins.  Falls back to beam-level median when
        # the local window has < 3 valid estimates.
        HALF_WINDOW = 10  # ±10 bins = ±5 km at 500 m horizontal_res
        MIN_LOCAL = 3  # minimum valid noise floors to use local median

        nf_array = pass1_df["noise_floor"].values.copy()
        n_bins = len(nf_array)

        # Beam-level fallback
        valid_nf_all = pass1_df["noise_floor"].dropna()
        valid_nf_all = valid_nf_all[valid_nf_all > 0]
        beam_median_nf = (
            float(valid_nf_all.median()) if len(valid_nf_all) >= MIN_LOCAL else None
        )

        if beam_median_nf is not None:
            # Build per-bin expected noise floor via sliding window
            expected_nf_per_bin = np.full(n_bins, np.nan)
            for i in range(n_bins):
                lo = max(0, i - HALF_WINDOW)
                hi = min(n_bins, i + HALF_WINDOW + 1)
                window_nf = nf_array[lo:hi]
                valid = window_nf[~np.isnan(window_nf) & (window_nf > 0)]
                if len(valid) >= MIN_LOCAL:
                    expected_nf_per_bin[i] = float(np.median(valid))
                else:
                    expected_nf_per_bin[i] = beam_median_nf  # fallback

            logging.info(
                "Hybrid pass 2: sliding window noise floor "
                "(half_window=%d bins, beam_median=%.3f, "
                "local range=%.3f-%.3f)",
                HALF_WINDOW,
                beam_median_nf,
                float(np.nanmin(expected_nf_per_bin)),
                float(np.nanmax(expected_nf_per_bin)),
            )
        else:
            expected_nf_per_bin = None
            logging.info(
                "Hybrid: insufficient noise floor estimates (%d), skipping pass 2",
                len(valid_nf_all),
            )

        # ------------------------------------------------------------------
        # Pass 2: re-fit with per-bin expected noise floor constraint
        # ------------------------------------------------------------------
        if expected_nf_per_bin is not None:
            results = []
            for idx, (_, group) in enumerate(groups):
                sigma = (
                    float(group["surface_sigma"].iloc[0])
                    if ("surface_sigma" in group.columns and len(group) > 0)
                    else None
                )
                results.append(
                    CalculateKdFromFilteredSubsurfacePhoton(
                        group,
                        decay_zone_threshold=decay_zone_threshold,
                        kd_fit_method=kd_fit_method,
                        expected_noise_floor=float(expected_nf_per_bin[idx]),
                        surface_sigma=sigma,
                        wave_exclusion_multiplier=wave_exclusion_multiplier,
                        wave_sigma_calm_threshold=wave_sigma_calm_threshold,
                    )
                )
            SubsurfacePhotonDFAddedKd = pd.concat(results, ignore_index=True)
        else:
            SubsurfacePhotonDFAddedKd = pass1_df

        # ------------------------------------------------------------------
        # IQR-based outlier filtering (hybrid only)
        # Uses 3×IQR to accommodate real spatial variation (e.g. turbidity
        # gradients near river mouths) while removing fitting artefacts.
        # ------------------------------------------------------------------
        kd_vals = SubsurfacePhotonDFAddedKd["kd"].dropna()
        if len(kd_vals) >= 5:
            q1 = float(kd_vals.quantile(0.25))
            q3 = float(kd_vals.quantile(0.75))
            iqr = q3 - q1
            lower = q1 - 3.0 * iqr
            upper = q3 + 3.0 * iqr
            # Also apply physical cap: Kd > 5.0 m⁻¹ is unrealistic
            upper = min(upper, 5.0)
            outlier_mask = (SubsurfacePhotonDFAddedKd["kd"] < lower) | (
                SubsurfacePhotonDFAddedKd["kd"] > upper
            )
            n_outliers = int(outlier_mask.sum())
            if n_outliers > 0:
                logging.info(
                    "Hybrid IQR filter: removed %d outliers (bounds: [%.4f, %.4f])",
                    n_outliers,
                    lower,
                    upper,
                )
                SubsurfacePhotonDFAddedKd.loc[outlier_mask, "kd"] = np.nan

    else:
        # ------------------------------------------------------------------
        # Non-hybrid methods: single pass, no IQR filtering
        # ------------------------------------------------------------------
        results = []
        for _, group in groups:
            sigma = (
                float(group["surface_sigma"].iloc[0])
                if ("surface_sigma" in group.columns and len(group) > 0)
                else None
            )
            results.append(
                CalculateKdFromFilteredSubsurfacePhoton(
                    group,
                    decay_zone_threshold=decay_zone_threshold,
                    kd_fit_method=kd_fit_method,
                    surface_sigma=sigma,
                    wave_exclusion_multiplier=wave_exclusion_multiplier,
                    wave_sigma_calm_threshold=wave_sigma_calm_threshold,
                )
            )
        if not results:
            return empty_df
        SubsurfacePhotonDFAddedKd = pd.concat(results, ignore_index=True)

    return SubsurfacePhotonDFAddedKd


# Updated function to apply kd calculation beam-by-beam
def process_kd_calculation(
    Final_filtered_subsurface_photon_dataset,
    decay_zone_threshold=0.0,
    kd_fit_method="log_linear",
    wave_exclusion_multiplier=0.0,
    wave_sigma_calm_threshold=0.1,
):
    """
    Beam-by-beam wrapper that calls calculate_kd for every beam and concatenates
    the results into a single Kd output DataFrame.

    Flowchart steps:
      16 — Determine depth of exponential decay zone (delegated to
           CalculateKdFromFilteredSubsurfacePhoton).
      17 — Fit Beer's Law exponential decay curve (delegated).
      18 — Save K_dph attenuation coefficient value (slope of the Beer's Law
           curve) and statistical terms (kd, e0) — the returned DataFrame is
           written to CSV by run_pipeline.
    """
    # Initialize list to store results for each beam
    kd_beam_datasets = []

    # Group by 'beam_id' to process each beam independently
    for beam_id, beam_data in Final_filtered_subsurface_photon_dataset.groupby(
        "beam_id"
    ):
        logging.info(f"Calculating Kd for beam: {beam_id}")

        # Apply the calculate_kd function to the current beam's dataset
        SubsurfacePhotonDFAddedKd = calculate_kd(
            beam_data,
            decay_zone_threshold=decay_zone_threshold,
            kd_fit_method=kd_fit_method,
            wave_exclusion_multiplier=wave_exclusion_multiplier,
            wave_sigma_calm_threshold=wave_sigma_calm_threshold,
        )

        # Add a column to track the beam_id in the results
        SubsurfacePhotonDFAddedKd["beam_id"] = beam_id

        # Append the result to the list
        kd_beam_datasets.append(SubsurfacePhotonDFAddedKd)

    if not kd_beam_datasets:
        logging.warning(
            "process_kd_calculation: no beam data remained after filtering. "
            "All bins may have been discarded by an upstream filter (e.g. histogram quality). "
            "Returning empty DataFrame."
        )
        return pd.DataFrame(
            columns=[
                "lat_bins",
                "kd",
                "e0",
                "noise_floor",
                "surface_sigma",
                "latitude",
                "longitude",
                "beam_id",
            ]
        )

    # Combine results from all beams into a single DataFrame
    combined_kd_dataset = pd.concat(kd_beam_datasets, ignore_index=True)

    return combined_kd_dataset
