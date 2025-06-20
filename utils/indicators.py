"""
Technical indicators for market analysis.
"""
from typing import Tuple, Dict, Optional, Union, List
import numpy as np
import pandas as pd
from pandas import DataFrame, Series

def calculate_atr(
    high: Union[Series, np.ndarray],
    low: Union[Series, np.ndarray],
    close: Union[Series, np.ndarray],
    period: int = 14,
    fillna: bool = False
) -> Series:
    """
    Calculate the Average True Range (ATR) indicator.
    
    Args:
        high: High prices
        low: Low prices
        close: Close prices
        period: Number of periods for ATR calculation
        fillna: If True, fill NaN values with 0
        
    Returns:
        Series: ATR values
    """
    if not isinstance(high, (Series, np.ndarray)) or not isinstance(low, (Series, np.ndarray)) or not isinstance(close, (Series, np.ndarray)):
        raise ValueError("Inputs must be pandas Series or numpy arrays")
    
    if len(high) != len(low) or len(high) != len(close):
        raise ValueError("Input arrays must have the same length")
    
    # Convert to numpy arrays for faster computation
    high = np.asarray(high, dtype=np.float64)
    low = np.asarray(low, dtype=np.float64)
    close = np.asarray(close, dtype=np.float64)
    
    # Calculate True Range
    prev_close = np.roll(close, 1)
    prev_close[0] = np.nan  # First value has no previous close
    
    tr1 = high - low
    tr2 = np.abs(high - prev_close)
    tr3 = np.abs(low - prev_close)
    
    true_range = np.maximum(np.maximum(tr1, tr2), tr3)
    
    # Calculate ATR using Wilder's smoothing (WMA)
    atr = pd.Series(true_range).ewm(alpha=1/period, min_periods=period, adjust=False).mean()
    
    if fillna:
        atr = atr.fillna(0)
    
    return atr

def calculate_rsi(
    close: Union[Series, np.ndarray],
    period: int = 14,
    fillna: bool = False
) -> Series:
    """
    Calculate the Relative Strength Index (RSI) indicator.
    
    Args:
        close: Close prices
        period: Number of periods for RSI calculation
        fillna: If True, fill NaN values with 50 (neutral RSI)
        
    Returns:
        Series: RSI values (0-100)
    """
    if not isinstance(close, (Series, np.ndarray)):
        raise ValueError("Input must be a pandas Series or numpy array")
    
    close = pd.Series(close) if not isinstance(close, Series) else close
    
    # Calculate price changes
    delta = close.diff()
    
    # Separate gains and losses
    gain = delta.where(delta > 0, 0.0)
    loss = -delta.where(delta < 0, 0.0)
    
    # Calculate average gain and loss
    avg_gain = gain.ewm(alpha=1/period, min_periods=period, adjust=False).mean()
    avg_loss = loss.ewm(alpha=1/period, min_periods=period, adjust=False).mean()
    
    # Calculate RS and RSI
    rs = avg_gain / avg_loss
    rsi = 100 - (100 / (1 + rs))
    
    if fillna:
        rsi = rsi.fillna(50)  # Neutral RSI is 50
    
    return rsi

def calculate_moving_averages(
    close: Union[Series, np.ndarray],
    periods: List[int] = [20, 50, 200],
    ma_type: str = 'sma',
    fillna: bool = False
) -> Dict[str, Series]:
    """
    Calculate various moving averages.
    
    Args:
        close: Close prices
        periods: List of periods for moving averages
        ma_type: Type of moving average ('sma' or 'ema')
        fillna: If True, fill NaN values with the first valid value
        
    Returns:
        Dictionary of moving average Series with period as key
    """
    if not isinstance(close, (Series, np.ndarray)):
        raise ValueError("Input must be a pandas Series or numpy array")
    
    close = pd.Series(close) if not isinstance(close, Series) else close
    ma_type = ma_type.lower()
    
    if ma_type not in ['sma', 'ema']:
        raise ValueError("ma_type must be either 'sma' or 'ema'")
    
    mas = {}
    
    for period in periods:
        if ma_type == 'sma':
            ma = close.rolling(window=period, min_periods=1).mean()
        else:  # ema
            ma = close.ewm(span=period, min_periods=period, adjust=False).mean()
        
        if fillna:
            ma = ma.fillna(method='bfill')
        
        mas[f'{ma_type.upper()}_{period}'] = ma
    
    return mas

def calculate_bollinger_bands(
    close: Union[Series, np.ndarray],
    period: int = 20,
    std_dev: float = 2.0,
    fillna: bool = False
) -> Dict[str, Series]:
    """
    Calculate Bollinger Bands.
    
    Args:
        close: Close prices
        period: Number of periods for the moving average
        std_dev: Number of standard deviations for the bands
        fillna: If True, fill NaN values with the first valid value
        
    Returns:
        Dictionary with 'upper', 'middle', and 'lower' bands
    """
    if not isinstance(close, (Series, np.ndarray)):
        raise ValueError("Input must be a pandas Series or numpy array")
    
    close = pd.Series(close) if not isinstance(close, Series) else close
    
    # Calculate middle band (SMA)
    middle_band = close.rolling(window=period, min_periods=1).mean()
    
    # Calculate standard deviation
    std = close.rolling(window=period, min_periods=1).std()
    
    # Calculate upper and lower bands
    upper_band = middle_band + (std * std_dev)
    lower_band = middle_band - (std * std_dev)
    
    if fillna:
        middle_band = middle_band.fillna(method='bfill')
        upper_band = upper_band.fillna(method='bfill')
        lower_band = lower_band.fillna(method='bfill')
    
    return {
        'upper': upper_band,
        'middle': middle_band,
        'lower': lower_band
    }

def calculate_macd(
    close: Union[Series, np.ndarray],
    fast_period: int = 12,
    slow_period: int = 26,
    signal_period: int = 9,
    fillna: bool = False
) -> Dict[str, Series]:
    """
    Calculate Moving Average Convergence Divergence (MACD).
    
    Args:
        close: Close prices
        fast_period: Number of periods for fast EMA
        slow_period: Number of periods for slow EMA
        signal_period: Number of periods for signal line
        fillna: If True, fill NaN values with 0
        
    Returns:
        Dictionary with 'macd', 'signal', and 'histogram' Series
    """
    if not isinstance(close, (Series, np.ndarray)):
        raise ValueError("Input must be a pandas Series or numpy array")
    
    close = pd.Series(close) if not isinstance(close, Series) else close
    
    # Calculate EMAs
    fast_ema = close.ewm(span=fast_period, min_periods=fast_period, adjust=False).mean()
    slow_ema = close.ewm(span=slow_period, min_periods=slow_period, adjust=False).mean()
    
    # Calculate MACD line
    macd_line = fast_ema - slow_ema
    
    # Calculate signal line
    signal_line = macd_line.ewm(span=signal_period, min_periods=signal_period, adjust=False).mean()
    
    # Calculate histogram
    histogram = macd_line - signal_line
    
    if fillna:
        macd_line = macd_line.fillna(0)
        signal_line = signal_line.fillna(0)
        histogram = histogram.fillna(0)
    
    return {
        'macd': macd_line,
        'signal': signal_line,
        'histogram': histogram
    }

def calculate_support_resistance(
    high: Union[Series, np.ndarray],
    low: Union[Series, np.ndarray],
    close: Union[Series, np.ndarray],
    lookback: int = 20,
    threshold: float = 2.0
) -> Dict[str, List[float]]:
    """
    Identify support and resistance levels using swing highs and lows.
    
    Args:
        high: High prices
        low: Low prices
        close: Close prices
        lookback: Number of periods to look back for swing points
        threshold: Minimum distance between levels (in ATR)
        
    Returns:
        Dictionary with 'support' and 'resistance' levels
    """
    if not isinstance(high, (Series, np.ndarray)) or not isinstance(low, (Series, np.ndarray)) or not isinstance(close, (Series, np.ndarray)):
        raise ValueError("Inputs must be pandas Series or numpy arrays")
    
    high = pd.Series(high) if not isinstance(high, Series) else high
    low = pd.Series(low) if not isinstance(low, Series) else low
    close = pd.Series(close) if not isinstance(close, Series) else close
    
    # Calculate ATR for threshold
    atr = calculate_atr(high, low, close, period=14)
    min_distance = atr.iloc[-1] * threshold
    
    # Find swing highs and lows
    highs = []
    lows = []
    
    for i in range(lookback, len(close) - lookback):
        # Check for swing high
        is_swing_high = True
        for j in range(1, lookback + 1):
            if high.iloc[i] < high.iloc[i - j] or high.iloc[i] < high.iloc[i + j]:
                is_swing_high = False
                break
        
        if is_swing_high:
            highs.append(high.iloc[i])
        
        # Check for swing low
        is_swing_low = True
        for j in range(1, lookback + 1):
            if low.iloc[i] > low.iloc[i - j] or low.iloc[i] > low.iloc[i + j]:
                is_swing_low = False
                break
        
        if is_swing_low:
            lows.append(low.iloc[i])
    
    # Filter levels that are too close to each other
    def filter_levels(levels, min_dist):
        if not levels:
            return []
            
        levels = sorted(levels)
        filtered = [levels[0]]
        
        for level in levels[1:]:
            if level - filtered[-1] >= min_dist:
                filtered.append(level)
        
        return filtered
    
    support_levels = filter_levels(lows, min_distance)
    resistance_levels = filter_levels(highs, min_distance)
    
    return {
        'support': support_levels,
        'resistance': resistance_levels
    }
