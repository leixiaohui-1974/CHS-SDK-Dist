"""
Module for data cleaning utilities.
"""
import pandas as pd
from typing import List, Union

def fill_missing_with_interpolation(data: Union[pd.Series, List]) -> pd.Series:
    """
    Fills missing values (NaN) in a time series using linear interpolation.

    Args:
        data: A pandas Series or a list containing numbers and potentially
              None or np.nan for missing values.

    Returns:
        A new pandas Series with missing values filled.
    """
    # Ensure the data is a pandas Series for easy manipulation
    if not isinstance(data, pd.Series):
        series = pd.Series(data, dtype=float)
    else:
        series = data.astype(float)

    # Use pandas' built-in interpolate method
    # This is highly optimized and handles edge cases (e.g., leading/trailing NaNs).
    filled_series = series.interpolate(method='linear', limit_direction='both')

    return filled_series
