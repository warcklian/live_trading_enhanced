import pandas as pd
import numpy as np
from typing import Optional, Dict, Any, List, Tuple
import MetaTrader5 as mt5
from datetime import datetime, timedelta

class TradingStrategy:
    """
    Implements the SMC (Smart Money Concept) trading strategy
    """
    
    def __init__(self, symbol: str, df: pd.DataFrame, config: Optional[Dict[str, Any]] = None):
        """
        Initialize the trading strategy
        
        Args:
            symbol: Trading symbol (e.g., 'EURUSD')
            df: DataFrame with historical price data
            config: Optional configuration dictionary
        """
        self.symbol = symbol
        self.df = df.copy()
        self.config = self._get_default_config()
        
        # Update with provided config
        if config:
            self.config.update(config)
        
        # Calculate indicators
        self._calculate_indicators()
    
    def _get_default_config(self) -> Dict[str, Any]:
        """Get default strategy configuration"""
        return {
            'ma_period': 20,           # Moving average period
            'atr_period': 14,          # ATR period
            'rsi_period': 14,          # RSI period
            'rsi_overbought': 70,      # RSI overbought level
            'rsi_oversold': 30,        # RSI oversold level
            'risk_reward_ratio': 2.0,  # Risk:Reward ratio
            'max_trades_per_day': 5,   # Maximum number of trades per day
            'use_volume': True,        # Use volume in analysis
            'use_order_blocks': True,  # Use order blocks for entries
            'use_liquidity': True,     # Use liquidity zones for targets/stops
            'timeframe': '15m',        # Default timeframe
            'lot_size': 0.1,           # Default lot size
            'risk_per_trade': 1.0,     # Risk per trade (% of balance)
            'trailing_stop': True,     # Use trailing stop
            'trail_offset': 1.5,       # ATR multiplier for trailing stop
            'break_even': True,        # Move to break even
            'break_even_atr': 1.0,     # ATR multiplier for break even
            'max_drawdown_pct': 5.0,   # Max daily drawdown percentage
        }
    
    def _calculate_indicators(self):
        """Calculate technical indicators"""
        if self.df.empty:
            return
        
        df = self.df
        
        # Calculate moving averages
        df['ma_fast'] = df['close'].rolling(window=self.config['ma_period']).mean()
        df['ma_slow'] = df['close'].rolling(window=self.config['ma_period'] * 2).mean()
        
        # Calculate ATR
        df['tr'] = self._true_range(df)
        df['atr'] = df['tr'].rolling(window=self.config['atr_period']).mean()
        
        # Calculate RSI
        delta = df['close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=self.config['rsi_period']).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=self.config['rsi_period']).mean()
        rs = gain / loss
        df['rsi'] = 100 - (100 / (1 + rs))
        
        # Identify trend
        df['trend'] = self._identify_trend(df)
        
        # Identify order blocks if enabled
        if self.config['use_order_blocks']:
            df['order_blocks'] = self._identify_order_blocks(df)
        
        # Identify liquidity zones if enabled
        if self.config['use_liquidity']:
            df['liquidity_zones'] = self._identify_liquidity_zones(df)
        
        self.df = df
    
    def _true_range(self, df: pd.DataFrame) -> pd.Series:
        """Calculate True Range"""
        tr1 = df['high'] - df['low']
        tr2 = abs(df['high'] - df['close'].shift())
        tr3 = abs(df['low'] - df['close'].shift())
        return pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
    
    def _identify_trend(self, df: pd.DataFrame) -> pd.Series:
        """Identify market trend"""
        # Simple moving average crossover
        ma_fast = df['close'].rolling(window=self.config['ma_period']).mean()
        ma_slow = df['close'].rolling(window=self.config['ma_period'] * 2).mean()
        
        # 1 for uptrend, -1 for downtrend, 0 for neutral
        trend = np.where(ma_fast > ma_slow, 1, -1)
        return pd.Series(trend, index=df.index)
    
    def _identify_order_blocks(self, df: pd.DataFrame, lookback: int = 20) -> pd.Series:
        """Identify order blocks in price action using SMC methodology"""
        df = df.copy()
        df['ob_bullish'] = np.nan
        df['ob_bearish'] = np.nan
        
        for i in range(lookback, len(df)):
            # Bullish Order Block
            if (df['close'].iloc[i-1] < df['open'].iloc[i-1] and 
                df['close'].iloc[i] > df['open'].iloc[i] and 
                df['close'].iloc[i] > df['high'].iloc[i-1]):
                df.at[df.index[i-1], 'ob_bullish'] = df['low'].iloc[i-1]
                
                # Verificar si es un bloque de orden válido
                if i >= 2:
                    prev_high = df['high'].iloc[i-2:i-1].max()
                    if df['close'].iloc[i] > prev_high:
                        df.at[df.index[i-1], 'ob_bullish'] = df['low'].iloc[i-1]
            
            # Bearish Order Block
            if (df['close'].iloc[i-1] > df['open'].iloc[i-1] and 
                df['close'].iloc[i] < df['open'].iloc[i] and 
                df['close'].iloc[i] < df['low'].iloc[i-1]):
                df.at[df.index[i-1], 'ob_bearish'] = df['high'].iloc[i-1]
                
                # Verificar si es un bloque de orden válido
                if i >= 2:
                    prev_low = df['low'].iloc[i-2:i-1].min()
                    if df['close'].iloc[i] < prev_low:
                        df.at[df.index[i-1], 'ob_bearish'] = df['high'].iloc[i-1]
        
        # Convertir a series con valores 1 (bullish), -1 (bearish), 0 (neutral)
        blocks = pd.Series(0, index=df.index)
        blocks[df['ob_bullish'].notna()] = 1
        blocks[df['ob_bearish'].notna()] = -1
        
        return blocks
    
    def _identify_liquidity_zones(self, df: pd.DataFrame, window: int = 50) -> pd.Series:
        """Identify liquidity zones using SMC methodology"""
        df = df.copy()
        
        # Calcular máximos y mínimos recientes
        df['recent_high'] = df['high'].rolling(window=window).max()
        df['recent_low'] = df['low'].rolling(window=window).min()
        
        # Identificar zonas de liquidez superiores
        df['liquidity_high'] = np.where(
            (df['high'] == df['recent_high']) & 
            (df['high'].shift(1) != df['recent_high'].shift(1)) &
            (df['volume'] > df['volume'].rolling(window=20).mean() * 1.2),
            df['high'],
            np.nan
        )
        
        # Identificar zonas de liquidez inferiores
        df['liquidity_low'] = np.where(
            (df['low'] == df['recent_low']) & 
            (df['low'].shift(1) != df['recent_low'].shift(1)) &
            (df['volume'] > df['volume'].rolling(window=20).mean() * 1.2),
            df['low'],
            np.nan
        )
        
        # Crear series con valores 1 (zona superior), -1 (zona inferior), 0 (neutral)
        zones = pd.Series(0, index=df.index)
        zones[df['liquidity_high'].notna()] = 1
        zones[df['liquidity_low'].notna()] = -1
        
        # Añadir información sobre la fuerza de la zona
        if 'volume' in df.columns:
            volume_strength = df['volume'] / df['volume'].rolling(window=20).mean()
            zones = zones * volume_strength
        
        return zones
    
    def check_signals(self) -> Optional[Dict[str, Any]]:
        """
        Check for trading signals based on SMC methodology
        
        Returns:
            dict: Signal information or None if no signal
        """
        if self.df.empty or len(self.df) < max(self.config['ma_period'] * 2, self.config['atr_period']):
            return None
            
        # Calcular indicadores SMC
        df = self.df.copy()
        prd = self.config.get('smc_period', 20)
        resp = self.config.get('smc_response', 7)
        
        # Calcular pivotes y niveles
        df['Up'] = df['high'].rolling(prd).max()
        df['Dn'] = df['low'].rolling(prd).min()
        
        df['pvtHi'] = df['high'].rolling(2*prd+1, center=True).apply(
            lambda x: x[prd] if x[prd] == max(x) else np.nan, raw=True)
        df['pvtLo'] = df['low'].rolling(2*prd+1, center=True).apply(
            lambda x: x[prd] if x[prd] == min(x) else np.nan, raw=True)
        
        # Analizar últimas barras para señales
        latest_idx = len(df) - 1
        if latest_idx < 2*prd:
            return None
            
        signal = {
            'symbol': self.symbol,
            'timestamp': df.index[-1],
            'price': df['close'].iloc[-1],
            'volume': df['volume'].iloc[-1] if 'volume' in df else 0,
            'atr': df['atr'].iloc[-1]
        }
        
        # Verificar señales CHoCH (Change of Character)
        if not pd.isna(df['pvtHi'].iloc[-1]) and df['high'].iloc[-1] > df['Up'].iloc[-2]:
            signal.update({
                'action': 'buy',
                'type': 'CHoCH',
                'confidence': 0.8,
                'entry_price': df['close'].iloc[-1],
                'stop_loss': df['low'].iloc[-1] - df['atr'].iloc[-1],
                'take_profit': df['close'].iloc[-1] + df['atr'].iloc[-1] * 2
            })
            return signal
            
        if not pd.isna(df['pvtLo'].iloc[-1]) and df['low'].iloc[-1] < df['Dn'].iloc[-2]:
            signal.update({
                'action': 'sell',
                'type': 'CHoCH',
                'confidence': 0.8,
                'entry_price': df['close'].iloc[-1],
                'stop_loss': df['high'].iloc[-1] + df['atr'].iloc[-1],
                'take_profit': df['close'].iloc[-1] - df['atr'].iloc[-1] * 2
            })
            return signal
        
        # Verificar señales SMS (Small Market Structure)
        last_up = df['Up'].iloc[-resp:].max()
        last_dn = df['Dn'].iloc[-resp:].min()
        
        if df['close'].iloc[-1] > last_up and df['volume'].iloc[-1] > df['volume'].iloc[-resp:].mean():
            signal.update({
                'action': 'buy',
                'type': 'SMS',
                'confidence': 0.7,
                'entry_price': df['close'].iloc[-1],
                'stop_loss': last_dn,
                'take_profit': df['close'].iloc[-1] + (df['close'].iloc[-1] - last_dn)
            })
            return signal
            
        if df['close'].iloc[-1] < last_dn and df['volume'].iloc[-1] > df['volume'].iloc[-resp:].mean():
            signal.update({
                'action': 'sell',
                'type': 'SMS',
                'confidence': 0.7,
                'entry_price': df['close'].iloc[-1],
                'stop_loss': last_up,
                'take_profit': df['close'].iloc[-1] - (last_up - df['close'].iloc[-1])
            })
            return signal
        
        # Verificar señales de bloques de orden
        if self.config['use_order_blocks'] and 'order_blocks' in df:
            latest_block = df['order_blocks'].iloc[-1]
            if latest_block != 0:
                signal.update({
                    'action': 'buy' if latest_block > 0 else 'sell',
                    'type': 'order_block',
                    'confidence': 0.75,
                    'entry_price': df['close'].iloc[-1],
                    'stop_loss': df['low'].iloc[-1] - df['atr'].iloc[-1] if latest_block > 0 else df['high'].iloc[-1] + df['atr'].iloc[-1],
                    'take_profit': df['close'].iloc[-1] + df['atr'].iloc[-1] * 2 if latest_block > 0 else df['close'].iloc[-1] - df['atr'].iloc[-1] * 2
                })
                return signal
        
        return None
    
    def _check_trend_following_signal(self, latest: pd.Series, prev: pd.Series) -> bool:
        """Check for trend following signals"""
        # Check for moving average crossover
        ma_cross = (
            prev['ma_fast'] <= prev['ma_slow'] and 
            latest['ma_fast'] > latest['ma_slow']
        ) or (
            prev['ma_fast'] >= prev['ma_slow'] and 
            latest['ma_fast'] < latest['ma_slow']
        )
        
        # Check if price is above/below MA for trend confirmation
        trend_confirmation = (
            (latest['close'] > latest['ma_fast'] and latest['ma_fast'] > latest['ma_slow']) or
            (latest['close'] < latest['ma_fast'] and latest['ma_fast'] < latest['ma_slow'])
        )
        
        return ma_cross and trend_confirmation
    
    def _check_mean_reversion_signal(self, latest: pd.Series, prev: pd.Series) -> bool:
        """Check for mean reversion signals"""
        # Check RSI for overbought/oversold conditions
        rsi_signal = (
            (prev['rsi'] > self.config['rsi_oversold'] and latest['rsi'] <= self.config['rsi_oversold']) or
            (prev['rsi'] < self.config['rsi_overbought'] and latest['rsi'] >= self.config['rsi_overbought'])
        )
        
        # Check if price is at a support/resistance level
        price_action = (
            (latest['rsi'] <= self.config['rsi_oversold'] and latest['close'] > latest['open']) or  # Bullish reversal
            (latest['rsi'] >= self.config['rsi_overbought'] and latest['close'] < latest['open'])    # Bearish reversal
        )
        
        return rsi_signal and price_action
    
    def _calculate_confidence(self, data: pd.Series, signal_type: str) -> float:
        """Calculate confidence score for a signal (0-1)"""
        confidence = 0.5  # Base confidence
        
        if signal_type == 'trend':
            # Higher confidence with stronger trend and volume
            ma_diff = abs(data['ma_fast'] - data['ma_slow']) / data['close']
            confidence += min(0.3, ma_diff * 10)  # Up to 0.3 for MA spread
            
            if 'volume' in data and data['volume'] > 0:
                vol_ratio = data['volume'] / self.df['volume'].mean()
                confidence += min(0.2, vol_ratio * 0.1)  # Up to 0.2 for volume
                
        elif signal_type == 'mr':
            # Higher confidence with stronger RSI extreme
            rsi_extreme = (
                max(0, self.config['rsi_overbought'] - data['rsi']) / 
                (self.config['rsi_overbought'] - self.config['rsi_oversold'])
            )
            confidence += rsi_extreme * 0.5  # Up to 0.5 for RSI extreme
        
        return min(1.0, max(0.0, confidence))
    
    def calculate_position_size(self, entry_price: float, stop_loss: float, risk_amount: float) -> float:
        """
        Calculate position size based on risk parameters
        
        Args:
            entry_price: Entry price
            stop_loss: Stop loss price
            risk_amount: Amount to risk in account currency
            
        Returns:
            float: Position size in lots
        """
        if entry_price <= 0 or stop_loss <= 0 or risk_amount <= 0:
            return self.config['lot_size']  # Default to configured lot size
        
        # Calculate risk per unit
        risk_per_unit = abs(entry_price - stop_loss)
        if risk_per_unit == 0:
            return self.config['lot_size']  # Avoid division by zero
        
        # Get symbol info for contract size and pip value
        symbol_info = mt5.symbol_info(self.symbol)
        if symbol_info is None:
            return self.config['lot_size']
        
        contract_size = symbol_info.trade_contract_size
        tick_value = symbol_info.trade_tick_value
        tick_size = symbol_info.trade_tick_size
        
        # Calculate position size
        if tick_size > 0 and tick_value > 0:
            # Calculate position size based on ticks
            ticks_per_unit = risk_per_unit / tick_size
            risk_per_tick = ticks_per_unit * tick_value
            
            if risk_per_tick > 0:
                position_size = (risk_amount / risk_per_tick) * contract_size
                return round(position_size, 2)  # Round to 2 decimal places
        
        # Fallback to simple calculation if tick info is not available
        position_size = risk_amount / (risk_per_unit * contract_size)
        return round(max(0.01, min(100.0, position_size)), 2)  # Clamp between 0.01 and 100.0
    
    def calculate_risk_parameters(self, entry_price: float, direction: str) -> Dict[str, float]:
        """
        Calculate stop loss and take profit levels
        
        Args:
            entry_price: Entry price
            direction: 'buy' or 'sell'
            
        Returns:
            dict: Dictionary with 'stop_loss' and 'take_profit' prices
        """
        if self.df.empty:
            return {'stop_loss': 0.0, 'take_profit': 0.0}
        
        atr = self.df['atr'].iloc[-1] if not pd.isna(self.df['atr'].iloc[-1]) else 0.0
        
        if atr == 0:
            # Fallback to fixed percentage if ATR is not available
            if direction.lower() == 'buy':
                return {
                    'stop_loss': entry_price * 0.99,  # 1% stop loss
                    'take_profit': entry_price * 1.02  # 2% take profit
                }
            else:
                return {
                    'stop_loss': entry_price * 1.01,  # 1% stop loss
                    'take_profit': entry_price * 0.98  # 2% take profit
                }
        
        # Use ATR for dynamic stop loss and take profit
        if direction.lower() == 'buy':
            stop_loss = entry_price - (atr * self.config.get('sl_atr_multiplier', 1.5))
            take_profit = entry_price + (atr * self.config.get('tp_atr_multiplier', 3.0))
        else:
            stop_loss = entry_price + (atr * self.config.get('sl_atr_multiplier', 1.5))
            take_profit = entry_price - (atr * self.config.get('tp_atr_multiplier', 3.0))
        
        return {
            'stop_loss': max(0.0, stop_loss),
            'take_profit': max(0.0, take_profit)
        }
