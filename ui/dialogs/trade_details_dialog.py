from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QFormLayout, QLabel, 
    QDialogButtonBox, QTabWidget, QTableWidget, QTableWidgetItem,
    QHeaderView, QGroupBox, QTextEdit
)
from PyQt6.QtCore import Qt, QDateTime
from PyQt6.QtGui import QFont, QColor, QBrush

class TradeDetailsDialog(QDialog):
    """Dialog for displaying detailed information about a trade"""
    
    def __init__(self, trade_data, parent=None):
        super().__init__(parent)
        self.trade_data = trade_data
        self.setWindowTitle("Trade Details")
        self.setMinimumSize(800, 600)
        
        self.init_ui()
    
    def init_ui(self):
        """Initialize the UI components"""
        layout = QVBoxLayout(self)
        
        # Create tab widget
        self.tab_widget = QTabWidget()
        
        # Summary tab
        self.create_summary_tab()
        
        # Execution tab
        self.create_execution_tab()
        
        # Performance tab
        self.create_performance_tab()
        
        # Notes tab
        self.create_notes_tab()
        
        # Add tabs to tab widget
        self.tab_widget.addTab(self.summary_tab, "Summary")
        self.tab_widget.addTab(self.execution_tab, "Execution")
        self.tab_widget.addTab(self.performance_tab, "Performance")
        self.tab_widget.addTab(self.notes_tab, "Notes")
        
        # Button box
        button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Close)
        button_box.rejected.connect(self.reject)
        
        # Add to layout
        layout.addWidget(self.tab_widget)
        layout.addWidget(button_box)
        
        # Load trade data
        self.load_trade_data()
    
    def create_summary_tab(self):
        """Create the Summary tab"""
        self.summary_tab = QWidget()
        layout = QVBoxLayout(self.summary_tab)
        
        # Trade info group
        info_group = QGroupBox("Trade Information")
        info_layout = QFormLayout()
        
        # Create labels to display trade info
        self.trade_id_label = QLabel()
        self.symbol_label = QLabel()
        self.type_label = QLabel()
        self.status_label = QLabel()
        self.volume_label = QLabel()
        self.open_price_label = QLabel()
        self.current_price_label = QLabel()
        self.profit_label = QLabel()
        self.commission_label = QLabel()
        self.swap_label = QLabel()
        
        # Add to form
        info_layout.addRow("Trade ID:", self.trade_id_label)
        info_layout.addRow("Symbol:", self.symbol_label)
        info_layout.addRow("Type:", self.type_label)
        info_layout.addRow("Status:", self.status_label)
        info_layout.addRow("Volume (lots):", self.volume_label)
        info_layout.addRow("Open Price:", self.open_price_label)
        info_layout.addRow("Current Price:", self.current_price_label)
        info_layout.addRow("Profit/Loss:", self.profit_label)
        info_layout.addRow("Commission:", self.commission_label)
        info_layout.addRow("Swap:", self.swap_label)
        
        info_group.setLayout(info_layout)
        
        # Add to layout
        layout.addWidget(info_group)
        layout.addStretch()
    
    def create_execution_tab(self):
        """Create the Execution tab"""
        self.execution_tab = QWidget()
        layout = QVBoxLayout(self.execution_tab)
        
        # Execution details group
        exec_group = QGroupBox("Execution Details")
        exec_layout = QFormLayout()
        
        # Create labels for execution details
        self.open_time_label = QLabel()
        self.close_time_label = QLabel()
        self.duration_label = QLabel()
        self.slippage_label = QLabel()
        self.spread_label = QLabel()
        self.magic_number_label = QLabel()
        self.comment_label = QLabel()
        
        # Add to form
        exec_layout.addRow("Open Time:", self.open_time_label)
        exec_layout.addRow("Close Time:", self.close_time_label)
        exec_layout.addRow("Duration:", self.duration_label)
        exec_layout.addRow("Slippage:", self.slippage_label)
        exec_layout.addRow("Spread (points):", self.spread_label)
        exec_layout.addRow("Magic Number:", self.magic_number_label)
        exec_layout.addRow("Comment:", self.comment_label)
        
        exec_group.setLayout(exec_layout)
        
        # Add to layout
        layout.addWidget(exec_group)
        layout.addStretch()
    
    def create_performance_tab(self):
        """Create the Performance tab"""
        self.performance_tab = QWidget()
        layout = QVBoxLayout(self.performance_tab)
        
        # Performance metrics group
        perf_group = QGroupBox("Performance Metrics")
        perf_layout = QFormLayout()
        
        # Create labels for performance metrics
        self.max_profit_label = QLabel()
        self.max_drawdown_label = QLabel()
        self.risk_reward_label = QLabel()
        self.probability_label = QLabel()
        self.quality_label = QLabel()
        
        # Add to form
        perf_layout.addRow("Maximum Profit:", self.max_profit_label)
        perf_layout.addRow("Maximum Drawdown:", self.max_drawdown_label)
        perf_layout.addRow("Risk/Reward Ratio:", self.risk_reward_label)
        perf_layout.addRow("Probability of Profit:", self.probability_label)
        perf_layout.addRow("Trade Quality:", self.quality_label)
        
        perf_group.setLayout(perf_layout)
        
        # Add to layout
        layout.addWidget(perf_group)
        layout.addStretch()
    
    def create_notes_tab(self):
        """Create the Notes tab"""
        self.notes_tab = QWidget()
        layout = QVBoxLayout(self.notes_tab)
        
        # Notes editor
        self.notes_edit = QTextEdit()
        self.notes_edit.setPlaceholderText("Add notes about this trade...")
        
        # Add to layout
        layout.addWidget(QLabel("Trade Notes:"))
        layout.addWidget(self.notes_edit)
        layout.addStretch()
    
    def load_trade_data(self):
        """Load trade data into the UI"""
        if not self.trade_data:
            return
        
        trade = self.trade_data
        
        # Summary tab
        self.trade_id_label.setText(str(trade.get('ticket', '')))
        self.symbol_label.setText(trade.get('symbol', ''))
        self.type_label.setText(self.get_trade_type(trade.get('type', 0)))
        self.status_label.setText(self.get_trade_status(trade.get('status', 0)))
        self.volume_label.setText(f"{trade.get('volume', 0):.2f}")
        self.open_price_label.setText(str(trade.get('price_open', '')))
        self.current_price_label.setText(str(trade.get('price_current', '')))
        
        # Format profit with color
        profit = trade.get('profit', 0)
        profit_text = f"{profit:.2f} {trade.get('currency', '')}"
        self.profit_label.setText(profit_text)
        self.profit_label.setStyleSheet(
            f"color: {'#4CAF50' if profit >= 0 else '#F44336'};"
            f"font-weight: bold;"
        )
        
        self.commission_label.setText(f"{trade.get('commission', 0):.2f} {trade.get('currency', '')}")
        self.swap_label.setText(f"{trade.get('swap', 0):.2f} {trade.get('currency', '')}")
        
        # Execution tab
        self.open_time_label.setText(
            QDateTime.fromSecsSinceEpoch(trade.get('time_open', 0)).toString("yyyy-MM-dd hh:mm:ss")
            if trade.get('time_open') else "N/A"
        )
        
        close_time = trade.get('time_close')
        if close_time:
            self.close_time_label.setText(
                QDateTime.fromSecsSinceEpoch(close_time).toString("yyyy-MM-dd hh:mm:ss")
            )
            
            # Calculate duration
            duration_secs = close_time - trade.get('time_open', close_time)
            days = duration_secs // (24 * 3600)
            hours = (duration_secs % (24 * 3600)) // 3600
            minutes = (duration_secs % 3600) // 60
            seconds = duration_secs % 60
            self.duration_label.setText(f"{days}d {hours}h {minutes}m {seconds}s")
        else:
            self.close_time_label.setText("N/A")
            self.duration_label.setText("N/A")
        
        self.slippage_label.setText(f"{trade.get('slippage', 0)} points")
        self.spread_label.setText(str(trade.get('spread', 0)))
        self.magic_number_label.setText(str(trade.get('magic', 0)))
        self.comment_label.setText(trade.get('comment', ''))
        
        # Performance tab
        self.max_profit_label.setText(f"{trade.get('max_profit', 0):.2f} {trade.get('currency', '')}")
        self.max_drawdown_label.setText(f"{trade.get('max_drawdown', 0):.2f} {trade.get('currency', '')} ({trade.get('max_drawdown_pct', 0):.2f}%)")
        self.risk_reward_label.setText(f"{trade.get('risk_reward', 0):.2f}")
        self.probability_label.setText(f"{trade.get('probability', 0):.1f}%")
        self.quality_label.setText(self.get_quality_rating(trade.get('quality', 0)))
        
        # Notes tab
        self.notes_edit.setPlainText(trade.get('notes', ''))
    
    def get_trade_type(self, type_code):
        """Convert trade type code to string"""
        types = {
            0: "Buy",
            1: "Sell",
            2: "Buy Limit",
            3: "Sell Limit",
            4: "Buy Stop",
            5: "Sell Stop"
        }
        return types.get(type_code, f"Unknown ({type_code})")
    
    def get_trade_status(self, status_code):
        """Convert trade status code to string"""
        statuses = {
            0: "Open",
            1: "Pending",
            2: "Closed",
            3: "Modified",
            4: "Canceled"
        }
        return statuses.get(status_code, f"Unknown ({status_code})")
    
    def get_quality_rating(self, score):
        """Convert quality score to rating"""
        if score >= 9:
            return "Excellent (A+)"
        elif score >= 8:
            return "Very Good (A)"
        elif score >= 7:
            return "Good (B+)"
        elif score >= 6:
            return "Average (B)"
        elif score >= 5:
            return "Below Average (C)"
        else:
            return "Poor (D)"


if __name__ == "__main__":
    import sys
    from PyQt6.QtWidgets import QApplication
    import time
    
    # Sample trade data
    sample_trade = {
        'ticket': 12345678,
        'symbol': 'EURUSD',
        'type': 0,  # Buy
        'status': 0,  # Open
        'volume': 0.1,
        'price_open': 1.12345,
        'price_current': 1.12567,
        'price_sl': 1.12000,
        'price_tp': 1.13000,
        'profit': 12.34,
        'commission': 1.50,
        'swap': 0.25,
        'currency': 'USD',
        'time_open': int(time.time()) - 3600,  # 1 hour ago
        'time_close': 0,  # Still open
        'slippage': 2,
        'spread': 12,
        'magic': 12345,
        'comment': 'SMC Strategy',
        'max_profit': 15.67,
        'max_drawdown': -5.43,
        'max_drawdown_pct': 2.1,
        'risk_reward': 2.5,
        'probability': 68.5,
        'quality': 8.2,
        'notes': 'Entered on daily support level. Strong trend continuation setup.'
    }
    
    app = QApplication(sys.argv)
    dialog = TradeDetailsDialog(sample_trade)
    dialog.show()
    sys.exit(app.exec())
