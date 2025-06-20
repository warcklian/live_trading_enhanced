"""
Enhanced Risk Management System

This module provides risk management functionality for trading operations,
including position sizing, stop loss/take profit calculation, and risk assessment.
"""
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple
import numpy as np
import pandas as pd
from datetime import datetime

@dataclass
class RiskParameters:
    """Parameters for risk management calculations."""
    account_balance: float = 10000.0
    risk_per_trade: float = 1.0  # percentage of account to risk per trade
    max_position_size: float = 10.0  # in lots
    max_daily_drawdown: float = 5.0  # percentage
    daily_loss_limit: float = 2.0  # percentage
    use_atr: bool = True
    atr_period: int = 14
    atr_multiplier: float = 2.0
    default_risk_reward: float = 2.0
    max_open_positions: int = 10

@dataclass
class PositionRisk:
    """Risk assessment for a single position."""
    symbol: str
    entry_price: float
    position_size: float  # in lots
    stop_loss: float
    take_profit: float
    risk_amount: float
    reward_amount: float
    risk_reward_ratio: float
    atr_value: Optional[float] = None
    pip_value: Optional[float] = None
    margin_required: Optional[float] = None

class EnhancedRiskManager:
    """
    Enhanced risk management system that handles position sizing, stop loss,
    take profit, and other risk-related calculations.
    """
    
    def __init__(self, parameters: Optional[RiskParameters] = None):
        """
        Initialize the risk manager with the given parameters.
        
        Args:
            parameters: Risk management parameters. If None, defaults will be used.
        """
        self.parameters = parameters or RiskParameters()
        self.daily_pnl = 0.0
        self.trades_today = 0
        self.open_positions: List[PositionRisk] = []
        self._reset_daily_stats()
    
    def _reset_daily_stats(self) -> None:
        """Reset daily statistics at the start of a new trading day."""
        self.daily_pnl = 0.0
        self.trades_today = 0
    
    def calculate_position_size(
        self,
        symbol: str,
        entry_price: float,
        stop_loss: float,
        account_risk: Optional[float] = None,
        atr_value: Optional[float] = None
    ) -> PositionRisk:
        """
        Calculate the optimal position size based on risk parameters.
        
        Args:
            symbol: Trading symbol
            entry_price: Entry price for the position
            stop_loss: Stop loss price
            account_risk: Optional override for account risk percentage
            atr_value: Optional ATR value for volatility-based sizing
            
        Returns:
            PositionRisk: Calculated position risk parameters
        """
        if account_risk is None:
            account_risk = self.parameters.risk_per_trade
            
        # Calculate risk amount in account currency
        risk_amount = (self.parameters.account_balance * account_risk) / 100.0
        
        # Calculate position size based on stop loss
        if atr_value is not None and self.parameters.use_atr:
            # Use ATR for position sizing if available
            stop_distance = atr_value * self.parameters.atr_multiplier
            pip_value = self._calculate_pip_value(symbol, entry_price)
            risk_per_lot = stop_distance * pip_value * 10  # 10 is standard lot size multiplier
            
            if risk_per_lot > 0:
                position_size = min(
                    risk_amount / risk_per_lot,
                    self.parameters.max_position_size
                )
            else:
                position_size = 0.1  # Default minimum position size
        else:
            # Simple percentage-based position sizing
            risk_per_share = abs(entry_price - stop_loss)
            if risk_per_share > 0:
                position_size = min(
                    risk_amount / risk_per_share,
                    self.parameters.max_position_size
                )
            else:
                position_size = 0.1  # Default minimum position size
        
        # Calculate take profit based on risk/reward ratio
        if entry_price > stop_loss:  # Long position
            take_profit = entry_price + (entry_price - stop_loss) * self.parameters.default_risk_reward
        else:  # Short position
            take_profit = entry_price - (stop_loss - entry_price) * self.parameters.default_risk_reward
        
        # Create and return position risk assessment
        position_risk = PositionRisk(
            symbol=symbol,
            entry_price=entry_price,
            position_size=position_size,
            stop_loss=stop_loss,
            take_profit=take_profit,
            risk_amount=risk_amount,
            reward_amount=risk_amount * self.parameters.default_risk_reward,
            risk_reward_ratio=self.parameters.default_risk_reward,
            atr_value=atr_value
        )
        
        return position_risk
    
    def check_daily_limits(self) -> Tuple[bool, str]:
        """
        Check if daily trading limits have been reached.
        
        Returns:
            Tuple of (can_trade, reason)
        """
        # Check daily drawdown
        if self.daily_pnl < 0 and abs(self.daily_pnl) >= (self.parameters.account_balance * self.parameters.daily_loss_limit / 100):
            return False, f"Daily loss limit of {self.parameters.daily_loss_limit}% reached"
        
        # Check max open positions
        if len(self.open_positions) >= self.parameters.max_open_positions:
            return False, f"Maximum open positions ({self.parameters.max_open_positions}) reached"
        
        return True, ""
    
    def update_position(self, position: PositionRisk, current_price: float) -> None:
        """
        Update position with current price and check if risk limits are still valid.
        
        Args:
            position: Position to update
            current_price: Current market price
        """
        # Update position metrics
        if position.entry_price < position.stop_loss:  # Short position
            position.risk_amount = (position.entry_price - current_price) * position.position_size
            position.reward_amount = (position.entry_price - position.take_profit) * position.position_size
        else:  # Long position
            position.risk_amount = (current_price - position.entry_price) * position.position_size
            position.reward_amount = (position.take_profit - position.entry_price) * position.position_size
        
        # Update risk/reward ratio
        if position.risk_amount != 0:
            position.risk_reward_ratio = abs(position.reward_amount / position.risk_amount)
    
    def adjust_trailing_stop(
        self,
        position: PositionRisk,
        current_price: float,
        atr_value: Optional[float] = None
    ) -> bool:
        """
        Adjust trailing stop for a position.
        
        Args:
            position: Position to adjust
            current_price: Current market price
            atr_value: Optional ATR value for dynamic trailing stop
            
        Returns:
            bool: True if stop was adjusted, False otherwise
        """
        if atr_value is None:
            atr_value = position.atr_value or 0
        
        if position.entry_price < position.stop_loss:  # Short position
            new_stop = current_price + (atr_value * self.parameters.atr_multiplier)
            if new_stop < position.stop_loss:  # Only move stop down for short
                position.stop_loss = new_stop
                return True
        else:  # Long position
            new_stop = current_price - (atr_value * self.parameters.atr_multiplier)
            if new_stop > position.stop_loss:  # Only move stop up for long
                position.stop_loss = new_stop
                return True
                
        return False
    
    def _calculate_pip_value(self, symbol: str, price: float) -> float:
        """
        Calculate the pip value for a symbol.
        
        Args:
            symbol: Trading symbol
            price: Current price
            
        Returns:
            Pip value in account currency
        """
        # This is a simplified version - in a real application, you would
        # need to handle different currency pairs and account currencies
        if 'JPY' in symbol:
            return 0.01  # For JPY pairs, 1 pip is 0.01
        return 0.0001  # For most other pairs, 1 pip is 0.0001
    
    def on_trade_opened(self, position: PositionRisk) -> None:
        """
        Call this when a new trade is opened.
        
        Args:
            position: The opened position
        """
        self.open_positions.append(position)
        self.trades_today += 1
    
    def on_trade_closed(self, position: PositionRisk, pnl: float) -> None:
        """
        Call this when a trade is closed.
        
        Args:
            position: The closed position
            pnl: Profit/loss from the trade
        """
        if position in self.open_positions:
            self.open_positions.remove(position)
        self.daily_pnl += pnl
    
    def get_risk_summary(self) -> Dict[str, float]:
        """
        Get a summary of current risk metrics.
        
        Returns:
            Dictionary with risk metrics
        """
        total_risk = sum(pos.risk_amount for pos in self.open_positions)
        total_margin = sum(pos.margin_required or 0 for pos in self.open_positions)
        
        return {
            'open_positions': len(self.open_positions),
            'total_risk': total_risk,
            'total_margin': total_margin,
            'daily_pnl': self.daily_pnl,
            'trades_today': self.trades_today,
            'account_balance': self.parameters.account_balance,
            'equity': self.parameters.account_balance + self.daily_pnl
        }
