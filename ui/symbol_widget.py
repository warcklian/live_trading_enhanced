from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGroupBox, QFormLayout,
    QLabel, QPushButton, QComboBox, QDoubleSpinBox, QSpinBox,
    QCheckBox, QTableWidget, QTableWidgetItem, QHeaderView, QSplitter,
    QTabWidget, QMessageBox
)
from PyQt6.QtCore import Qt, pyqtSignal, QTimer
from PyQt6.QtGui import QColor, QFont
from typing import Dict, List, Optional, Tuple
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from datetime import datetime, timedelta

from core.models import SymbolConfig
from core.strategy import TradingStrategy
from ui.chart_widget import ChartWidget

class SymbolWidget(QWidget):
    """Widget for trading a single symbol"""
    
    # Signals
    error_occurred = pyqtSignal(str)
    status_message = pyqtSignal(str)
    
    def __init__(self, symbol: str, mt5_client, parent=None, config=None):
        super().__init__(parent)
        self.symbol = symbol
        self.mt5_client = mt5_client
        self.config = config or {}
        self.strategy = None
        self.trading_active = False
        self.update_timer = QTimer()
        self.update_interval = 5000  # ms
        
        # Initialize UI
        self.init_ui()
        
        # Apply configuration if provided
        if self.config:
            self.apply_config()
        
        # Load symbol data
        self.load_symbol_data()
        
        # Connect signals
        self.update_timer.timeout.connect(self.update_data)
    
    def init_ui(self):
        """Initialize the UI components"""
        # Main layout
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(5, 5, 5, 5)
        
        # Create splitter for resizable panels
        splitter = QSplitter(Qt.Orientation.Vertical)
        
        # Top panel: Symbol info and controls
        top_panel = QWidget()
        top_layout = QHBoxLayout(top_panel)
        
        # Left side: Symbol info
        info_group = QGroupBox("Symbol Info")
        info_layout = QFormLayout()
        
        self.price_label = QLabel("-")
        self.price_label.setFont(QFont("Arial", 16, QFont.Weight.Bold))
        self.change_label = QLabel("-")
        
        info_layout.addRow("Price:", self.price_label)
        info_layout.addRow("Change:", self.change_label)
        info_group.setLayout(info_layout)
        
        # Middle: Trading controls
        control_group = QGroupBox("Trading Controls")
        control_layout = QVBoxLayout()
        
        # Strategy selection
        self.strategy_combo = QComboBox()
        self.strategy_combo.addItems(["SMC Strategy", "Mean Reversion", "Trend Following"])
        self.strategy_combo.setCurrentText("SMC Strategy")
        
        # Lot size
        self.lot_size_spin = QDoubleSpinBox()
        self.lot_size_spin.setRange(0.01, 100.0)
        self.lot_size_spin.setValue(self.config.get('lot_size', 0.1))
        self.lot_size_spin.setSingleStep(0.01)
        
        # Risk management
        self.risk_percent_spin = QDoubleSpinBox()
        self.risk_percent_spin.setRange(0.1, 10.0)
        risk_per_trade = self.config.get('risk_params', {}).get('risk_per_trade', 1.0)
        self.risk_percent_spin.setValue(risk_per_trade)
        self.risk_percent_spin.setSuffix("%")
        
        # Add to layout
        form_layout = QFormLayout()
        form_layout.addRow("Strategy:", self.strategy_combo)
        form_layout.addRow("Lot Size:", self.lot_size_spin)
        form_layout.addRow("Risk per Trade:", self.risk_percent_spin)
        
        # SMC Strategy specific controls (initially hidden)
        self.smc_group = QGroupBox("SMC Strategy Settings")
        smc_layout = QFormLayout()
        
        # Market Structure
        self.market_structure_combo = QComboBox()
        self.market_structure_combo.addItems(["Bullish", "Bearish", "Ranging"])
        
        # Order Block Settings
        self.ob_lookback_spin = QSpinBox()
        self.ob_lookback_spin.setRange(5, 100)
        self.ob_lookback_spin.setValue(20)
        
        # Fair Value Gap
        self.fvg_enabled = QCheckBox("Enable Fair Value Gap")
        self.fvg_enabled.setChecked(True)
        
        # Add to SMC layout
        smc_layout.addRow("Market Structure:", self.market_structure_combo)
        smc_layout.addRow("OB Lookback (bars):", self.ob_lookback_spin)
        smc_layout.addRow(self.fvg_enabled)
        
        self.smc_group.setLayout(smc_layout)
        self.smc_group.setVisible(False)  # Hide by default
        
        # Show/hide SMC settings based on strategy selection
        self.strategy_combo.currentTextChanged.connect(self.on_strategy_changed)
        
        # Add to main layout
        control_layout.addLayout(form_layout)
        control_layout.addWidget(self.smc_group)
        
        # Initialize strategy visibility
        self.on_strategy_changed(self.strategy_combo.currentText())
        
        # Buttons
        button_layout = QHBoxLayout()
        self.buy_button = QPushButton("BUY")
        self.sell_button = QPushButton("SELL")
        self.close_all_button = QPushButton("Close All")
        
        self.buy_button.setStyleSheet("background-color: #4CAF50; color: white; font-weight: bold;")
        self.sell_button.setStyleSheet("background-color: #F44336; color: white; font-weight: bold;")
        self.close_all_button.setStyleSheet("background-color: #FF9800; color: white;")
        
        button_layout.addWidget(self.buy_button)
        button_layout.addWidget(self.sell_button)
        button_layout.addWidget(self.close_all_button)
        
        control_layout.addLayout(form_layout)
        control_layout.addLayout(button_layout)
        control_group.setLayout(control_layout)
        
        # Right side: Position info
        position_group = QGroupBox("Positions")
        position_layout = QVBoxLayout()
        
        self.positions_table = QTableWidget(0, 5)
        self.positions_table.setHorizontalHeaderLabels(["ID", "Type", "Volume", "Entry", "P/L"])
        self.positions_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        
        position_layout.addWidget(self.positions_table)
        position_group.setLayout(position_layout)
        
        # Add to top panel
        top_layout.addWidget(info_group, 1)
        top_layout.addWidget(control_group, 2)
        top_layout.addWidget(position_group, 2)
        
        # Create chart widget
        self.chart_widget = ChartWidget()
        
        # Add to splitter
        splitter.addWidget(top_panel)
        splitter.addWidget(self.chart_widget)
        splitter.setSizes([200, 600])
        
        # Add splitter to main layout
        main_layout.addWidget(splitter)
        
        # Connect signals
        self.buy_button.clicked.connect(self.on_buy_clicked)
        self.sell_button.clicked.connect(self.on_sell_clicked)
        self.close_all_button.clicked.connect(self.on_close_all_clicked)
    
    def load_symbol_data(self):
        """Load initial data for the symbol"""
        try:
            # Get historical data
            timeframe = self.config.get('timeframe', 'M15')
            df = self.mt5_client.get_historical_data(
                self.symbol, 
                timeframe=timeframe,
                count=1000
            )
            
            if df is None or df.empty:
                raise Exception(f"No data available for {self.symbol}")
            
            # Calculate technical indicators
            df = self.calculate_indicators(df)
            
            # Initialize strategy
            self.strategy = TradingStrategy(self.symbol, df)
            
            # Update UI
            self.update_price_display()
            self.update_chart()
            self.update_positions()
            
            # Start update timer
            self.update_timer.start(self.update_interval)
            
        except Exception as e:
            self.error_occurred.emit(f"Error loading {self.symbol}: {str(e)}")
    
    def update_data(self):
        """Update symbol data"""
        if not self.trading_active:
            return
            
        try:
            # Update price
            self.update_price_display()
            
            # Run strategy
            if self.strategy:
                signal = self.strategy.check_signals()
                if signal:
                    self.handle_strategy_signal(signal)
            
            # Update positions
            self.update_positions()
            
        except Exception as e:
            self.error_occurred.emit(f"Error updating {self.symbol}: {str(e)}")
    
    def update_price_display(self):
        """Update the price display"""
        tick = self.mt5_client.get_live_price(self.symbol)
        if not tick:
            return
            
        current_price = tick['last']
        self.price_label.setText(f"{current_price:.5f}")
        
        # Update price color based on change
        if hasattr(self, 'last_price'):
            if current_price > self.last_price:
                self.price_label.setStyleSheet("color: #4CAF50;")
            elif current_price < self.last_price:
                self.price_label.setStyleSheet("color: #F44336;")
        
        self.last_price = current_price
    
    def update_chart(self):
        """Update the chart with latest data"""
        if not self.strategy or not hasattr(self.strategy, 'df') or self.strategy.df.empty:
            return
            
        try:
            # Get OHLC data
            df = self.strategy.df.tail(100)  # Last 100 candles
            
            # Create figure
            fig = go.Figure()
            
            # Add candlestick trace
            fig.add_trace(go.Candlestick(
                x=df.index,
                open=df['open'],
                high=df['high'],
                low=df['low'],
                close=df['close'],
                name='Price'
            ))
            
            # Add Order Blocks if exist
            if 'ob_bullish' in df.columns:
                bull_ob = df[~df['ob_bullish'].isna()]
                for idx, row in bull_ob.iterrows():
                    fig.add_shape(
                        type="rect",
                        x0=idx,
                        x1=idx + pd.Timedelta(hours=12),
                        y0=row['low'],
                        y1=row['high'],
                        fillcolor="green",
                        opacity=0.2,
                        line=dict(width=0)
                    )
            
            if 'ob_bearish' in df.columns:
                bear_ob = df[~df['ob_bearish'].isna()]
                for idx, row in bear_ob.iterrows():
                    fig.add_shape(
                        type="rect",
                        x0=idx,
                        x1=idx + pd.Timedelta(hours=12),
                        y0=row['low'],
                        y1=row['high'],
                        fillcolor="red",
                        opacity=0.2,
                        line=dict(width=0)
                    )
            
            # Add Liquidity Zones
            if 'liquidity_high' in df.columns:
                fig.add_trace(go.Scatter(
                    x=df.index,
                    y=df['liquidity_high'],
                    mode='markers',
                    marker=dict(symbol='star', size=12, color='orange'),
                    name='Supply Zone'
                ))
            
            if 'liquidity_low' in df.columns:
                fig.add_trace(go.Scatter(
                    x=df.index,
                    y=df['liquidity_low'],
                    mode='markers',
                    marker=dict(symbol='star', size=12, color='cyan'),
                    name='Demand Zone'
                ))
            
            # Add SMC Pivots
            if 'pvtHi' in df.columns:
                fig.add_trace(go.Scatter(
                    x=df.index,
                    y=df['pvtHi'],
                    mode='markers',
                    marker=dict(symbol='circle', size=8, color='yellow'),
                    name='Pivot High'
                ))
            
            if 'pvtLo' in df.columns:
                fig.add_trace(go.Scatter(
                    x=df.index,
                    y=df['pvtLo'],
                    mode='markers',
                    marker=dict(symbol='circle', size=8, color='purple'),
                    name='Pivot Low'
                ))
            
            # Add recent signals if they exist
            if hasattr(self.strategy, 'signals'):
                recent_signals = [s for s in self.strategy.signals if s[1] >= len(df) - 20]
                for signal in recent_signals:
                    label, idx, center, price, direction = signal
                    if idx < len(df):
                        color = 'green' if direction == 'bull' else 'red'
                        symbol = 'triangle-up' if direction == 'bull' else 'triangle-down'
                        
                        fig.add_trace(go.Scatter(
                            x=[df.index[idx]],
                            y=[price],
                            mode='markers',
                            marker=dict(symbol=symbol, size=12, color=color),
                            name=f"{label} {direction}",
                            showlegend=False
                        ))
            
            # Update layout
            fig.update_layout(
                title=f"{self.symbol} - {self.config.get('timeframe', 'M15')} - {datetime.now().strftime('%H:%M:%S')}",
                height=400,
                xaxis_title="Date",
                yaxis_title="Price",
                showlegend=True,
                legend=dict(
                    orientation="h",
                    yanchor="bottom",
                    y=1.02,
                    xanchor="right",
                    x=1,
                    bgcolor='rgba(44, 44, 44, 0.8)'
                ),
                template="plotly_dark",
                margin=dict(l=10, r=10, t=40, b=10),
                paper_bgcolor='#1e1e1e',
                plot_bgcolor='#1e1e1e',
                font=dict(color='white', size=10),
                xaxis=dict(
                    gridcolor='#444',
                    rangeslider=dict(visible=False),
                    type='date'
                ),
                yaxis=dict(
                    gridcolor='#444',
                    side='right'
                ),
                hovermode='x unified'
            )
            
            # Update chart using the correct method
            self.chart_widget.update_figure(fig)
            
        except Exception as e:
            self.error_occurred.emit(f"Error updating chart: {str(e)}")
    
    def update_positions(self):
        """Update the positions table"""
        try:
            positions = self.mt5_client.get_open_positions(self.symbol)
            
            # Clear table
            self.positions_table.setRowCount(0)
            
            # Add positions to table
            for pos in positions:
                row = self.positions_table.rowCount()
                self.positions_table.insertRow(row)
                
                # Set items
                self.positions_table.setItem(row, 0, QTableWidgetItem(str(pos['ticket'])))
                self.positions_table.setItem(row, 1, QTableWidgetItem(pos['type'].upper()))
                self.positions_table.setItem(row, 2, QTableWidgetItem(f"{pos['volume']:.2f}"))
                self.positions_table.setItem(row, 3, QTableWidgetItem(f"{pos['open_price']:.5f}"))
                
                # P/L with color coding
                pl_item = QTableWidgetItem(f"{pos['profit']:.2f}")
                if pos['profit'] > 0:
                    pl_item.setForeground(QColor('#4CAF50'))
                elif pos['profit'] < 0:
                    pl_item.setForeground(QColor('#F44336'))
                self.positions_table.setItem(row, 4, pl_item)
                
        except Exception as e:
            self.error_occurred.emit(f"Error updating positions: {str(e)}")
    
    def handle_strategy_signal(self, signal: dict):
        """Handle trading signal from strategy"""
        try:
            if signal['action'] == 'buy':
                self.place_order('buy', signal.get('volume', self.lot_size_spin.value()))
            elif signal['action'] == 'sell':
                self.place_order('sell', signal.get('volume', self.lot_size_spin.value()))
        except Exception as e:
            self.error_occurred.emit(f"Error handling signal: {str(e)}")
    
    def place_order(self, order_type: str, volume: float):
        """Place an order"""
        try:
            # Get current price
            tick = self.mt5_client.get_live_price(self.symbol)
            if not tick:
                raise Exception("Could not get current price")
            
            # Calculate SL/TP based on ATR or fixed values
            atr = self.strategy.get_atr() if hasattr(self.strategy, 'get_atr') else 0.0
            price = tick['ask'] if order_type == 'buy' else tick['bid']
            
            # Place order
            if order_type == 'buy':
                sl = price - (atr * 2) if atr > 0 else price * 0.995
                tp = price + (atr * 4) if atr > 0 else price * 1.01
            else:  # sell
                sl = price + (atr * 2) if atr > 0 else price * 1.005
                tp = price - (atr * 4) if atr > 0 else price * 0.99
            
            # Execute order
            self.mt5_client.place_order(
                symbol=self.symbol,
                order_type=order_type,
                volume=volume,
                sl=sl,
                tp=tp,
                comment="Auto-trade"
            )
            
            self.status_message.emit(f"{order_type.upper()} order placed for {self.symbol}")
            
        except Exception as e:
            self.error_occurred.emit(f"Error placing order: {str(e)}")
    
    def apply_config(self):
        """Apply configuration from the config dictionary"""
        # Apply basic settings
        if 'lot_size' in self.config:
            self.lot_size_spin.setValue(self.config['lot_size'])
            
        # Apply SMC strategy settings
        smc_params = self.config.get('smc_params', {})
        if smc_params:
            self.market_structure_combo.setCurrentText(smc_params.get('market_structure', 'Ranging').capitalize())
            self.ob_lookback_spin.setValue(smc_params.get('ob_lookback', 20))
            self.fvg_enabled.setChecked(smc_params.get('fvg_enabled', True))
        
        # Apply risk parameters
        risk_params = self.config.get('risk_params', {})
        if risk_params:
            self.risk_percent_spin.setValue(risk_params.get('risk_per_trade', 1.0))
    
    def on_strategy_changed(self, strategy_name):
        """Handle strategy selection change"""
        show_smc = (strategy_name == "SMC Strategy")
        self.smc_group.setVisible(show_smc)
    
    def initialize_strategy(self):
        """Initialize the trading strategy based on current settings"""
        strategy_name = self.strategy_combo.currentText()
        
        if strategy_name == "SMC Strategy":
            # Initialize SMC Strategy with current parameters
            smc_params = {
                'market_structure': self.market_structure_combo.currentText().lower(),
                'ob_lookback': self.ob_lookback_spin.value(),
                'fvg_enabled': self.fvg_enabled.isChecked(),
                # Add other SMC parameters here
            }
            # TODO: Initialize SMC strategy with these parameters
            # self.strategy = SMCStrategy(symbol=self.symbol, **smc_params)
            pass
        else:
            # Initialize other strategies
            pass
    
    def start_trading(self):
        """Start automated trading"""
        if not self.trading_active:
            # Initialize strategy with current settings
            self.initialize_strategy()
            self.trading_active = True
            self.update_timer.start(self.update_interval)
            self.status_message.emit(f"Started trading {self.symbol}")
    
    def stop_trading(self):
        """Stop automated trading"""
        self.trading_active = False
        self.status_message.emit(f"Stopped trading {self.symbol}")
    
    def refresh_data(self):
        """Refresh all data"""
        self.load_symbol_data()
    
    # --- Event Handlers ---
    def on_buy_clicked(self):
        """Handle buy button click"""
        self.place_order('buy', self.lot_size_spin.value())
    
    def on_sell_clicked(self):
        """Handle sell button click"""
        self.place_order('sell', self.lot_size_spin.value())
    
    def on_close_all_clicked(self):
        """Close all open positions"""
        try:
            positions = self.mt5_client.get_open_positions(self.symbol)
            for pos in positions:
                self.mt5_client.close_position(pos['ticket'])
            
            self.status_message.emit(f"Closed all positions for {self.symbol}")
            
        except Exception as e:
            self.error_occurred.emit(f"Error closing positions: {str(e)}")
    
    def calculate_indicators(self, df):
        """Calculate technical indicators for the chart and strategy"""
        try:
            # Calculate ATR
            df = self.calculate_atr(df)
            
            # Calculate Order Blocks
            df = self.identify_order_blocks(df)
            
            # Calculate Liquidity Zones
            df = self.identify_liquidity_zones(df)
            
            # Calculate SMC probability
            df = self.calculate_smc_probability(df)
            
            return df
        except Exception as e:
            self.error_occurred.emit(f"Error calculating indicators: {str(e)}")
            return df
    
    def calculate_atr(self, df, window=14):
        """Calculate Average True Range"""
        df = df.copy()
        df['tr'] = np.maximum(
            df['high'] - df['low'],
            np.maximum(
                abs(df['high'] - df['close'].shift(1)),
                abs(df['low'] - df['close'].shift(1))
            )
        )
        df['atr'] = df['tr'].rolling(window).mean()
        return df
    
    def identify_order_blocks(self, df, lookback=20):
        """Identify bullish and bearish order blocks"""
        df = df.copy()
        df['ob_bullish'] = np.nan
        df['ob_bearish'] = np.nan
        
        for i in range(lookback, len(df)):
            # Bullish Order Block
            if (df['close'].iloc[i-1] < df['open'].iloc[i-1] and 
                df['close'].iloc[i] > df['open'].iloc[i] and 
                df['close'].iloc[i] > df['high'].iloc[i-1]):
                df.iloc[i-1, df.columns.get_loc('ob_bullish')] = df['low'].iloc[i-1]
            
            # Bearish Order Block
            if (df['close'].iloc[i-1] > df['open'].iloc[i-1] and 
                df['close'].iloc[i] < df['open'].iloc[i] and 
                df['close'].iloc[i] < df['low'].iloc[i-1]):
                df.iloc[i-1, df.columns.get_loc('ob_bearish')] = df['high'].iloc[i-1]
        
        return df
    
    def identify_liquidity_zones(self, df, window=50):
        """Identify liquidity zones"""
        df = df.copy()
        df['recent_high'] = df['high'].rolling(window).max()
        df['recent_low'] = df['low'].rolling(window).min()
        
        df['liquidity_high'] = np.where(
            (df['high'] == df['recent_high']) & 
            (df['high'].shift(1) != df['recent_high'].shift(1)),
            df['high'], np.nan
        )
        
        df['liquidity_low'] = np.where(
            (df['low'] == df['recent_low']) & 
            (df['low'].shift(1) != df['recent_low'].shift(1)),
            df['low'], np.nan
        )
        
        return df
    
    def calculate_smc_probability(self, df, prd=20, resp=7, s1=True):
        """Calculate SMC probability and signals"""
        df = df.copy()
        
        # Calculate pivots
        df['Up'] = df['high'].rolling(prd).max()
        df['Dn'] = df['low'].rolling(prd).min()
        
        df['pvtHi'] = df['high'].rolling(2*prd+1, center=True).apply(
            lambda x: x[prd] if x[prd] == max(x) else np.nan, raw=True)
        df['pvtLo'] = df['low'].rolling(2*prd+1, center=True).apply(
            lambda x: x[prd] if x[prd] == min(x) else np.nan, raw=True)
        
        return df
    
    def closeEvent(self, event):
        """Handle widget close event"""
        self.stop_trading()
        self.update_timer.stop()
        event.accept()
