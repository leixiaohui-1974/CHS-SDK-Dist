"""
Module for model evaluation metrics.

This module provides standard metrics used in hydrology and time series
forecasting to compare simulated or predicted data against observed data.
"""
import numpy as np
from typing import Union, List

def calculate_rmse(simulated: Union[List[float], np.ndarray],
                   observed: Union[List[float], np.ndarray]) -> float:
    """
    Calculates the Root Mean Squared Error (RMSE).

    Args:
        simulated: A list or numpy array of simulated values.
        observed: A list or numpy array of observed values.

    Returns:
        The RMSE value.
    """
    sim = np.asarray(simulated)
    obs = np.asarray(observed)
    if sim.shape != obs.shape:
        raise ValueError("Simulated and observed arrays must have the same shape.")

    return np.sqrt(np.mean((sim - obs) ** 2))


def calculate_nse(simulated: Union[List[float], np.ndarray],
                  observed: Union[List[float], np.ndarray]) -> float:
    """
    Calculates the Nash-Sutcliffe Efficiency (NSE).

    NSE is a widely used indicator of the goodness of fit for hydrological models.
    It ranges from -inf to 1. An NSE of 1 corresponds to a perfect match,
    an NSE of 0 indicates the model is as accurate as the mean of the observed data,
    and an NSE < 0 indicates the observed mean is a better predictor than the model.

    Args:
        simulated: A list or numpy array of simulated values.
        observed: A list or numpy array of observed values.

    Returns:
        The NSE value.
    """
    sim = np.asarray(simulated)
    obs = np.asarray(observed)
    if sim.shape != obs.shape:
        raise ValueError("Simulated and observed arrays must have the same shape.")

    numerator = np.sum((sim - obs) ** 2)
    denominator = np.sum((obs - np.mean(obs)) ** 2)

    if denominator == 0:
        # Avoid division by zero if the observed data is constant
        return -np.inf

    return 1 - (numerator / denominator)


def calculate_kge(simulated: Union[List[float], np.ndarray],
                  observed: Union[List[float], np.ndarray]) -> float:
    """
    Calculates the Kling-Gupta Efficiency (KGE).

    KGE is designed to overcome shortcomings in the NSE. It decomposes the
    mean squared error into three components: correlation, bias, and variability.
    Like NSE, a KGE of 1 is optimal.

    The formula is: KGE = 1 - sqrt((r-1)^2 + (beta-1)^2 + (gamma-1)^2)
    - r: Pearson correlation coefficient
    - beta: Bias ratio (mean_sim / mean_obs)
    - gamma: Variability ratio (std_sim / std_obs)

    Args:
        simulated: A list or numpy array of simulated values.
        observed: A list or numpy array of observed values.

    Returns:
        The KGE value.
    """
    sim = np.asarray(simulated)
    obs = np.asarray(observed)
    if sim.shape != obs.shape:
        raise ValueError("Simulated and observed arrays must have the same shape.")

    mean_sim = np.mean(sim)
    mean_obs = np.mean(obs)
    std_sim = np.std(sim)
    std_obs = np.std(obs)

    if mean_obs == 0 or std_obs == 0:
        # Avoid division by zero in bias or variability calculations
        return -np.inf

    # Pearson correlation coefficient (r)
    r = np.corrcoef(sim, obs)[0, 1]

    # Bias ratio (beta)
    beta = mean_sim / mean_obs

    # Variability ratio (gamma)
    gamma = std_sim / std_obs

    # KGE calculation
    kge = 1 - np.sqrt((r - 1)**2 + (beta - 1)**2 + (gamma - 1)**2)

    return kge
