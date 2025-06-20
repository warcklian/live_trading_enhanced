import os
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QTabWidget, QGroupBox, QFormLayout, QCheckBox, 
    QSpinBox, QDialogButtonBox, QPushButton, QFileDialog, QLineEdit, QLabel,
    QMessageBox, QListWidget, QDoubleSpinBox, QWidget, QFrame
)
from PyQt6.QtCore import Qt, pyqtSignal, QSettings as QtCoreQSettings
from config.settings import Settings

class SettingsDialog(QWidget):
    """Settings widget that can be used both as a dialog and embedded in another widget"""
    settings_updated = pyqtSignal(dict)  # Signal to emit when settings are saved
    finished = pyqtSignal()  # Signal to emit when dialog is closed
    
    def __init__(self, parent=None, embedded=False):
        super().__init__(parent)
        self.settings = Settings()
        self.embedded = embedded
        
        if not self.embedded:
            self.setWindowTitle("Settings")
            self.setMinimumWidth(600)
            self.setMinimumHeight(500)
        
        # Create main layout and tab widget
        layout = QVBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)
        
        self.tabs = QTabWidget()
        
        # Create tabs
        self.create_general_tab()
        self.create_risk_tab()
        self.create_strategies_tab()
        
        # Add tabs to tab widget
        self.tabs.addTab(self.general_tab, "General")
        self.tabs.addTab(self.risk_tab, "Risk Management")
        self.tabs.addTab(self.strategies_tab, "Strategies")
        
        # Create buttons
        button_layout = QHBoxLayout()
        
        self.save_btn = QPushButton("Save")
        self.save_btn.clicked.connect(self.save_settings)
        
        self.cancel_btn = QPushButton("Cancel")
        self.cancel_btn.clicked.connect(self.on_cancel)
        
        self.defaults_btn = QPushButton("Restore Defaults")
        self.defaults_btn.clicked.connect(self.restore_defaults)
        
        button_layout.addStretch()
        button_layout.addWidget(self.defaults_btn)
        button_layout.addWidget(self.cancel_btn)
        button_layout.addWidget(self.save_btn)
        
        # Add widgets to layout
        layout.addWidget(self.tabs)
        layout.addLayout(button_layout)
        
        # Load current settings
        self.load_current_settings()
        
    def create_general_tab(self):
        """Create the General settings tab"""
        self.general_tab = QWidget()
        layout = QVBoxLayout(self.general_tab)
        
        # MT5 Settings
        mt5_group = QGroupBox("MT5 Settings")
        mt5_layout = QFormLayout()
        
        # MT5 Path
        self.mt5_path_edit = QLineEdit()
        self.mt5_browse_btn = QPushButton("Browse...")
        self.mt5_browse_btn.clicked.connect(self.browse_mt5_path)
        
        path_layout = QHBoxLayout()
        path_layout.addWidget(self.mt5_path_edit)
        path_layout.addWidget(self.mt5_browse_btn)
        
        mt5_layout.addRow("MT5 Terminal Path:", path_layout)
        
        # Data Directory
        self.data_dir_edit = QLineEdit()
        self.data_dir_browse_btn = QPushButton("Browse...")
        self.data_dir_browse_btn.clicked.connect(self.browse_data_dir)
        
        dir_layout = QHBoxLayout()
        dir_layout.addWidget(self.data_dir_edit)
        dir_layout.addWidget(self.data_dir_browse_btn)
        
        mt5_layout.addRow("Data Directory:", dir_layout)
        mt5_group.setLayout(mt5_layout)
        
        # Connection settings
        conn_group = QGroupBox("Connection Settings")
        conn_layout = QFormLayout()

        self.auto_reconnect = QCheckBox("Auto-reconnect on disconnection")
        self.auto_reconnect.setChecked(True)

        self.reconnect_attempts = QSpinBox()
        self.reconnect_attempts.setRange(1, 100)
        self.reconnect_attempts.setValue(5)

        self.reconnect_delay = QSpinBox()
        self.reconnect_delay.setRange(1, 60)
        self.reconnect_delay.setValue(5)
        self.reconnect_delay.setSuffix(" seconds")

        conn_layout.addRow(self.auto_reconnect)
        conn_layout.addRow("Max Reconnect Attempts:", self.reconnect_attempts)
        conn_layout.addRow("Reconnect Delay:", self.reconnect_delay)
        conn_group.setLayout(conn_layout)
                
        # Add to layout
        layout.addWidget(mt5_group)
        layout.addWidget(conn_group)
        layout.addStretch()
    def create_risk_tab(self):
        """Create the Risk Management settings tab"""
        self.risk_tab = QWidget()
        layout = QVBoxLayout(self.risk_tab)
        
        # Position Sizing
        sizing_group = QGroupBox("Position Sizing")
        sizing_layout = QFormLayout()
        
        self.risk_per_trade = QDoubleSpinBox()
        self.risk_per_trade.setRange(0.1, 10.0)
        self.risk_per_trade.setValue(1.0)
        self.risk_per_trade.setSuffix("%")
        
        self.max_positions = QSpinBox()
        self.max_positions.setRange(1, 100)
        self.max_positions.setValue(10)
        
        self.max_position_size = QDoubleSpinBox()
        self.max_position_size.setRange(0.01, 100.0)
        self.max_position_size.setValue(10.0)
        self.max_position_size.setSuffix(" lots")
        
        sizing_layout.addRow("Risk per Trade (%):", self.risk_per_trade)
        sizing_layout.addRow("Max Open Positions:", self.max_positions)
        sizing_layout.addRow("Max Position Size:", self.max_position_size)
        sizing_group.setLayout(sizing_layout)
        
        # Stop Loss & Take Profit
        sltp_group = QGroupBox("Stop Loss & Take Profit")
        sltp_layout = QFormLayout()
        
        self.use_atr_sl = QCheckBox("Use ATR for Stop Loss")
        self.use_atr_sl.setChecked(True)
        
        self.atr_multiplier = QDoubleSpinBox()
        self.atr_multiplier.setRange(0.5, 10.0)
        self.atr_multiplier.setValue(2.0)
        self.atr_multiplier.setSingleStep(0.1)
        
        self.default_risk_reward = QDoubleSpinBox()
        self.default_risk_reward.setRange(1.0, 10.0)
        self.default_risk_reward.setValue(2.0)
        self.default_risk_reward.setSingleStep(0.1)
        
        sltp_layout.addRow(self.use_atr_sl)
        sltp_layout.addRow("ATR Multiplier:", self.atr_multiplier)
        sltp_layout.addRow("Default Risk/Reward:", self.default_risk_reward)
        sltp_group.setLayout(sltp_layout)
        
        # Daily Limits
        limits_group = QGroupBox("Daily Trading Limits")
        limits_layout = QFormLayout()
        
        self.daily_loss_limit = QDoubleSpinBox()
        self.daily_loss_limit.setRange(1.0, 50.0)
        self.daily_loss_limit.setValue(5.0)
        self.daily_loss_limit.setSuffix("%")
        
        self.max_daily_trades = QSpinBox()
        self.max_daily_trades.setRange(1, 1000)
        self.max_daily_trades.setValue(50)
        
        limits_layout.addRow("Daily Loss Limit:", self.daily_loss_limit)
        limits_layout.addRow("Max Daily Trades:", self.max_daily_trades)
        limits_group.setLayout(limits_layout)
        
        # Add to layout
        layout.addWidget(sizing_group)
        layout.addWidget(sltp_group)
        layout.addWidget(limits_group)
        layout.addStretch()
    
    def create_strategies_tab(self):
        """Create the Strategies settings tab"""
        self.strategies_tab = QWidget()
        layout = QVBoxLayout(self.strategies_tab)
        
        # Available strategies list
        self.strategies_list = QListWidget()
        self.strategies_list.addItems(["SMC Strategy", "Moving Average Crossover", "RSI Divergence"])
        self.strategies_list.setCurrentRow(0)
        
        # Strategy parameters
        self.strategy_params = QWidget()
        self.strategy_params_layout = QFormLayout(self.strategy_params)
        
        # Add sample parameter controls (these would be dynamic based on selected strategy)
        self.param1 = QDoubleSpinBox()
        self.param1.setRange(1, 100)
        self.param1.setValue(14)
        
        self.param2 = QDoubleSpinBox()
        self.param2.setRange(1, 100)
        self.param2.setValue(21)
        
        self.strategy_params_layout.addRow("Parameter 1:", self.param1)
        self.strategy_params_layout.addRow("Parameter 2:", self.param2)
        
        # Add to layout
        layout.addWidget(QLabel("Available Strategies:"))
        layout.addWidget(self.strategies_list)
        layout.addWidget(QLabel("Strategy Parameters:"))
        layout.addWidget(self.strategy_params)
        layout.addStretch()
    
    def browse_data_dir(self):
        """Open a dialog to select the data directory"""
        dir_path = QFileDialog.getExistingDirectory(self, "Select Data Directory")
        if dir_path:
            self.data_dir_edit.setText(dir_path)
    
    def browse_mt5_path(self):
        """Open a dialog to select the MT5 terminal executable"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, 
            "Select MetaTrader 5 Terminal", 
            "", 
            "Executable Files (*.exe)"
        )
        if file_path:
            self.mt5_path_edit.setText(file_path)
    
    def load_current_settings(self):
        """Load current settings from config file or use defaults"""
        # TODO: Load from config file
        # For now, just set some defaults
        self.data_dir_edit.setText(os.path.expanduser("~/trading_data"))
        self.mt5_path_edit.setText("C:\\Program Files\\MetaTrader 5\\terminal64.exe")
    
    def save_settings(self):
        """Save settings and close dialog"""
        try:
            # Save general settings
            self.settings.set('general', 'data_dir', self.data_dir_edit.text())
            self.settings.set('general', 'mt5_path', self.mt5_path_edit.text())
            
            # Save connection settings
            self.settings.set('connection', 'auto_reconnect', self.auto_reconnect.isChecked())
            self.settings.set('connection', 'reconnect_attempts', self.reconnect_attempts.value())
            self.settings.set('connection', 'reconnect_delay', self.reconnect_delay.value())
            
            # Save risk management settings
            self.settings.set('risk', 'risk_per_trade', self.risk_per_trade.value())
            self.settings.set('risk', 'max_positions', self.max_positions.value())
            self.settings.set('risk', 'max_position_size', self.max_position_size.value())
            self.settings.set('risk', 'use_atr_sl', self.use_atr_sl.isChecked())
            self.settings.set('risk', 'atr_multiplier', self.atr_multiplier.value())
            self.settings.set('risk', 'default_risk_reward', self.default_risk_reward.value())
            self.settings.set('risk', 'daily_loss_limit', self.daily_loss_limit.value())
            self.settings.set('risk', 'max_daily_trades', self.max_daily_trades.value())
            
            # Save strategy settings
            if hasattr(self, 'strategies_list') and self.strategies_list.currentItem():
                self.settings.set('strategies', 'selected_strategy', self.strategies_list.currentItem().text())
            
            if hasattr(self, 'param1') and hasattr(self.param1, 'value'):
                self.settings.set('strategies', 'param1', self.param1.value())
                
            if hasattr(self, 'param2') and hasattr(self.param2, 'value'):
                self.settings.set('strategies', 'param2', self.param2.value())
            
            # Save to disk
            self.settings.save()
            
            # Emit signal that settings were updated
            self.settings_updated.emit(self.settings.get_all())
            
            # Show success message
            QMessageBox.information(self, "Success", "Settings saved successfully!")
            
            # Close the dialog if not embedded
            if not self.embedded:
                self.close()
            else:
                self.finished.emit()
                
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to save settings: {str(e)}")
    
    def on_cancel(self):
        """Handle cancel button"""
        self.finished.emit()
        if not self.embedded:
            self.close()
        self.accept()
    
    def restore_defaults(self):
        """Restore all settings to their default values"""
        reply = QMessageBox.question(
            self,
            "Confirm Reset",
            "Are you sure you want to restore all settings to their default values?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            # Reset all controls to default values
            self.data_dir_edit.setText(os.path.expanduser("~/trading_data"))
            self.mt5_path_edit.setText("C:\\Program Files\\MetaTrader 5\\terminal64.exe")
            
            # Connection settings
            self.auto_reconnect.setChecked(True)
            self.reconnect_attempts.setValue(5)
            self.reconnect_delay.setValue(5)
            
            # Risk management defaults
            self.risk_per_trade.setValue(1.0)
            self.max_positions.setValue(10)
            self.max_position_size.setValue(10.0)
            self.use_atr_sl.setChecked(True)
            self.atr_multiplier.setValue(2.0)
            self.default_risk_reward.setValue(2.0)
            self.daily_loss_limit.setValue(5.0)
            self.max_daily_trades.setValue(50)
            
            # Strategy defaults
            if self.strategies_list.count() > 0:
                self.strategies_list.setCurrentRow(0)
            self.param1.setValue(14)
            self.param2.setValue(21)
            self.use_atr_sl.setChecked(True)
            self.atr_multiplier.setValue(2.0)
            self.default_risk_reward.setValue(2.0)
            self.daily_loss_limit.setValue(5.0)
            self.max_daily_trades.setValue(50)
            
            if self.strategies_list.count() > 0:
                self.strategies_list.setCurrentRow(0)
            self.param1.setValue(14)
            self.param2.setValue(21)


if __name__ == "__main__":
    import sys
    from PyQt6.QtWidgets import QApplication

    app = QApplication(sys.argv)
    dialog = SettingsDialog()
    dialog.show()
    sys.exit(app.exec())
