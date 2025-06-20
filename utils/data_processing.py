"""
Data processing utilities for financial time series data.
"""
from typing import Dict, List, Optional, Tuple, Union
import pandas as pd
import numpy as np
from pandas import DataFrame, Series, DatetimeIndex
import pytz
from datetime import datetime, timedelta

def resample_data(
    df: DataFrame,
    timeframe: str = '1H',
    price_col: str = 'close',
    volume_col: Optional[str] = 'volume',
    tz: Optional[str] = None
) -> DataFrame:
    """
    Resample OHLCV data to a different timeframe.
    
    Args:
        df: Input DataFrame with datetime index and OHLCV columns
        timeframe: Target timeframe (e.g., '1H', '4H', '1D')
        price_col: Name of the price column
        volume_col: Name of the volume column (optional)
        tz: Timezone string (e.g., 'UTC', 'America/New_York')
        
    Returns:
        Resampled DataFrame
    """
    if not isinstance(df.index, DatetimeIndex):
        raise ValueError("DataFrame must have a DatetimeIndex")
    
    # Make a copy to avoid modifying the original
    df = df.copy()
    
    # Convert timezone if specified
    if tz is not None:
        df = df.tz_convert(pytz.timezone(tz), copy=True)
    
    # Define aggregation dictionary
    agg_dict = {
        'open': 'first',
        'high': 'max',
        'low': 'min',
        'close': 'last'
    }
    
    # Add volume if available
    if volume_col and volume_col in df.columns:
        agg_dict[volume_col] = 'sum'
    
    # Resample the data
    resampled = df.resample(timeframe).agg(agg_dict)
    
    # Forward fill any missing values for OHLC (but not volume)
    ohlc_cols = ['open', 'high', 'low', 'close']
    resampled[ohlc_cols] = resampled[ohlc_cols].ffill()
    
    # Drop any remaining NaN rows (usually at the beginning)
    resampled = resampled.dropna(subset=ohlc_cols)
    
    return resampled

def calculate_returns(
    prices: Union[Series, np.ndarray],
    method: str = 'log',
    periods: int = 1,
    fillna: bool = True
) -> Series:
    """
    Calculate returns from price data.
    
    Args:
        prices: Price Series or array
        method: 'log' for log returns, 'simple' for simple returns
        periods: Number of periods to shift for return calculation
        fillna: If True, fill NaN values with 0
        
    Returns:
        Series of returns
    """
    if not isinstance(prices, (Series, np.ndarray)):
        raise ValueError("Input must be a pandas Series or numpy array")
    
    prices = pd.Series(prices) if not isinstance(prices, Series) else prices
    
    if method == 'log':
        returns = np.log(prices / prices.shift(periods))
    elif method == 'simple':
        returns = prices.pct_change(periods=periods)
    else:
        raise ValueError("method must be 'log' or 'simple'")
    
    if fillna:
        returns = returns.fillna(0)
    
    return returns

def normalize_data(
    data: Union[DataFrame, Series],
    method: str = 'minmax',
    feature_range: Tuple[float, float] = (0, 1),
    axis: int = 0
) -> Union[DataFrame, Series]:
    """
    Normalize data using the specified method.
    
    Args:
        data: Input data (DataFrame or Series)
        method: Normalization method ('minmax', 'zscore', 'robust')
        feature_range: Desired range for min-max scaling (min, max)
        axis: Axis to normalize along (0 for columns, 1 for rows)
        
    Returns:
        Normalized data
    """
    if not isinstance(data, (DataFrame, Series)):
        raise ValueError("Input must be a pandas DataFrame or Series")
    
    if method == 'minmax':
        min_val = data.min(axis=axis)
        max_val = data.max(axis=axis)
        range_diff = max_val - min_val
        
        # Handle division by zero
        range_diff[range_diff == 0] = 1
        
        normalized = (data - min_val) / range_diff
        
        # Scale to feature range
        if feature_range != (0, 1):
            min_desired, max_desired = feature_range
            normalized = normalized * (max_desired - min_desired) + min_desired
            
    elif method == 'zscore':
        mean = data.mean(axis=axis)
        std = data.std(axis=axis)
        
        # Handle division by zero
        std[std == 0] = 1
        
        normalized = (data - mean) / std
        
    elif method == 'robust':
        median = data.median(axis=axis)
        q75 = data.quantile(0.75, axis=axis)
        q25 = data.quantile(0.25, axis=axis)
        iqr = q75 - q25
        
        # Handle division by zero
        iqr[iqr == 0] = 1
        
        normalized = (data - median) / iqr
        
    else:
        raise ValueError("method must be 'minmax', 'zscore', or 'robust'")
    
    return normalized

def add_technical_indicators(
    df: DataFrame,
    close_col: str = 'close',
    high_col: str = 'high',
    low_col: str = 'low',
    volume_col: Optional[str] = None,
    indicators: Optional[Dict[str, dict]] = None
) -> DataFrame:
    """
    Add technical indicators to a DataFrame with OHLCV data.
    
    Args:
        df: Input DataFrame with OHLCV data
        close_col: Name of the close price column
        high_col: Name of the high price column
        low_col: Name of the low price column
        volume_col: Name of the volume column (optional)
        indicators: Dictionary of indicators to add with their parameters
                   Example: {'sma': {'periods': [20, 50]}, 'rsi': {'period': 14}}
                   
    Returns:
        DataFrame with added indicator columns
    """
    if indicators is None:
        indicators = {
            'sma': {'periods': [20, 50, 200]},
            'ema': {'periods': [9, 21]},
            'rsi': {'period': 14},
            'bb': {'period': 20, 'std_dev': 2.0},
            'macd': {'fast_period': 12, 'slow_period': 26, 'signal_period': 9}
        }
    
    # Make a copy to avoid modifying the original
    df = df.copy()
    
    # Add indicators
    for indicator, params in indicators.items():
        if indicator.lower() == 'sma':
            periods = params.get('periods', [20, 50])
            for period in periods:
                df[f'sma_{period}'] = df[close_col].rolling(window=period).mean()
                
        elif indicator.lower() == 'ema':
            periods = params.get('periods', [9, 21])
            for period in periods:
                df[f'ema_{period}'] = df[close_col].ewm(span=period, adjust=False).mean()
                
        elif indicator.lower() == 'rsi':
            from .indicators import calculate_rsi
            period = params.get('period', 14)
            df['rsi'] = calculate_rsi(df[close_col], period=period)
            
        elif indicator.lower() in ['bb', 'bollinger']:
            from .indicators import calculate_bollinger_bands
            period = params.get('period', 20)
            std_dev = params.get('std_dev', 2.0)
            bb = calculate_bollinger_bands(df[close_col], period=period, std_dev=std_dev)
            df['bb_upper'] = bb['upper']
            df['bb_middle'] = bb['middle']
            df['bb_lower'] = bb['lower']
            
        elif indicator.lower() == 'macd':
            from .indicators import calculate_macd
            fast = params.get('fast_period', 12)
            slow = params.get('slow_period', 26)
            signal = params.get('signal_period', 9)
            macd = calculate_macd(df[close_col], fast_period=fast, slow_period=slow, signal_period=signal)
            df['macd'] = macd['macd']
            df['macd_signal'] = macd['signal']
            df['macd_hist'] = macd['histogram']
            
        elif indicator.lower() == 'atr':
            from .indicators import calculate_atr
            period = params.get('period', 14)
            df['atr'] = calculate_atr(df[high_col], df[low_col], df[close_col], period=period)
            
        elif indicator.lower() == 'volume' and volume_col is not None:
            # Add volume-based indicators
            ma_period = params.get('ma_period', 20)
            df['volume_ma'] = df[volume_col].rolling(window=ma_period).mean()
            df['volume_ratio'] = df[volume_col] / df['volume_ma']
    
    return df

def detect_outliers(
    data: Union[DataFrame, Series],
    method: str = 'zscore',
    threshold: float = 3.0,
    fill_method: Optional[str] = None
) -> Union[DataFrame, Tuple[Union[DataFrame, Series], np.ndarray]]:
    """
    Detect and optionally fill outliers in the data.
    
    Args:
        data: Input data (DataFrame or Series)
        method: Method for outlier detection ('zscore', 'iqr')
        threshold: Threshold for outlier detection
        fill_method: If None, return mask of outliers. Otherwise, fill outliers using:
                   'mean', 'median', 'linear', 'nearest', etc.
        
    Returns:
        If fill_method is None: Tuple of (data, outlier_mask)
        Otherwise: Data with filled values
    """
    if not isinstance(data, (DataFrame, Series)):
        raise ValueError("Input must be a pandas DataFrame or Series")
    
    # Make a copy to avoid modifying the original
    data = data.copy()
    
    if method == 'zscore':
        if isinstance(data, DataFrame):
            z_scores = (data - data.mean()) / data.std()
            outlier_mask = (z_scores.abs() > threshold)
        else:  # Series
            z_scores = (data - data.mean()) / data.std()
            outlier_mask = (z_scores.abs() > threshold)
            
    elif method == 'iqr':
        if isinstance(data, DataFrame):
            q1 = data.quantile(0.25)
            q3 = data.quantile(0.75)
            iqr = q3 - q1
            lower_bound = q1 - threshold * iqr
            upper_bound = q3 + threshold * iqr
            outlier_mask = (data < lower_bound) | (data > upper_bound)
        else:  # Series
            q1 = data.quantile(0.25)
            q3 = data.quantile(0.75)
            iqr = q3 - q1
            lower_bound = q1 - threshold * iqr
            upper_bound = q3 + threshold * iqr
            outlier_mask = (data < lower_bound) | (data > upper_bound)
    else:
        raise ValueError("method must be 'zscore' or 'iqr'")
    
    if fill_method is None:
        return data, outlier_mask
    else:
        if fill_method in ['mean', 'median']:
            if isinstance(data, DataFrame):
                fill_values = data.mean() if fill_method == 'mean' else data.median()
                data = data.mask(outlier_mask, fill_values, axis=1)
            else:  # Series
                fill_value = data.mean() if fill_method == 'mean' else data.median()
                data = data.mask(outlier_mask, fill_value)
        else:
            # Use pandas interpolation
            data = data.interpolate(method=fill_method, limit_direction='both')
        
        return data
