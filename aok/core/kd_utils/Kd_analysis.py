# utils/Kd_analysis.py
# updated to perform a linear fit in log-space, just like MATLAB's polyfitn(zdepth, y, 1) for a first-order polynomial.

import logging
import warnings

import numpy as np
import pandas as pd
from scipy.optimize import curve_fit
from sklearn.linear_model import LinearRegression

# Suppress np.polyfit RankWarning once at module scope; BMA/hybrid hot path
# fires ~1.6M polyfit calls per granule, so per-call warning overhead would
# dominate. Pathological inputs (zero z-variance) are guarded upstream by
# MIN_DEPTH_BINS_FOR_FIT and min_total_range_m gates.
warnings.filterwarnings("ignore", message=".*Polyfit may be poorly conditioned.*")

MIN_DEPTH_BINS_FOR_FIT = 6  # hybrid fitter requires at least this many non-zero bins


def compute_physics_noise_floor(df, horizontal_res, iss_velocity, vertical_res=0.25):
    """Compute expected noise floor per horizontal bin from ATL03 bckgrd_rate.

    Background photons are distributed uniformly across the detector's
    altimetric range window (bckgrd_int_height from ATL03).  The expected
    noise per depth bin is:

        expected_nf = median(bckgrd_rate) * dwell_time * (vertical_res / median(bckgrd_int_height))

    This is a diagnostic/validation value — not used as a fitter constraint.

    Parameters
    ----------
    df : pd.DataFrame
        Subsurface photon dataset with 'lat_bins', 'background_rate',
        and 'bckgrd_int_height'.
    horizontal_res : float
        Horizontal bin size in meters (e.g. 500).
    iss_velocity : float
        ISS ground velocity in m/s (e.g. 7000).
    vertical_res : float
        Depth bin height in meters (default 0.25).

    Returns
    -------
    pd.Series
        Indexed by lat_bins, values are expected noise floor (photon counts
        per depth bin). NaN for bins with missing data.
    """
    if "background_rate" not in df.columns or "bckgrd_int_height" not in df.columns:
        return pd.Series(dtype=float)

    dwell_time = horizontal_res / iss_velocity

    grouped = df.groupby("lat_bins", observed=False)
    median_bg = grouped["background_rate"].median()
    median_int_height = grouped["bckgrd_int_height"].median()

    expected_nf = median_bg * dwell_time * (vertical_res / median_int_height)

    return expected_nf


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
def fit_beers_law_breakpoint(
    hist_df,
    min_breakpoint_depth=2.0,
    min_decay_range_m=5.0,
    min_decay_photons=30,
    min_decay_bins=8,
    min_total_photons=30,
    min_total_range_m=5.0,
):
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
    min_breakpoint_depth : float
        Minimum depth (m) below surface for a valid breakpoint. Default 2.0 m.
    min_decay_range_m : float
        Minimum span (m) covered by the decay segment. Prevents short noisy
        decay fits in low-signal bins. Default 5.0 m.
    min_decay_photons : int
        Minimum number of photons that must lie within the decay segment.
        Default 30.
    min_decay_bins : int
        Minimum number of non-empty histogram bins in the decay segment.
        Default 8.
    min_total_photons : int
        Minimum total photons in the bin for the fit to be attempted at all.
        Default 30.
    min_total_range_m : float
        Minimum total histogram span (m) for the fit to be attempted at all.
        Default 5.0 m.

    Returns
    -------
    tuple[float, float, float, float, str or None]
        (kd, e0, breakpoint_depth, noise_floor, failure_reason).
        failure_reason is None on success, otherwise a short string
        explaining why Kd is NaN (e.g. 'too_few_bins', 'insufficient_photons').
    """
    df = hist_df.copy().sort_values("zdepth")
    df = df[df["photon_counts"] > 0].copy()
    if len(df) < 5:
        return np.nan, np.nan, np.nan, np.nan, "too_few_bins"

    # NEW: reject the entire bin if insufficient data for any meaningful fit.
    total_photons = int(df["photon_counts"].sum())
    total_range = df["zdepth"].max() - df["zdepth"].min()
    if total_photons < min_total_photons:
        return np.nan, np.nan, np.nan, np.nan, "insufficient_photons"
    if total_range < min_total_range_m:
        return np.nan, np.nan, np.nan, np.nan, "insufficient_range"

    df["log_counts"] = np.log(df["photon_counts"])
    depths = df["zdepth"].values
    log_counts = df["log_counts"].values
    counts = df["photon_counts"].values
    n = len(depths)

    best_rss = np.inf
    best_bp_idx = None

    # Try each candidate breakpoint (need >= min_decay_bins in decay segment,
    # >= 1 in noise segment)
    for bp_idx in range(max(4, min_decay_bins), n - 1):
        if depths[bp_idx] < min_breakpoint_depth:
            continue

        # NEW: decay zone must span at least min_decay_range_m meters
        decay_range = depths[bp_idx - 1] - depths[0]
        if decay_range < min_decay_range_m:
            continue

        # NEW: decay zone must contain at least min_decay_photons photons
        decay_photons = int(counts[:bp_idx].sum())
        if decay_photons < min_decay_photons:
            continue

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
        return np.nan, np.nan, np.nan, np.nan, "no_breakpoint_found"

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
        return np.nan, np.nan, np.nan, np.nan, "negative_slope"
    return kd, e0, breakpoint_depth, noise_floor, None


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

    Two-stage approach for robust convergence:
      Stage 1: Run bg_subtract to get reliable (Kd, A, N) estimates.
               The log-linear fit on noise-subtracted counts gives a good
               Kd, and the noise floor from deep bins gives N.
      Stage 2: Use Stage 1 results as initial guesses for the nonlinear fit,
               with N constrained to [0, 3 * N_stage1].  This refines the
               physically correct model starting from a good solution.

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

    # Stage 1: bg_subtract for Kd and N estimates
    kd_init, _, N_init = fit_beers_law_bg_subtract(hist_df)

    if np.isnan(N_init) or N_init < 0:
        N_init = float(np.median(counts[len(counts) * 3 // 4 :]))
    if np.isnan(kd_init) or kd_init <= 0:
        kd_init = 0.1

    # A0 from actual data: surface count minus noise, extrapolated to z=0
    # A = (counts[0] - N) / exp(-Kd * z[0])
    A_init = max(float(counts[0] - N_init), 1.0) / max(
        np.exp(-kd_init * depths[0]), 1e-6
    )

    N_upper = max(N_init * 3.0, 1.0)

    # Stage 2: nonlinear refinement
    try:
        popt, _ = curve_fit(
            _beer_plus_noise,
            depths,
            counts,
            p0=[A_init, kd_init, N_init],
            bounds=([0, 0.001, 0], [np.inf, np.inf, N_upper]),
            maxfev=5000,
        )
        A_fit, kd_fit, N_fit = popt
        if kd_fit <= 0:
            kd_fit = np.nan
        return float(kd_fit), float(A_fit), float(N_fit)
    except (RuntimeError, ValueError):
        # If nonlinear fails, return bg_subtract result
        return kd_init, A_init, N_init


# ---------------------------------------------------------------------------
#  Hybrid: Stabilised breakpoint zone detection + log-linear fit on decay only
# ---------------------------------------------------------------------------
def fit_beers_law_hybrid(
    hist_df,
    min_breakpoint_depth=2.0,
    expected_noise_floor=None,
    noise_floor_tolerance=3.0,
    min_decay_range_m=5.0,
    min_decay_photons=30,
    min_decay_bins=8,
    min_total_photons=30,
    min_total_range_m=5.0,
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
      * NEW: whole-bin rejection when insufficient total photons or total
        range exist to support any meaningful fit.
      * NEW: decay-zone constraints (minimum range, minimum photons, minimum
        non-empty bins) prevent spurious high-Kd fits in low-signal bins.

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
    min_decay_range_m : float
        Minimum span (m) that the decay segment must cover. Prevents
        short decay fits dominated by noise. Default 5.0 m.
    min_decay_photons : int
        Minimum number of photons that must lie within the decay segment.
        Default 30.
    min_decay_bins : int
        Minimum number of non-empty histogram bins in the decay segment.
        Default 8.
    min_total_photons : int
        Minimum total photons in the bin for the fit to be attempted at all.
        Bins with fewer photons are rejected outright. Default 30.
    min_total_range_m : float
        Minimum total histogram span (m) for the fit to be attempted at all.
        Bins with a narrower span are rejected outright. Default 5.0 m.

    Returns
    -------
    tuple[float, float, float, float, str or None]
        (kd, e0, breakpoint_depth, noise_floor, failure_reason).
        breakpoint_depth and noise_floor are np.nan if fallback to full fit.
        failure_reason is None on success, otherwise a short string
        explaining why Kd is NaN or the fit fell back
        (e.g. 'too_few_bins', 'insufficient_photons',
        'no_breakpoint_fallback', 'no_breakpoint_found').
    """
    df = hist_df.copy().sort_values("zdepth")
    df = df[df["photon_counts"] > 0].copy()
    n = len(df)
    if n < 6:
        return np.nan, np.nan, np.nan, np.nan, "too_few_bins"

    # NEW: Reject the entire bin if insufficient data for any meaningful fit.
    # Returns (nan, nan, nan, nan, reason_string) — reason is used by quality
    # flag system to explain why Kd is NaN.
    total_photons = int(df["photon_counts"].sum())
    total_range = df["zdepth"].max() - df["zdepth"].min()
    if total_photons < min_total_photons:
        return np.nan, np.nan, np.nan, np.nan, "insufficient_photons"
    if total_range < min_total_range_m:
        return np.nan, np.nan, np.nan, np.nan, "insufficient_range"

    df["log_counts"] = np.log(df["photon_counts"])
    depths = df["zdepth"].values
    log_counts = df["log_counts"].values
    counts = df["photon_counts"].values

    # ------------------------------------------------------------------
    # Reference: BIC for a single-line model (no breakpoint)
    # ------------------------------------------------------------------
    slope_full, intercept_full = np.polyfit(depths, log_counts, 1)
    pred_full = slope_full * depths + intercept_full
    rss_full = float(np.sum((pred_full - log_counts) ** 2))
    k_full = 2  # slope + intercept
    bic_full = n * np.log(rss_full / n + 1e-10) + k_full * np.log(n)

    # ------------------------------------------------------------------
    # Search: best breakpoint using BIC
    # ------------------------------------------------------------------
    best_bic = bic_full  # must beat the single-line model
    best_bp_idx = None
    best_slope = None
    best_intercept = None

    for bp_idx in range(max(4, min_decay_bins), n - 1):
        # -- Minimum breakpoint depth constraint --
        if depths[bp_idx] < min_breakpoint_depth:
            continue

        # NEW: decay zone must span at least min_decay_range_m meters
        decay_range = depths[bp_idx - 1] - depths[0]
        if decay_range < min_decay_range_m:
            continue

        # NEW: decay zone must contain at least min_decay_photons photons
        decay_photons = int(counts[:bp_idx].sum())
        if decay_photons < min_decay_photons:
            continue

        # -- Decay segment (surface to breakpoint) --
        z_decay = depths[:bp_idx]
        lc_decay = log_counts[:bp_idx]
        slope, intercept = np.polyfit(z_decay, lc_decay, 1)

        # Physical constraint: slope must be negative
        if slope >= 0:
            continue

        pred_decay = slope * z_decay + intercept
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
            best_slope = slope
            best_intercept = intercept

    # ------------------------------------------------------------------
    # Result
    # ------------------------------------------------------------------
    if best_bp_idx is None:
        # No breakpoint beats the single-line model — fall back
        kd = -slope_full
        e0 = np.exp(intercept_full)
        if kd < 0:
            # Full fit also produces a non-physical slope; fitter cannot
            # recover a Kd estimate from this bin.
            return np.nan, np.nan, np.nan, np.nan, "no_breakpoint_found"
        return kd, e0, np.nan, np.nan, "no_breakpoint_fallback"

    kd = -best_slope
    e0 = np.exp(best_intercept)
    breakpoint_depth = float(depths[best_bp_idx])
    noise_floor = float(np.exp(log_counts[best_bp_idx:].mean()))

    if kd < 0:
        return np.nan, np.nan, np.nan, np.nan, "no_breakpoint_found"
    return kd, e0, breakpoint_depth, noise_floor, None


def fit_beers_law_bma(
    hist_df,
    min_breakpoint_depth=2.0,
    expected_noise_floor=None,
    noise_floor_tolerance=3.0,
    min_decay_range_m=5.0,
    min_decay_photons=30,
    min_decay_bins=8,
    min_total_photons=30,
    min_total_range_m=5.0,
):
    """
    Bayesian Model-Averaged Kd: weighted average across all candidate breakpoints.

    Instead of picking the single best BIC breakpoint (which is unstable),
    compute Kd for every candidate and weight by BIC probability:
        w_i = exp(-0.5 * (BIC_i - BIC_min))
        kd = sum(w_i * kd_i) / sum(w_i)

    When BIC is confident (one clear winner), gives same result as hybrid.
    When BIC is ambiguous, gives a smoothed, more stable Kd.

    Parameters
    ----------
    hist_df : pd.DataFrame
        Columns: 'zdepth' (ascending from surface), 'photon_counts'.
    min_breakpoint_depth : float
        Minimum depth (m) below surface for a valid breakpoint. Default 2.0 m.
    expected_noise_floor : float or None
        If provided, the beam-level median noise floor (photon counts).
        Candidate breakpoints whose noise segment mean deviates by more
        than ``noise_floor_tolerance`` times from the expected value
        receive a BIC penalty.
    noise_floor_tolerance : float
        Factor controlling how far the candidate noise segment mean may
        deviate from ``expected_noise_floor`` before a penalty is applied.
        Default 3.0.
    min_decay_range_m : float
        Minimum span (m) that the decay segment must cover. Default 5.0 m.
    min_decay_photons : int
        Minimum number of photons in the decay segment. Default 30.
    min_decay_bins : int
        Minimum number of non-empty histogram bins in the decay segment.
        Default 8.
    min_total_photons : int
        Minimum total photons for the fit to be attempted. Default 30.
    min_total_range_m : float
        Minimum total histogram span (m) for the fit to be attempted. Default 5.0.

    Returns
    -------
    tuple[float, float, float, float, str or None]
        (kd, e0, breakpoint_avg, noise_floor_avg, failure_reason).
        Same signature as fit_beers_law_hybrid for drop-in replacement.
    """
    df = hist_df.copy().sort_values("zdepth")
    df = df[df["photon_counts"] > 0].copy()
    n = len(df)
    if n < MIN_DEPTH_BINS_FOR_FIT:
        return np.nan, np.nan, np.nan, np.nan, "too_few_bins"

    # Whole-bin rejection: insufficient data for any meaningful fit.
    total_photons = int(df["photon_counts"].sum())
    total_range = df["zdepth"].max() - df["zdepth"].min()
    if total_photons < min_total_photons:
        return np.nan, np.nan, np.nan, np.nan, "insufficient_photons"
    if total_range < min_total_range_m:
        return np.nan, np.nan, np.nan, np.nan, "insufficient_range"

    df["log_counts"] = np.log(df["photon_counts"])
    depths = df["zdepth"].values
    log_counts = df["log_counts"].values
    counts = df["photon_counts"].values

    # ------------------------------------------------------------------
    # Full single-line model (no breakpoint) as baseline candidate
    # ------------------------------------------------------------------
    slope_full, intercept_full = np.polyfit(depths, log_counts, 1)
    pred_full = slope_full * depths + intercept_full
    rss_full = float(np.sum((pred_full - log_counts) ** 2))
    k_full = 2  # slope + intercept
    bic_full = n * np.log(rss_full / n + 1e-10) + k_full * np.log(n)
    kd_full = -slope_full
    e0_full = np.exp(intercept_full)

    candidates = []

    # Include the full-line model as a candidate (no breakpoint)
    if kd_full > 0:
        candidates.append(
            {
                "bic": bic_full,
                "kd": kd_full,
                "e0": e0_full,
                "bp": np.nan,
                "nf": np.nan,
            }
        )

    # ------------------------------------------------------------------
    # Breakpoint candidates: same search as hybrid
    # ------------------------------------------------------------------
    for bp_idx in range(max(4, min_decay_bins), n - 1):
        if depths[bp_idx] < min_breakpoint_depth:
            continue

        # Decay zone must span at least min_decay_range_m meters
        decay_range = depths[bp_idx - 1] - depths[0]
        if decay_range < min_decay_range_m:
            continue

        # Decay zone must contain at least min_decay_photons photons
        decay_photons = int(counts[:bp_idx].sum())
        if decay_photons < min_decay_photons:
            continue

        # Fit linear decay on surface-to-breakpoint segment
        z_decay = depths[:bp_idx]
        lc_decay = log_counts[:bp_idx]
        slope, intercept = np.polyfit(z_decay, lc_decay, 1)

        # Physical constraint: slope must be negative (Kd > 0)
        if slope >= 0:
            continue

        pred_decay = slope * z_decay + intercept
        rss_decay = float(np.sum((pred_decay - lc_decay) ** 2))

        # Noise segment (breakpoint to bottom)
        lc_noise = log_counts[bp_idx:]
        noise_mean = float(lc_noise.mean())
        rss_noise = float(np.sum((lc_noise - noise_mean) ** 2))

        # BIC for piecewise model (3 params: slope, intercept, noise level)
        rss_total = rss_decay + rss_noise
        k_bp = 3
        bic_bp = n * np.log(rss_total / n + 1e-10) + k_bp * np.log(n)

        # Noise floor consistency penalty (same as hybrid)
        if expected_noise_floor is not None and expected_noise_floor > 0:
            candidate_nf = float(np.exp(noise_mean))
            ratio = candidate_nf / expected_noise_floor
            if ratio > noise_floor_tolerance or ratio < 1.0 / noise_floor_tolerance:
                bic_bp += n * abs(np.log(ratio))

        candidates.append(
            {
                "bic": bic_bp,
                "kd": -slope,
                "e0": np.exp(intercept),
                "bp": float(depths[bp_idx]),
                "nf": float(np.exp(noise_mean)),
            }
        )

    if not candidates:
        return np.nan, np.nan, np.nan, np.nan, "no_valid_candidates"

    # ------------------------------------------------------------------
    # BIC weights: w_i = exp(-0.5 * (BIC_i - BIC_min)), normalised
    # ------------------------------------------------------------------
    cdf = pd.DataFrame(candidates)
    bic_min = cdf["bic"].min()
    cdf["weight"] = np.exp(-0.5 * (cdf["bic"] - bic_min))
    cdf["weight"] /= cdf["weight"].sum()

    kd_avg = float((cdf["weight"] * cdf["kd"]).sum())
    e0_avg = float((cdf["weight"] * cdf["e0"]).sum())

    # Weighted average breakpoint (excluding NaN for full-line model)
    bp_valid = cdf.dropna(subset=["bp"])
    if len(bp_valid) > 0 and bp_valid["weight"].sum() > 0.01:
        bp_avg = float(
            (bp_valid["weight"] * bp_valid["bp"]).sum() / bp_valid["weight"].sum()
        )
        nf_avg = float(
            (bp_valid["weight"] * bp_valid["nf"]).sum() / bp_valid["weight"].sum()
        )
    else:
        bp_avg = np.nan
        nf_avg = np.nan

    if kd_avg <= 0:
        return np.nan, np.nan, np.nan, np.nan, "negative_kd"

    return kd_avg, e0_avg, bp_avg, nf_avg, None


# ---------------------------------------------------------------------------
#  Dispatcher: select fitting strategy by name
# ---------------------------------------------------------------------------
KD_FIT_METHODS = (
    "log_linear",
    "bg_subtract",
    "breakpoint",
    "nonlinear",
    "hybrid",
    "bma",
)


def _fit_kd_with_method(
    hist_df,
    method="log_linear",
    decay_threshold=0.0,
    expected_noise_floor=None,
    **kwargs,
):
    """
    Run the requested fitting strategy on a single histogram.

    Extra keyword arguments are forwarded to the underlying fitter (e.g.
    ``min_decay_range_m``, ``min_decay_photons``, ``min_total_photons``,
    ``min_total_range_m`` for the hybrid and breakpoint methods).

    Returns
    -------
    tuple[float, float, float, str or None]
        (kd, e0, noise_floor, failure_reason).  noise_floor is np.nan for
        log_linear.  failure_reason is None for methods that do not report
        one (log_linear, bg_subtract, nonlinear).
    """
    if method == "log_linear":
        valid = find_exponential_decay_zone(hist_df, decay_threshold=decay_threshold)
        kd, e0 = fit_beers_law(valid)
        return kd, e0, np.nan, None

    if method == "bg_subtract":
        kd, e0, nf = fit_beers_law_bg_subtract(hist_df)
        return kd, e0, nf, None

    if method == "breakpoint":
        kd, e0, _, nf, reason = fit_beers_law_breakpoint(hist_df, **kwargs)
        return kd, e0, nf, reason

    if method == "nonlinear":
        kd, e0, nf = fit_beers_law_nonlinear(hist_df)
        return kd, e0, nf, None

    if method == "hybrid":
        kd, e0, _, nf, reason = fit_beers_law_hybrid(
            hist_df, expected_noise_floor=expected_noise_floor, **kwargs
        )
        return kd, e0, nf, reason

    if method == "bma":
        kd, e0, _, nf, reason = fit_beers_law_bma(
            hist_df, expected_noise_floor=expected_noise_floor, **kwargs
        )
        return kd, e0, nf, reason

    raise ValueError(
        f"Unknown kd_fit_method: {method!r}. " f"Choose from {KD_FIT_METHODS}"
    )


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
    **fit_kwargs,
):
    """
    Calculate Kd for a single along-track bin by fitting Beer's Law in log-space.

    Orchestrates steps 16 and 17 by calling find_exponential_decay_zone and
    fit_beers_law in sequence.

    Extra keyword arguments in ``fit_kwargs`` are forwarded to the underlying
    fitter (hybrid/breakpoint constraint parameters such as
    ``min_decay_range_m``, ``min_decay_photons``, ``min_decay_bins``,
    ``min_total_photons``, ``min_total_range_m``).

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
                "fit_failure_reason": [None],
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

    kd, e0, noise_floor, fit_failure_reason = _fit_kd_with_method(
        hist_df,
        method=kd_fit_method,
        decay_threshold=decay_zone_threshold,
        expected_noise_floor=expected_noise_floor,
        **fit_kwargs,
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
            "fit_failure_reason": [fit_failure_reason],
        }
    )


# Original kd calculation function remains unchanged
def calculate_kd(
    filtered_seafloor_subsurface_photon_dataset,
    decay_zone_threshold=0.0,
    kd_fit_method="log_linear",
    wave_exclusion_multiplier=0.0,
    wave_sigma_calm_threshold=0.1,
    **fit_kwargs,
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

    Extra keyword arguments in ``fit_kwargs`` (e.g. ``min_decay_range_m``,
    ``min_decay_photons``, ``min_total_photons``) are forwarded to the
    underlying fitter to tune the data-sufficiency constraints.

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
            "fit_failure_reason": [],
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
                    **fit_kwargs,
                )
            )
        if not pass1_results:
            return empty_df
        pass1_df = pd.concat(pass1_results, ignore_index=True)

        # ------------------------------------------------------------------
        # Compute sliding-window noise floor for pass 2
        # ------------------------------------------------------------------
        HALF_WINDOW = 10
        MIN_LOCAL = 3

        nf_array = pass1_df["noise_floor"].values.copy()
        n_bins = len(nf_array)

        valid_nf_all = pass1_df["noise_floor"].dropna()
        valid_nf_all = valid_nf_all[valid_nf_all > 0]
        beam_median_nf = (
            float(valid_nf_all.median()) if len(valid_nf_all) >= MIN_LOCAL else None
        )

        if beam_median_nf is not None:
            expected_nf_per_bin = np.full(n_bins, np.nan)
            for i in range(n_bins):
                lo = max(0, i - HALF_WINDOW)
                hi = min(n_bins, i + HALF_WINDOW + 1)
                window_nf = nf_array[lo:hi]
                valid = window_nf[~np.isnan(window_nf) & (window_nf > 0)]
                if len(valid) >= MIN_LOCAL:
                    expected_nf_per_bin[i] = float(np.median(valid))
                else:
                    expected_nf_per_bin[i] = beam_median_nf

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
                "Hybrid: insufficient noise floor estimates (%d), " "skipping pass 2",
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
                        **fit_kwargs,
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
                    **fit_kwargs,
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
    **fit_kwargs,
):
    """
    Beam-by-beam wrapper that calls calculate_kd for every beam and concatenates
    the results into a single Kd output DataFrame.

    Extra keyword arguments in ``fit_kwargs`` (e.g. ``min_decay_range_m``,
    ``min_decay_photons``, ``min_total_photons``) are forwarded to the
    underlying fitter via ``calculate_kd``.

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
            **fit_kwargs,
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
                "fit_failure_reason",
                "beam_id",
            ]
        )

    # Combine results from all beams into a single DataFrame
    combined_kd_dataset = pd.concat(kd_beam_datasets, ignore_index=True)
    return combined_kd_dataset


def bootstrap_kd_for_bin_loglinear(
    photon_heights, n_boot=500, vertical_res=0.25, rng=None
):
    """
    Legacy log-linear residual bootstrap (kept for reference).

    Build the depth histogram, fit log-linear Beer's Law to get baseline Kd,
    compute residuals, and resample residuals N times to get a distribution
    of bootstrap Kd values. Reports std + 95% CI.

    This does NOT capture BIC breakpoint uncertainty. Use ``bootstrap_kd_for_bin``
    for the hybrid-method bootstrap that re-runs the full fit (BIC breakpoint +
    log-linear decay fit) on every bootstrap iteration.

    Parameters
    ----------
    photon_heights : np.ndarray
        Photon heights (negative below surface) for one along-track bin.
    n_boot : int
        Number of bootstrap iterations.
    vertical_res : float
        Depth bin width (m).
    rng : np.random.Generator or None
        Random number generator for reproducibility.

    Returns
    -------
    dict with keys: kd_baseline, kd_std, kd_ci_low, kd_ci_high, n_boot_success
        All values are NaN if the fit cannot be performed (insufficient data).
    """
    if rng is None:
        rng = np.random.default_rng(42)

    nan_result = {
        "kd_baseline": np.nan,
        "kd_std": np.nan,
        "kd_ci_low": np.nan,
        "kd_ci_high": np.nan,
        "n_boot_success": 0,
    }

    if len(photon_heights) < 20:
        return nan_result

    h_min, h_max = float(np.min(photon_heights)), float(np.max(photon_heights))
    if h_max <= h_min:
        return nan_result

    bin_edges = np.arange(h_min, h_max + vertical_res, vertical_res)
    counts, edges = np.histogram(photon_heights, bins=bin_edges)
    bin_centers = (edges[:-1] + edges[1:]) / 2.0
    mask = counts > 0
    if mask.sum() < 4:
        return nan_result

    counts_used = counts[mask]
    bin_centers_used = bin_centers[mask]
    # zdepth convention: 0 at surface-most bin, increasing downward
    zdepth = bin_centers_used.max() - bin_centers_used
    log_counts = np.log(counts_used.astype(float))

    # Baseline log-linear fit
    model = LinearRegression()
    model.fit(zdepth.reshape(-1, 1), log_counts)
    kd_base = -float(model.coef_[0])
    fitted = model.predict(zdepth.reshape(-1, 1)).flatten()
    residuals = log_counts - fitted

    if kd_base < 0 or np.isnan(kd_base):
        return {**nan_result, "kd_baseline": kd_base}

    # Residual bootstrap
    boot_kds = []
    n_points = len(residuals)
    for _ in range(n_boot):
        boot_resid = rng.choice(residuals, size=n_points, replace=True)
        boot_log = fitted + boot_resid
        m = LinearRegression().fit(zdepth.reshape(-1, 1), boot_log)
        kd_b = -float(m.coef_[0])
        if not np.isnan(kd_b) and kd_b > 0:
            boot_kds.append(kd_b)

    if len(boot_kds) < n_boot * 0.5:
        return {**nan_result, "kd_baseline": kd_base, "n_boot_success": len(boot_kds)}

    boot_kds = np.asarray(boot_kds)
    return {
        "kd_baseline": kd_base,
        "kd_std": float(np.std(boot_kds)),
        "kd_ci_low": float(np.percentile(boot_kds, 2.5)),
        "kd_ci_high": float(np.percentile(boot_kds, 97.5)),
        "n_boot_success": len(boot_kds),
    }


def bootstrap_kd_for_bin(
    photon_heights,
    n_boot=300,
    vertical_res=0.25,
    rng=None,
    fit_method="bma",
    min_decay_range_m=5.0,
    min_decay_photons=30,
    min_decay_bins=8,
    min_total_photons=30,
    min_total_range_m=5.0,
):
    """
    Residual bootstrap for single-bin Kd uncertainty.

    Each bootstrap iteration re-runs the fit procedure (BIC breakpoint
    search + log-linear fit on decay segment), capturing BOTH slope uncertainty
    AND breakpoint-location uncertainty.

    Procedure:
      1. Build depth histogram from photons in the bin.
      2. Run fit on the original histogram to get baseline kd, breakpoint,
         e0, and noise floor.
      3. Compute residuals for each depth bin (log_counts - fitted_value), where
         the fitted value is the log-linear slope for the decay segment and
         log(noise_floor) for the noise segment (if a breakpoint was found).
      4. For each of N bootstrap iterations:
         a. Resample residuals with replacement.
         b. Add resampled residuals to fitted values to produce bootstrap log counts.
         c. Run the fit on the bootstrap histogram to get bootstrap kd
            and bp.
      5. Report kd_std (std of bootstrap kds) + 95% CI, plus bp_std (std of
         bootstrap breakpoints when available).

    Parameters
    ----------
    photon_heights : np.ndarray
        Photon heights (negative below surface) for one along-track bin.
    n_boot : int
        Number of bootstrap iterations. Default 300.
    vertical_res : float
        Depth bin width (m). Default 0.25.
    rng : np.random.Generator or None
        Random number generator for reproducibility.
    fit_method : str
        Fitting method to use for baseline and bootstrap iterations.
        'bma' (default) or 'hybrid'.
    min_decay_range_m, min_decay_photons, min_decay_bins, min_total_photons,
    min_total_range_m : forwarded to the fit function.

    Returns
    -------
    dict with keys: kd_baseline, kd_std, kd_ci_low, kd_ci_high,
        n_boot_success, bp_std. All values are NaN if the fit cannot be
        performed (insufficient data, or the bin is rejected by the
        fit constraints).
    """
    if rng is None:
        rng = np.random.default_rng(42)

    nan_result = {
        "kd_baseline": np.nan,
        "kd_std": np.nan,
        "kd_ci_low": np.nan,
        "kd_ci_high": np.nan,
        "n_boot_success": 0,
        "bp_std": np.nan,
    }

    if len(photon_heights) == 0:
        return nan_result

    h_min = float(np.min(photon_heights))
    h_max = float(np.max(photon_heights))
    if h_max <= h_min:
        return nan_result

    bin_edges = np.arange(h_min, h_max + vertical_res, vertical_res)
    counts, edges = np.histogram(photon_heights, bins=bin_edges)
    bin_centers = (edges[:-1] + edges[1:]) / 2.0
    # zdepth convention: 0 at surface-most bin, increasing downward
    zdepth_all = bin_centers.max() - bin_centers
    hist = pd.DataFrame({"zdepth": zdepth_all, "photon_counts": counts})

    if len(hist) < 6:
        return nan_result

    # Select fit function based on method
    fit_kwargs = dict(
        min_decay_range_m=min_decay_range_m,
        min_decay_photons=min_decay_photons,
        min_decay_bins=min_decay_bins,
        min_total_photons=min_total_photons,
        min_total_range_m=min_total_range_m,
    )
    if fit_method == "bma":
        fit_func = fit_beers_law_bma
    else:
        fit_func = fit_beers_law_hybrid

    # Baseline fit
    kd_base, e0_base, bp_base, nf_base, reason = fit_func(
        hist,
        **fit_kwargs,
    )

    if np.isnan(kd_base) or reason is not None:
        # Bin rejected by hybrid constraints — no uncertainty to report.
        return {**nan_result, "kd_baseline": kd_base}

    # Build residuals from the baseline fit on non-empty bins.
    df = (
        hist[hist["photon_counts"] > 0]
        .copy()
        .sort_values("zdepth")
        .reset_index(drop=True)
    )
    df["log_counts"] = np.log(df["photon_counts"].astype(float))

    if not np.isnan(bp_base):
        # Two-segment model: linear decay + constant noise floor.
        decay_mask = df["zdepth"] < bp_base
        noise_mask = ~decay_mask

        fitted = np.empty(len(df))
        # Decay: log_counts ~ log(e0) - kd*zdepth
        fitted[decay_mask.values] = (
            np.log(e0_base) - kd_base * df.loc[decay_mask, "zdepth"].values
        )
        # Noise segment: constant log(noise_floor) (fallback to empirical mean).
        if not np.isnan(nf_base) and nf_base > 0:
            fitted[noise_mask.values] = np.log(nf_base)
        else:
            fitted[noise_mask.values] = (
                df.loc[noise_mask, "log_counts"].mean() if noise_mask.any() else 0.0
            )
    else:
        # Full-line fallback (no breakpoint selected).
        fitted = np.log(e0_base) - kd_base * df["zdepth"].values

    residuals = df["log_counts"].values - fitted
    zdepth_fit = df["zdepth"].values

    # Bootstrap: resample residuals, add to fitted, re-run fit.
    boot_kds = []
    boot_bps = []
    for _ in range(n_boot):
        boot_resid = rng.choice(residuals, size=len(residuals), replace=True)
        boot_log = fitted + boot_resid
        boot_counts = np.exp(boot_log)
        # Clip to avoid zero or negative counts; histogram fit uses log.
        boot_counts = np.clip(boot_counts, 0.5, None)
        boot_hist = pd.DataFrame({"zdepth": zdepth_fit, "photon_counts": boot_counts})
        kd_b, _e0_b, bp_b, _nf_b, _reason_b = fit_func(
            boot_hist,
            **fit_kwargs,
        )
        if not np.isnan(kd_b) and kd_b > 0:
            boot_kds.append(kd_b)
            if not np.isnan(bp_b):
                boot_bps.append(bp_b)

    # Hybrid fit is more stringent than log-linear — use a lower success threshold.
    if len(boot_kds) < n_boot * 0.3:
        return {**nan_result, "kd_baseline": kd_base, "n_boot_success": len(boot_kds)}

    boot_kds = np.asarray(boot_kds)
    return {
        "kd_baseline": kd_base,
        "kd_std": float(np.std(boot_kds)),
        "kd_ci_low": float(np.percentile(boot_kds, 2.5)),
        "kd_ci_high": float(np.percentile(boot_kds, 97.5)),
        "n_boot_success": len(boot_kds),
        "bp_std": float(np.std(boot_bps)) if len(boot_bps) > 1 else np.nan,
    }


def bootstrap_kd_uncertainty(
    subsurface_photon_df,
    n_boot=300,
    vertical_res=0.25,
    random_seed=42,
    fit_method="bma",
    min_decay_range_m=5.0,
    min_decay_photons=30,
    min_decay_bins=8,
    min_total_photons=30,
    min_total_range_m=5.0,
):
    """
    Apply bootstrap to every along-track bin in a subsurface photon DataFrame.

    Parameters
    ----------
    subsurface_photon_df : pd.DataFrame
        Must contain 'lat_bins' and 'photon_height' columns.
    n_boot : int
        Bootstrap iterations per bin. Set to 0 to skip bootstrap entirely
        (returns an empty DataFrame).
    vertical_res : float
        Depth bin width (m).
    random_seed : int
        Random seed for reproducibility.
    fit_method : str
        Fitting method for baseline and bootstrap iterations ('bma' or 'hybrid').
    min_decay_range_m, min_decay_photons, min_decay_bins, min_total_photons,
    min_total_range_m : forwarded to the fit function via
        ``bootstrap_kd_for_bin`` so defaults match the pipeline fit.

    Returns
    -------
    pd.DataFrame
        Columns: lat_bins, kd_baseline, kd_std, kd_ci_low, kd_ci_high,
        n_boot_success, bp_std. One row per unique lat_bin in the input.
        Empty DataFrame if n_boot=0.
    """
    empty_cols = [
        "lat_bins",
        "kd_baseline",
        "kd_std",
        "kd_ci_low",
        "kd_ci_high",
        "n_boot_success",
        "bp_std",
    ]
    if n_boot <= 0:
        return pd.DataFrame(columns=empty_cols)

    rng = np.random.default_rng(random_seed)
    results = []
    for lb in sorted(subsurface_photon_df["lat_bins"].unique()):
        bin_heights = subsurface_photon_df[subsurface_photon_df["lat_bins"] == lb][
            "photon_height"
        ].values
        r = bootstrap_kd_for_bin(
            bin_heights,
            n_boot=n_boot,
            vertical_res=vertical_res,
            rng=rng,
            fit_method=fit_method,
            min_decay_range_m=min_decay_range_m,
            min_decay_photons=min_decay_photons,
            min_decay_bins=min_decay_bins,
            min_total_photons=min_total_photons,
            min_total_range_m=min_total_range_m,
        )
        r["lat_bins"] = lb
        results.append(r)

    if not results:
        # Empty input (e.g. track rejected upstream) — preserve the schema
        # so callers' df[cols] / merge calls don't blow up with KeyError.
        return pd.DataFrame(columns=empty_cols)
    df = pd.DataFrame(results)
    cols = [
        "lat_bins",
        "kd_baseline",
        "kd_std",
        "kd_ci_low",
        "kd_ci_high",
        "n_boot_success",
        "bp_std",
    ]
    return df[cols]
