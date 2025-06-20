from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QTabWidget,
    QPushButton, QLabel, QStatusBar, QMessageBox, QComboBox, QSpinBox,
    QDoubleSpinBox, QCheckBox, QGroupBox, QFormLayout, QTableWidget,
    QTableWidgetItem, QHeaderView, QSplitter, QToolBar, QSizePolicy,
    QFrame, QListWidget, QListWidgetItem, QStackedWidget, QApplication
)
from PyQt6.QtCore import Qt, QTimer, pyqtSignal, QThread
from PyQt6.QtGui import QAction, QIcon, QColor
from typing import Dict, List, Optional
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from datetime import datetime, timedelta
import os
import sys

from core.mt5_client import MT5Client
from core.models import SymbolConfig
from core.strategy import TradingStrategy
from ui.dialogs.settings_dialog import SettingsDialog
from ui.dialogs.add_symbol_dialog import AddSymbolDialog
from ui.symbol_widget import SymbolWidget
from ui.dialogs.add_symbol_dialog import AddSymbolDialog
from ui.chart_widget import ChartWidget

class MainWindow(QMainWindow):    
    def __init__(self, mt5_client: MT5Client):
        super().__init__()
        self.mt5_client = mt5_client
        self.symbol_widgets: Dict[str, SymbolWidget] = {}
        self.update_timer = QTimer()
        self.update_interval = 1000  # ms
        
        # Initialize logger
        import logging
        self.logger = logging.getLogger(__name__)
        
        # Initialize UI
        self.init_ui()
        
        # Start update timer
        self.update_timer.timeout.connect(self.update_data)
        self.update_timer.start(self.update_interval)
    
    def init_ui(self):
        """Initialize the main window UI"""
        self.setWindowTitle("SMC Strategy Live Trading")
        self.setGeometry(100, 100, 1200, 800)
        
        # Create central widget and main splitter
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Main layout (horizontal)
        main_layout = QHBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # Create splitter for resizable panels
        self.splitter = QSplitter(Qt.Orientation.Horizontal)
        
        # Create left panel
        self.create_left_panel()
        
        # Create right panel (main content)
        self.right_panel = QWidget()
        right_layout = QVBoxLayout(self.right_panel)
        right_layout.setContentsMargins(5, 5, 5, 5)
        
        # Create stacked widget for different views
        self.stacked_widget = QStackedWidget()
        
        # Add tab widget for symbols (main view)
        self.tab_widget = QTabWidget()
        self.tab_widget.setTabsClosable(True)
        self.tab_widget.tabCloseRequested.connect(self.close_symbol_tab)
        
        # Create container for settings view
        self.settings_container = QWidget()
        self.settings_layout = QVBoxLayout(self.settings_container)
        
        # Add widgets to stacked widget
        self.stacked_widget.addWidget(self.tab_widget)  # Index 0
        self.stacked_widget.addWidget(self.settings_container)  # Index 1
        
        # Set tab widget as default view
        self.stacked_widget.setCurrentIndex(0)
        
        # Add stacked widget to right panel
        right_layout.addWidget(self.stacked_widget)
        
        # Add panels to splitter
        self.splitter.addWidget(self.left_panel)
        self.splitter.addWidget(self.right_panel)
        
        # Set initial sizes (20% for left panel, 80% for right panel)
        self.splitter.setSizes([self.width() // 5, 4 * self.width() // 5])
        
        # Add splitter to main layout
        main_layout.addWidget(self.splitter)
        
        # Create menu bar and toolbar
        self.create_menu_bar()
        
        # Tab widget is now created in create_right_panel()
        
        # Status bar
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("Ready")
        
        # Don't add a default tab, let the user add one manually
        
    def create_left_panel(self):
        """Create the left panel with navigation and settings"""
        # Create left panel
        self.left_panel = QFrame()
        self.left_panel.setFrameShape(QFrame.Shape.StyledPanel)
        self.left_panel.setMinimumWidth(200)
        self.left_panel.setMaximumWidth(400)
        
        # Create layout for left panel
        left_layout = QVBoxLayout(self.left_panel)
        left_layout.setContentsMargins(5, 5, 5, 5)
        left_layout.setSpacing(5)
        
        # Add title
        title = QLabel("SMC Strategy")
        title.setStyleSheet("font-size: 16px; font-weight: bold; margin-bottom: 10px;")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        left_layout.addWidget(title)
        
        # Add connection status
        self.connection_status = QLabel("MT5: Disconnected")
        self.connection_status.setStyleSheet("color: red;")
        left_layout.addWidget(self.connection_status)
        
        # Add buttons
        btn_style = """
            QPushButton {
                text-align: left;
                padding: 8px;
                border: 1px solid #ccc;
                border-radius: 4px;
                margin: 2px 0;
            }
            QPushButton:hover {
                background-color: #f0f0f0;
            }
        """
        
        # Add Symbol button
        self.btn_add_symbol = QPushButton("➕ Add Symbol")
        self.btn_add_symbol.setStyleSheet(btn_style)
        self.btn_add_symbol.clicked.connect(self.show_add_symbol_dialog)
        left_layout.addWidget(self.btn_add_symbol)
        
        # Start/Stop Trading button
        self.btn_toggle_trading = QPushButton("▶ Start Trading")
        self.btn_toggle_trading.setStyleSheet(btn_style)
        self.btn_toggle_trading.clicked.connect(self.toggle_trading)
        left_layout.addWidget(self.btn_toggle_trading)
        
        # Separator
        separator = QFrame()
        separator.setFrameShape(QFrame.Shape.HLine)
        separator.setFrameShadow(QFrame.Shadow.Sunken)
        left_layout.addWidget(separator)
        
        # Settings section
        settings_label = QLabel("Settings")
        settings_label.setStyleSheet("font-weight: bold; margin-top: 10px;")
        left_layout.addWidget(settings_label)
        
        # Settings buttons
        self.btn_settings = QPushButton("⚙ General Settings")
        self.btn_settings.setStyleSheet(btn_style)
        self.btn_settings.clicked.connect(self.show_settings_dialog)
        left_layout.addWidget(self.btn_settings)
        
        self.btn_risk_settings = QPushButton("📉 Risk Management")
        self.btn_risk_settings.setStyleSheet(btn_style)
        # Connect to risk management settings when implemented
        # self.btn_risk_settings.clicked.connect(self.show_risk_settings)
        left_layout.addWidget(self.btn_risk_settings)
        
        # Add a back button to the left panel
        self.btn_back = QPushButton("⬅ Back to Symbols")
        self.btn_back.setStyleSheet(btn_style)
        self.btn_back.clicked.connect(self.show_main_view)
        left_layout.addWidget(self.btn_back)
        self.btn_back.hide()  # Hidden by default, shown when in settings view
        
        # Add stretch to push everything to the top
        left_layout.addStretch()
        
        # Status bar at the bottom
        self.left_status_bar = QStatusBar()
        left_layout.addWidget(self.left_status_bar)
        
        # Update connection status
        self.update_connection_status()
    
    def update_connection_status(self):
        """Update the connection status in the left panel"""
        if hasattr(self, 'mt5_client') and self.mt5_client.initialized:
            self.connection_status.setText("MT5: Connected")
            self.connection_status.setStyleSheet("color: green;")
        else:
            self.connection_status.setText("MT5: Disconnected")
            self.connection_status.setStyleSheet("color: red;")
    
    def toggle_trading(self, checked=None):
        """Toggle trading on/off"""
        if not hasattr(self, 'start_stop_action'):
            # Initialize the action if it doesn't exist
            self.start_stop_action = type('', (), {'isChecked': lambda: False})()
            
        if checked is None:
            # Toggle the current state if no argument is provided
            checked = not self.start_stop_action.isChecked()
            
        if checked:
            self.start_stop_action.setText = lambda x: self.btn_toggle_trading.setText(f"⏸ {x}")
            self.btn_toggle_trading.setText("⏸ Stop Trading")
            self.status_bar.showMessage("Trading started")
            # Start all symbol trading
            for symbol, widget in self.symbol_widgets.items():
                widget.start_trading()
        else:
            self.start_stop_action.setText = lambda x: self.btn_toggle_trading.setText(f"▶ {x}")
            self.btn_toggle_trading.setText("▶ Start Trading")
            self.status_bar.showMessage("Trading stopped")
            # Stop all symbol trading
            for symbol, widget in self.symbol_widgets.items():
                widget.stop_trading()
    
    def create_menu_bar(self):
        """Create the main menu bar"""
        menubar = self.menuBar()
        
        # File menu
        file_menu = menubar.addMenu("&File")
        
        # Add symbol action
        add_symbol_action = QAction("&Add Symbol...", self)
        add_symbol_action.triggered.connect(self.show_add_symbol_dialog)
        add_symbol_action.setShortcut("Ctrl+A")
        file_menu.addAction(add_symbol_action)
        
        # Close tab action
        close_tab_action = QAction("&Close Tab", self)
        close_tab_action.triggered.connect(lambda: self.close_symbol_tab(self.tab_widget.currentIndex()))
        close_tab_action.setShortcut("Ctrl+W")
        file_menu.addAction(close_tab_action)
        
        file_menu.addSeparator()
        
        # Exit action
        exit_action = QAction("E&xit", self)
        exit_action.triggered.connect(self.close)
        exit_action.setShortcut("Alt+F4")
        file_menu.addAction(exit_action)
        
        # View menu
        view_menu = menubar.addMenu("&View")
        
        # Toggle toolbar action
        self.toolbar_visible = True
        toggle_toolbar_action = QAction("&Toolbar", self, checkable=True, checked=True)
        toggle_toolbar_action.triggered.connect(self.toggle_toolbar)
        view_menu.addAction(toggle_toolbar_action)
        
        # Status bar action
        self.statusbar_visible = True
        toggle_statusbar_action = QAction("S&tatus Bar", self, checkable=True, checked=True)
        toggle_statusbar_action.triggered.connect(self.toggle_statusbar)
        view_menu.addAction(toggle_statusbar_action)
        
        # Tools menu
        tools_menu = menubar.addMenu("&Tools")
        
        # Settings action
        settings_action = QAction("&Settings...", self)
        settings_action.triggered.connect(self.show_settings_dialog)
        settings_action.setShortcut("Ctrl+,")
        tools_menu.addAction(settings_action)
        
        # Refresh action
        refresh_action = QAction("&Refresh Data", self)
        refresh_action.triggered.connect(self.refresh_data)
        refresh_action.setShortcut("F5")
        tools_menu.addAction(refresh_action)
        
        # Help menu
        help_menu = menubar.addMenu("&Help")
        
        # About action
        about_action = QAction("&About...", self)
        about_action.triggered.connect(self.show_about_dialog)
        help_menu.addAction(about_action)
        
        # Create the toolbar
        self.create_toolbar()
    
    def create_toolbar(self):
        """Create the main toolbar"""
        self.toolbar = self.addToolBar("Main Toolbar")
        self.toolbar.setMovable(False)
        
        # Add symbol button
        add_symbol_action = QAction(QIcon.fromTheme("list-add"), "Add Symbol", self)
        add_symbol_action.triggered.connect(self.show_add_symbol_dialog)
        add_symbol_action.setToolTip("Add a new symbol (Ctrl+A)")
        self.toolbar.addAction(add_symbol_action)
        
        # Start/Stop trading button
        self.start_stop_action = QAction(QIcon.fromTheme("media-playback-start"), "Start Trading", self)
        self.start_stop_action.triggered.connect(self.toggle_trading)
        self.start_stop_action.setCheckable(True)
        self.start_stop_action.setToolTip("Start/Stop Trading")
        self.toolbar.addAction(self.start_stop_action)
        
        # Add separator
        self.toolbar.addSeparator()
        
        # Refresh button
        refresh_action = QAction(QIcon.fromTheme("view-refresh"), "Refresh", self)
        refresh_action.triggered.connect(self.refresh_data)
        refresh_action.setToolTip("Refresh data (F5)")
        self.toolbar.addAction(refresh_action)
    
    def toggle_toolbar(self, visible):
        """Toggle toolbar visibility"""
        self.toolbar.setVisible(visible)
        self.toolbar_visible = visible
    
    def toggle_statusbar(self, visible):
        """Toggle status bar visibility"""
        self.statusBar().setVisible(visible)
        self.statusbar_visible = visible
    
    def show_about_dialog(self):
        """Show about dialog"""
        from PyQt6.QtWidgets import QMessageBox
        
        about_text = """
        <h2>SMC Strategy Live Trading</h2>
        <p>Version 1.0.0</p>
        <p>Advanced trading platform implementing Smart Money Concepts strategies.</p>
        <p> 2023 SMC Trading Platform. All rights reserved.</p>
        """
        
        QMessageBox.about(self, "About SMC Strategy Live Trading", about_text)
    
    def toggle_trading(self, checked: bool):
        """Toggle trading on/off"""
        if checked:
            self.start_stop_action.setText("Stop Trading")
            self.status_bar.showMessage("Trading started")
            # Start all symbol trading
            for symbol, widget in self.symbol_widgets.items():
                widget.start_trading()
        else:
            self.start_stop_action.setText("Start Trading")
            self.status_bar.showMessage("Trading stopped")
            # Stop all symbol trading
            for symbol, widget in self.symbol_widgets.items():
                widget.stop_trading()
    
    def add_symbol(self, symbol_config):
        """Add a new symbol tab"""
        if not symbol_config or 'symbol' not in symbol_config:
            return
        
        symbol = symbol_config['symbol']
        if symbol in self.symbol_widgets:
            # Symbol already exists, switch to its tab
            widget = self.symbol_widgets[symbol]
            self.tab_widget.setCurrentWidget(widget)
            return
        
        # Create new symbol widget
        symbol_widget = SymbolWidget(
            symbol=symbol,
            mt5_client=self.mt5_client,
            parent=self,
            config=symbol_config
        )
        
        # Connect signals
        symbol_widget.error_occurred.connect(self.show_error)
        symbol_widget.status_message.connect(self.status_bar.showMessage)
        
        # Add to tab widget and dictionary
        self.symbol_widgets[symbol] = symbol_widget
        tab_index = self.tab_widget.addTab(symbol_widget, symbol)
        self.tab_widget.setCurrentIndex(tab_index)
        
        # Start trading if auto-trading is enabled
        if self.start_stop_action.isChecked():
            symbol_widget.start_trading()
        
        # Close any open AddSymbolDialog tabs
        for i in range(self.tab_widget.count() - 1, -1, -1):
            if isinstance(self.tab_widget.widget(i), AddSymbolDialog):
                self.close_symbol_tab(i)
    
    def close_symbol_tab(self, index: int):
        """Close a symbol tab"""
        if index < 0 or index >= self.tab_widget.count():
            return
            
        widget = self.tab_widget.widget(index)
        if widget is None:
            return
            
        # Handle AddSymbolDialog
        if isinstance(widget, AddSymbolDialog):
            # Disconnect signals first to prevent recursion
            try:
                widget.rejected.disconnect()
            except TypeError:
                pass  # No connections to disconnect
                
            # Remove the tab first to prevent any signal emissions during deletion
            self.tab_widget.removeTab(index)
            widget.deleteLater()
            return
            
        # Handle SymbolWidget
        if hasattr(widget, 'symbol'):
            symbol = widget.symbol
            # Stop trading if active
            if hasattr(widget, 'stop_trading'):
                try:
                    widget.stop_trading()
                except Exception as e:
                    print(f"Error stopping trading for {symbol}: {e}")
            
            # Remove from tracking dict first
            if symbol in self.symbol_widgets:
                del self.symbol_widgets[symbol]
                
            # Remove the tab
            self.tab_widget.removeTab(index)
            widget.deleteLater()
    
    def show_add_symbol_dialog(self):
        """Show add symbol widget in a new tab"""
        # Check if Add Symbol tab already exists
        for i in range(self.tab_widget.count()):
            if isinstance(self.tab_widget.widget(i), AddSymbolDialog):
                self.tab_widget.setCurrentIndex(i)
                return
        
        # Get available symbols first
        available_symbols = self.mt5_client.get_available_symbols()
        if not available_symbols:
            self.logger.error("No symbols available. Please check your MT5 connection.")
            QMessageBox.warning(self, "Error", "No symbols available. Please check your MT5 connection and ensure you have market data subscription.")
            return
            
        # Create add symbol widget with available symbols
        print(f"Creating dialog with {len(available_symbols)} symbols")
        add_symbol_widget = AddSymbolDialog(self, embedded=True, available_symbols=available_symbols)
        
        # Connect signals
        add_symbol_widget.accepted.connect(self.add_symbol)
        add_symbol_widget.rejected.connect(lambda: self.close_symbol_tab(self.tab_widget.indexOf(add_symbol_widget)))
        
        # Add to tab widget
        tab_index = self.tab_widget.addTab(add_symbol_widget, "➕ Add Symbol")
        self.tab_widget.setCurrentIndex(tab_index)
    
    def _on_symbols_loaded(self, available_symbols, error):
        """Handle the loaded symbols and create the dialog"""
        try:
            # Clear the loading message
            self.clear_settings_view()
            
            if error or not available_symbols:
                error_msg = error or "No symbols available. Please check your MT5 connection and ensure you have market data subscription."
                self.logger.error(f"Failed to load symbols: {error_msg}")
                self.show_error(error_msg)
                self.show_main_view()
                return
            
            self.logger.info(f"Loaded {len(available_symbols)} available symbols")
            
            # Create the dialog with embedded flag and available symbols
            print(f"Creating dialog with {len(available_symbols)} symbols in _on_symbols_loaded")
            self.add_symbol_widget = AddSymbolDialog(parent=self, embedded=True, available_symbols=available_symbols)
            
            # Connect signals
            self.add_symbol_widget.accepted.connect(self._on_symbol_accepted)
            self.add_symbol_widget.rejected.connect(self.show_main_view)
            
            # Add to settings container with proper layout
            self.settings_layout.addWidget(self.add_symbol_widget)
            
            # Switch to settings view
            self.logger.debug("Showing add symbol dialog")
            self.show_settings_view()
            
        except Exception as e:
            error_msg = f"Error creating symbol dialog: {str(e)}"
            self.logger.error(error_msg, exc_info=True)
            self.show_error(error_msg)
            self.show_main_view()
    
    def _on_symbol_accepted(self):
        """Handle when a symbol is accepted in the dialog"""
        try:
            if hasattr(self, 'add_symbol_widget') and self.add_symbol_widget:
                settings = self.add_symbol_widget.get_settings()
                if settings:
                    self.on_symbol_added(settings)
        except Exception as e:
            error_msg = f"Error processing symbol settings: {str(e)}"
            self.logger.error(error_msg, exc_info=True)
            self.show_error(error_msg)
        finally:
            self.show_main_view()
    
    def on_symbol_added(self, symbol_config):
        """Handle when a new symbol is added"""
        self.add_symbol_tab(symbol_config)
        self.show_main_view()
    
    def show_settings_dialog(self):
        """Show settings in the central panel"""
        try:
            # Clear previous settings
            self.clear_settings_view()
            
            # Create and add settings widget
            self.settings_widget = SettingsDialog(self, embedded=True)
            self.settings_widget.finished.connect(self.show_main_view)
            
            # Add to settings container
            self.settings_layout.addWidget(self.settings_widget)
            
            # Switch to settings view
            self.logger.debug("Showing settings dialog")
            self.show_settings_view()
            
        except Exception as e:
            error_msg = f"Error showing settings dialog: {str(e)}"
            self.logger.error(error_msg, exc_info=True)
            self.show_error(error_msg)
            self.show_main_view()
    
    def clear_settings_view(self):
        """Clear the settings view"""
        # Remove all widgets from settings container
        while self.settings_layout.count():
            item = self.settings_layout.takeAt(0)
            if item.widget():
                widget = item.widget()
                widget.setParent(None)
                widget.deleteLater()
        
        # Ensure the layout is properly cleaned up
        QApplication.processEvents()
    
    def show_settings_view(self):
        """Switch to the settings view"""
        try:
            self.stacked_widget.setCurrentIndex(1)
            self.btn_back.show()
            QApplication.processEvents()  # Ensure UI updates
        except Exception as e:
            self.logger.error(f"Error switching to settings view: {str(e)}", exc_info=True)
            self.show_error("Failed to switch to settings view")
    
    def show_main_view(self):
        """Switch to the main tab view"""
        try:
            # Clear any settings widgets
            self.clear_settings_view()
            
            # Switch to main view
            self.stacked_widget.setCurrentIndex(0)
            self.btn_back.hide()
            QApplication.processEvents()  # Ensure UI updates
        except Exception as e:
            self.logger.error(f"Error switching to main view: {str(e)}", exc_info=True)
            self.show_error("Failed to switch to main view")
    
    def show_error(self, message: str):
        """Show error message"""
        QMessageBox.critical(self, "Error", message)
    
    def update_data(self):
        """Update data for all symbols"""
        if not self.start_stop_action.isChecked():
            return
            
        current_widget = self.tab_widget.currentWidget()
        if current_widget and hasattr(current_widget, 'update_data'):
            current_widget.update_data()
    
    def refresh_data(self):
        """Force refresh of all data"""
        current_widget = self.tab_widget.currentWidget()
        if current_widget and hasattr(current_widget, 'refresh_data'):
            current_widget.refresh_data()
    
    def closeEvent(self, event):
        """Handle window close event"""
        # Stop all trading
        self.start_stop_action.setChecked(False)
        self.toggle_trading(False)
        
        # Stop update timer
        self.update_timer.stop()
        
        # Close MT5 connection
        self.mt5_client.shutdown()
        
        # Accept the close event
        event.accept()
