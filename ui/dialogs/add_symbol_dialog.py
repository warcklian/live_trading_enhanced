from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QFormLayout, QLabel, 
    QLineEdit, QComboBox, QDialogButtonBox, QDoubleSpinBox, 
    QSpinBox, QCheckBox, QGroupBox, QTabWidget, QWidget, QGridLayout,
    QPushButton, QMessageBox
)
from PyQt6.QtCore import Qt, pyqtSignal

class AddSymbolDialog(QWidget):
    """Widget for adding a new trading symbol with SMC strategy settings"""
    
    accepted = pyqtSignal(dict)  # Signal emitted when symbol is added
    rejected = pyqtSignal()       # Signal emitted when cancelled
    
    def __init__(self, parent=None, embedded=False, available_symbols=None):
        super().__init__(parent)
        self.embedded = embedded
        
        # Initialize available symbols first
        self._available_symbols = available_symbols if available_symbols else []
        print(f"AddSymbolDialog initialized with {len(self._available_symbols)} symbols")
        
        # Initialize UI components
        self.symbol_combo = None
        self.timeframe_combo = None
        self.lot_size_spin = None
        self.structure_combo = None
        self.ob_lookback_spin = None
        self.ob_strength_spin = None
        self.fvg_enabled = None
        self.fvg_lookback_spin = None
        self.entry_rsi_spin = None
        self.entry_volume_check = None
        self.take_profit_atr = None
        self.stop_loss_atr = None
        self.risk_per_trade = None
        self.max_daily_drawdown = None
        self.trailing_stop_check = None
        self.trailing_distance = None
        
        # Set minimum size
        self.setMinimumWidth(600)
        self.setMinimumHeight(500)
        
        # Initialize the UI
        self.setup_ui()
    
    @property
    def available_symbols(self):
        return self._available_symbols
    
    @available_symbols.setter
    def available_symbols(self, symbols):
        self._available_symbols = symbols if symbols else []
        if self.symbol_combo:
            self.symbol_combo.clear()
            if self._available_symbols:
                self.symbol_combo.addItems(self._available_symbols)
                self.symbol_combo.setCurrentIndex(0)
            else:
                print("Warning: No symbols available to add to combo box")
    
    def setup_ui(self):
        """Set up the UI components"""
        # Create main layout
        if self.layout() is not None:
            # Clear existing layout if it exists
            QWidget().setLayout(self.layout())
        
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(10, 10, 10, 10)
        
        # Create tab widget
        self.tab_widget = QTabWidget()
        
        # Create tabs
        self.basic_tab = self.create_basic_tab()
        self.smc_tab = self.create_smc_tab()
        self.risk_tab = self.create_risk_tab()
        
        # Add tabs to tab widget
        self.tab_widget.addTab(self.basic_tab, "Basic")
        self.tab_widget.addTab(self.smc_tab, "SMC Strategy")
        self.tab_widget.addTab(self.risk_tab, "Risk Management")
        
        main_layout.addWidget(self.tab_widget)
        
        # Create buttons container
        buttons_container = QWidget()
        buttons_layout = QHBoxLayout(buttons_container)
        
        # Add buttons
        add_button = QPushButton("Add Symbol")
        add_button.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
        """)
        add_button.clicked.connect(self.on_accept)
        
        cancel_button = QPushButton("Cancel")
        cancel_button.setStyleSheet("""
            QPushButton {
                background-color: #f44336;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #da190b;
            }
        """)
        cancel_button.clicked.connect(self.on_reject)
        
        buttons_layout.addWidget(add_button)
        buttons_layout.addWidget(cancel_button)
        main_layout.addWidget(buttons_container)
    
    def create_basic_tab(self):
        """Create the basic settings tab"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # Container widget for the form
        form_container = QWidget()
        form_layout = QFormLayout(form_container)
        form_layout.setFieldGrowthPolicy(QFormLayout.FieldGrowthPolicy.AllNonFixedFieldsGrow)
        form_layout.setLabelAlignment(Qt.AlignmentFlag.AlignLeft)
        
        # Symbol selection
        self.symbol_combo = QComboBox()
        print(f"Initializing symbol combo box. Available symbols: {len(self._available_symbols)}")
        if self._available_symbols:
            print(f"First few symbols: {self._available_symbols[:5]}")
            self.symbol_combo.addItems(self._available_symbols)
            self.symbol_combo.setCurrentIndex(0)
        else:
            print("Warning: No symbols available during combo box initialization")
        self.symbol_combo.setEditable(True)
        # Connect signal to track changes
        self.symbol_combo.currentTextChanged.connect(lambda text: print(f"Symbol selected: {text}"))
        
        # Timeframe
        self.timeframe_combo = QComboBox()
        self.timeframe_combo.addItems(["M1", "M5", "M15", "M30", "H1", "H4", "D1", "W1", "MN1"])
        self.timeframe_combo.setCurrentText("M15")
        
        # Lot size
        self.lot_size_spin = QDoubleSpinBox()
        self.lot_size_spin.setRange(0.01, 100.0)
        self.lot_size_spin.setValue(0.1)
        self.lot_size_spin.setSingleStep(0.01)
        self.lot_size_spin.setDecimals(2)
        
        # Add widgets to form
        form_layout.addRow("Symbol:", self.symbol_combo)
        form_layout.addRow("Timeframe:", self.timeframe_combo)
        form_layout.addRow("Lot Size:", self.lot_size_spin)
        
        # Add form to layout with stretch
        layout.addWidget(form_container)
        layout.addStretch()
        
        return tab
    
    def create_smc_tab(self):
        """Create the SMC strategy tab"""
        self.smc_tab = QWidget()
        layout = QVBoxLayout(self.smc_tab)
        
        # SMC Strategy Parameters
        params_group = QGroupBox("SMC Strategy Parameters")
        form_layout = QFormLayout()
        
        # Market Structure
        self.structure_combo = QComboBox()
        self.structure_combo.addItems(["Bullish", "Bearish", "Ranging"])
        
        # Order Block Settings
        self.ob_lookback_spin = QSpinBox()
        self.ob_lookback_spin.setRange(5, 100)
        self.ob_lookback_spin.setValue(20)
        
        self.ob_strength_spin = QDoubleSpinBox()
        self.ob_strength_spin.setRange(1.0, 5.0)
        self.ob_strength_spin.setValue(2.0)
        self.ob_strength_spin.setSingleStep(0.1)
        
        # Fair Value Gap Settings
        self.fvg_enabled = QCheckBox("Enable Fair Value Gap")
        self.fvg_enabled.setChecked(True)
        
        self.fvg_lookback_spin = QSpinBox()
        self.fvg_lookback_spin.setRange(3, 20)
        self.fvg_lookback_spin.setValue(5)
        
        # Add to form
        form_layout.addRow("Market Structure:", self.structure_combo)
        form_layout.addRow("Order Block Lookback (bars):", self.ob_lookback_spin)
        form_layout.addRow("Order Block Strength (ATR):", self.ob_strength_spin)
        form_layout.addRow(self.fvg_enabled)
        form_layout.addRow("FVG Lookback (bars):", self.fvg_lookback_spin)
        
        params_group.setLayout(form_layout)
        layout.addWidget(params_group)
        
        # Entry/Exit Rules
        rules_group = QGroupBox("Entry & Exit Rules")
        rules_layout = QFormLayout()
        
        # Entry Rules
        self.entry_rsi_spin = QSpinBox()
        self.entry_rsi_spin.setRange(20, 80)
        self.entry_rsi_spin.setValue(40)
        
        self.entry_volume_check = QCheckBox("Require Volume Confirmation")
        self.entry_volume_check.setChecked(True)
        
        # Exit Rules
        self.take_profit_atr = QDoubleSpinBox()
        self.take_profit_atr.setRange(0.5, 10.0)
        self.take_profit_atr.setValue(2.0)
        self.take_profit_atr.setSingleStep(0.1)
        
        self.stop_loss_atr = QDoubleSpinBox()
        self.stop_loss_atr.setRange(0.5, 5.0)
        self.stop_loss_atr.setValue(1.5)
        self.stop_loss_atr.setSingleStep(0.1)
        
        # Add to form
        rules_layout.addRow("Entry RSI Level:", self.entry_rsi_spin)
        rules_layout.addRow(self.entry_volume_check)
        rules_layout.addRow("Take Profit (ATR):", self.take_profit_atr)
        rules_layout.addRow("Stop Loss (ATR):", self.stop_loss_atr)
        
        rules_group.setLayout(rules_layout)
        layout.addWidget(rules_group)
        layout.addStretch()
        
        return self.smc_tab
    
    def create_risk_tab(self):
        """Create the risk management tab"""
        self.risk_tab = QWidget()
        layout = QVBoxLayout(self.risk_tab)
        
        # Risk per trade
        risk_group = QGroupBox("Position Sizing")
        risk_layout = QFormLayout()
        
        self.risk_per_trade = QDoubleSpinBox()
        self.risk_per_trade.setRange(0.1, 10.0)
        self.risk_per_trade.setValue(1.0)
        self.risk_per_trade.setSuffix("%")
        self.risk_per_trade.setSingleStep(0.1)
        
        self.max_daily_drawdown = QDoubleSpinBox()
        self.max_daily_drawdown.setRange(1.0, 20.0)
        self.max_daily_drawdown.setValue(5.0)
        self.max_daily_drawdown.setSuffix("%")
        
        # Add to form
        risk_layout.addRow("Risk per Trade (%):", self.risk_per_trade)
        risk_layout.addRow("Max Daily Drawdown (%):", self.max_daily_drawdown)
        
        risk_group.setLayout(risk_layout)
        layout.addWidget(risk_group)
        
        # Exit Settings
        exit_group = QGroupBox("Exit Settings")
        exit_layout = QFormLayout()
        
        # Trailing stop
        self.trailing_stop_check = QCheckBox("Use Trailing Stop")
        self.trailing_stop_check.setChecked(True)
        
        self.trailing_distance = QDoubleSpinBox()
        self.trailing_distance.setRange(0.5, 5.0)
        self.trailing_distance.setValue(1.5)
        self.trailing_distance.setSingleStep(0.1)
        self.trailing_distance.setSuffix(" ATR")
        
        # Break even
        self.break_even_check = QCheckBox("Use Break Even")
        self.break_even_check.setChecked(True)
        
        self.break_even_atr = QDoubleSpinBox()
        self.break_even_atr.setRange(0.5, 5.0)
        self.break_even_atr.setValue(1.0)
        self.break_even_atr.setSingleStep(0.1)
        self.break_even_atr.setSuffix(" ATR")
        
        # Add to exit layout
        exit_layout.addRow(self.trailing_stop_check)
        exit_layout.addRow("Trailing Stop Distance:", self.trailing_distance)
        exit_layout.addRow(self.break_even_check)
        exit_layout.addRow("Break Even Distance:", self.break_even_atr)
        
        exit_group.setLayout(exit_layout)
        layout.addWidget(exit_group)
        
        # Advanced Risk Settings
        advanced_group = QGroupBox("Advanced Risk Settings")
        adv_layout = QFormLayout()
        
        self.max_open_trades = QSpinBox()
        self.max_open_trades.setRange(1, 20)
        self.max_open_trades.setValue(5)
        
        self.max_position_size = QDoubleSpinBox()
        self.max_position_size.setRange(0.1, 100.0)
        self.max_position_size.setValue(10.0)
        self.max_position_size.setSuffix(" lots")
        
        # Add to form
        adv_layout.addRow("Max Open Trades:", self.max_open_trades)
        adv_layout.addRow("Max Position Size:", self.max_position_size)
        
        advanced_group.setLayout(adv_layout)
        layout.addWidget(advanced_group)
        layout.addStretch()
        
        return self.risk_tab
    
    def on_accept(self):
        """Handle accept button"""
        # Validate inputs
        if not self.validate_inputs():
            return
            
        # Get the settings
        settings = self.get_settings()
        if settings and 'symbol' in settings and settings['symbol']:
            self.accepted.emit(settings)
            
        if not self.embedded:
            self.close()
            
    def validate_inputs(self) -> bool:
        """Validate the form inputs"""
        if not self.get_selected_symbol():
            QMessageBox.warning(self, "Validation Error", "Please select a symbol")
            return False
            
        # Add any additional validation here
        return True
    
    def on_reject(self):
        """Handle cancel button"""
        self.rejected.emit()
        if not self.embedded:
            self.close()
    
    def get_selected_symbol(self) -> str:
        """Get the currently selected symbol"""
        if not self.symbol_combo:
            return None
        return self.symbol_combo.currentText().strip()

    def get_settings(self) -> dict:
        """Get all settings as a dictionary"""
        if not self.validate_inputs():
            return None
            
        return {
            'symbol': self.get_selected_symbol(),
            'timeframe': self.timeframe_combo.currentText(),
            'lot_size': self.lot_size_spin.value(),
            'smc_params': {
                'market_structure': self.structure_combo.currentText().lower(),
                'ob_lookback': self.ob_lookback_spin.value(),
                'ob_strength': self.ob_strength_spin.value(),
                'fvg_enabled': self.fvg_enabled.isChecked(),
                'fvg_lookback': self.fvg_lookback_spin.value(),
                'entry_rsi': self.entry_rsi_spin.value(),
                'require_volume': self.entry_volume_check.isChecked(),
                'take_profit_atr': self.take_profit_atr.value(),
                'stop_loss_atr': self.stop_loss_atr.value()
            },
            'risk_params': {
                'risk_per_trade': self.risk_per_trade.value(),
                'max_daily_drawdown': self.max_daily_drawdown.value(),
                'max_open_trades': self.max_open_trades.value(),
                'max_position_size': self.max_position_size.value()
            },
            'exit_params': {
                'use_trailing_stop': self.trailing_stop_check.isChecked(),
                'trailing_distance': self.trailing_distance.value(),
                'use_break_even': self.break_even_check.isChecked(),
                'break_even_distance': self.break_even_atr.value()
            }
        }
