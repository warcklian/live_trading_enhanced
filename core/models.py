from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import List, Dict, Optional, Any
import pandas as pd

class OrderType(str, Enum):
    """Order types"""
    MARKET = "MARKET"
    LIMIT = "LIMIT"
    STOP = "STOP"
    STOP_LIMIT = "STOP_LIMIT"
    MARKET_IF_TOUCHED = "MARKET_IF_TOUCHED"

class OrderSide(str, Enum):
    """Order sides"""
    BUY = "BUY"
    SELL = "SELL"

class OrderStatus(str, Enum):
    """Order statuses"""
    NEW = "NEW"
    PARTIALLY_FILLED = "PARTIALLY_FILLED"
    FILLED = "FILLED"
    CANCELED = "CANCELED"
    REJECTED = "REJECTED"
    EXPIRED = "EXPIRED"

class PositionSide(str, Enum):
    """Position sides"""
    LONG = "LONG"
    SHORT = "SHORT"

class TimeInForce(str, Enum):
    """Time in force options"""
    GTC = "GTC"  # Good Till Cancel
    IOC = "IOC"  # Immediate or Cancel
    FOK = "FOK"  # Fill or Kill
    GTD = "GTD"  # Good Till Date

@dataclass
class SymbolConfig:
    """Configuration for a trading symbol"""
    symbol: str
    timeframe: str = "15m"
    enabled: bool = True
    lot_size: float = 0.1
    risk_per_trade: float = 1.0  # Percentage of balance to risk per trade
    use_trailing_stop: bool = True
    trailing_stop_atr_multiplier: float = 1.5
    use_break_even: bool = True
    break_even_atr_multiplier: float = 1.0
    max_trades_per_day: int = 5
    max_drawdown_pct: float = 5.0
    strategy_params: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            'symbol': self.symbol,
            'timeframe': self.timeframe,
            'enabled': self.enabled,
            'lot_size': self.lot_size,
            'risk_per_trade': self.risk_per_trade,
            'use_trailing_stop': self.use_trailing_stop,
            'trailing_stop_atr_multiplier': self.trailing_stop_atr_multiplier,
            'use_break_even': self.use_break_even,
            'break_even_atr_multiplier': self.break_even_atr_multiplier,
            'max_trades_per_day': self.max_trades_per_day,
            'max_drawdown_pct': self.max_drawdown_pct,
            'strategy_params': self.strategy_params
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'SymbolConfig':
        """Create from dictionary"""
        return cls(**data)

@dataclass
class Order:
    """Represents a trading order"""
    order_id: str
    symbol: str
    side: OrderSide
    order_type: OrderType
    quantity: float
    price: float
    stop_price: Optional[float] = None
    time_in_force: TimeInForce = TimeInForce.GTC
    status: OrderStatus = OrderStatus.NEW
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    filled_quantity: float = 0.0
    average_fill_price: Optional[float] = None
    client_order_id: Optional[str] = None
    comment: str = ""
    
    def is_filled(self) -> bool:
        """Check if the order is fully filled"""
        return self.status == OrderStatus.FILLED

@dataclass
class PendingSignal:
    """Representa una señal de trading pendiente de ejecución"""
    signal_type: str  # CHoCH, SMS, BMS, OrderBlock
    direction: str    # buy, sell
    entry_price: float
    stop_loss: float
    take_profit: float
    timestamp: datetime
    atr: float
    symbol: str
    confidence: float
    volume: Optional[float] = None
    executed: bool = False
    order_ticket: Optional[int] = None
    expiry: Optional[datetime] = None
    
    def is_valid(self, current_price: float, current_time: datetime) -> bool:
        """Verifica si la señal sigue siendo válida"""
        # Verificar si la señal ha expirado
        if self.expiry and current_time > self.expiry:
            return False
            
        # Verificar si el precio sigue siendo válido (dentro de un rango del ATR)
        price_diff = abs(current_price - self.entry_price)
        max_diff = self.atr * 1.5  # Usar 1.5 ATR como máximo rango válido
        
        return price_diff <= max_diff
    
    def calculate_risk_reward(self) -> float:
        """Calcula el ratio riesgo/beneficio de la señal"""
        if self.direction == 'buy':
            risk = self.entry_price - self.stop_loss
            reward = self.take_profit - self.entry_price
        else:  # sell
            risk = self.stop_loss - self.entry_price
            reward = self.entry_price - self.take_profit
            
        return abs(reward / risk) if risk != 0 else 0
    
    def is_active(self) -> bool:
        """Check if the order is active (not filled, canceled, or rejected)"""
        return self.status in [OrderStatus.NEW, OrderStatus.PARTIALLY_FILLED]

@dataclass
class Position:
    """Represents an open position"""
    position_id: str
    symbol: str
    side: PositionSide
    quantity: float
    entry_price: float
    current_price: float
    unrealized_pnl: float = 0.0
    realized_pnl: float = 0.0
    stop_loss: Optional[float] = None
    take_profit: Optional[float] = None
    opened_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    leverage: float = 1.0
    margin: float = 0.0
    comment: str = ""
    
    def update_price(self, price: float) -> None:
        """Update the current price and recalculate P&L"""
        self.current_price = price
        price_diff = price - self.entry_price if self.side == PositionSide.LONG else self.entry_price - price
        self.unrealized_pnl = price_diff * self.quantity
        self.updated_at = datetime.utcnow()
    
    def close(self, price: Optional[float] = None) -> float:
        """Close the position and return the realized P&L"""
        if price is not None:
            self.current_price = price
        
        price_diff = self.current_price - self.entry_price if self.side == PositionSide.LONG else self.entry_price - self.current_price
        self.realized_pnl = price_diff * self.quantity
        self.unrealized_pnl = 0.0
        self.quantity = 0.0
        self.updated_at = datetime.utcnow()
        
        return self.realized_pnl

@dataclass
class Trade:
    """Represents a completed trade (entry + exit)"""
    trade_id: str
    symbol: str
    side: PositionSide
    quantity: float
    entry_price: float
    exit_price: float
    entry_time: datetime
    exit_time: datetime
    pnl: float
    pnl_pct: float
    commission: float = 0.0
    swap: float = 0.0
    comment: str = ""
    strategy: Optional[str] = None
    tags: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            'trade_id': self.trade_id,
            'symbol': self.symbol,
            'side': self.side.value,
            'quantity': self.quantity,
            'entry_price': self.entry_price,
            'exit_price': self.exit_price,
            'entry_time': self.entry_time.isoformat(),
            'exit_time': self.exit_time.isoformat(),
            'pnl': self.pnl,
            'pnl_pct': self.pnl_pct,
            'commission': self.commission,
            'swap': self.swap,
            'comment': self.comment,
            'strategy': self.strategy,
            'tags': self.tags
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Trade':
        """Create from dictionary"""
        return cls(
            trade_id=data['trade_id'],
            symbol=data['symbol'],
            side=PositionSide(data['side']),
            quantity=data['quantity'],
            entry_price=data['entry_price'],
            exit_price=data['exit_price'],
            entry_time=datetime.fromisoformat(data['entry_time']),
            exit_time=datetime.fromisoformat(data['exit_time']),
            pnl=data['pnl'],
            pnl_pct=data['pnl_pct'],
            commission=data.get('commission', 0.0),
            swap=data.get('swap', 0.0),
            comment=data.get('comment', ''),
            strategy=data.get('strategy'),
            tags=data.get('tags', [])
        )

@dataclass
class AccountInfo:
    """Account information"""
    account_id: str
    balance: float
    equity: float
    margin: float
    free_margin: float
    margin_level: float
    leverage: int
    currency: str = "USD"
    
    @property
    def used_margin(self) -> float:
        """Calculate used margin"""
        return self.margin
    
    @property
    def margin_used_pct(self) -> float:
        """Calculate margin used as a percentage of equity"""
        if self.equity == 0:
            return 0.0
        return (self.used_margin / self.equity) * 100.0

@dataclass
class Candle:
    """Price candle data"""
    symbol: str
    timeframe: str
    timestamp: datetime
    open: float
    high: float
    low: float
    close: float
    volume: float = 0.0
    spread: float = 0.0
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            'symbol': self.symbol,
            'timeframe': self.timeframe,
            'timestamp': self.timestamp.isoformat(),
            'open': self.open,
            'high': self.high,
            'low': self.low,
            'close': self.close,
            'volume': self.volume,
            'spread': self.spread
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Candle':
        """Create from dictionary"""
        return cls(
            symbol=data['symbol'],
            timeframe=data['timeframe'],
            timestamp=datetime.fromisoformat(data['timestamp']),
            open=data['open'],
            high=data['high'],
            low=data['low'],
            close=data['close'],
            volume=data.get('volume', 0.0),
            spread=data.get('spread', 0.0)
        )
    
    def to_pandas_series(self) -> pd.Series:
        """Convert to pandas Series"""
        return pd.Series({
            'open': self.open,
            'high': self.high,
            'low': self.low,
            'close': self.close,
            'volume': self.volume,
            'spread': self.spread
        }, name=self.timestamp)
