from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QFormLayout, QLabel, 
    QLineEdit, QPushButton, QTableWidget, QTableWidgetItem, QHeaderView,
    QTabWidget, QWidget, QMessageBox, QComboBox, QDoubleSpinBox, QSpinBox
)
from PyQt6.QtCore import Qt, pyqtSignal, QTimer
from PyQt6.QtGui import QColor, QBrush
from datetime import datetime

class AccountDialog(QDialog):
    """Dialog for displaying and managing account information"""
    
    # Signals
    deposit_requested = pyqtSignal(float)  # amount
    withdrawal_requested = pyqtSignal(float)  # amount
    
    def __init__(self, account_data, parent=None):
        super().__init__(parent)
        self.account_data = account_data or {}
        self.setWindowTitle("Account Information")
        self.setMinimumSize(800, 600)
        
        self.init_ui()
        self.load_account_data()
        
        # Setup auto-refresh
        self.refresh_timer = QTimer(self)
        self.refresh_timer.timeout.connect(self.refresh_account_data)
        self.refresh_timer.start(10000)  # Refresh every 10 seconds
    
    def init_ui(self):
        """Initialize the UI components"""
        layout = QVBoxLayout(self)
        
        # Create tab widget
        self.tab_widget = QTabWidget()
        
        # Summary tab
        self.create_summary_tab()
        
        # Balance tab
        self.create_balance_tab()
        
        # History tab
        self.create_history_tab()
        
        # Settings tab
        self.create_settings_tab()
        
        # Add tabs to tab widget
        self.tab_widget.addTab(self.summary_tab, "Summary")
        self.tab_widget.addTab(self.balance_tab, "Balance")
        self.tab_widget.addTab(self.history_tab, "History")
        self.tab_widget.addTab(self.settings_tab, "Settings")
        
        # Button box
        button_box = QPushButton("Close")
        button_box.clicked.connect(self.accept)
        
        # Add to layout
        layout.addWidget(self.tab_widget)
        layout.addWidget(button_box, alignment=Qt.AlignmentFlag.AlignRight)
    
    def create_summary_tab(self):
        """Create the Summary tab"""
        self.summary_tab = QWidget()
        layout = QVBoxLayout(self.summary_tab)
        
        # Account info group
        info_group = QGroupBox("Account Information")
        info_layout = QFormLayout()
        
        # Create labels to display account info
        self.account_id_label = QLabel()
        self.account_name_label = QLabel()
        self.account_type_label = QLabel()
        self.account_currency_label = QLabel()
        self.account_leverage_label = QLabel()
        
        # Add to form
        info_layout.addRow("Account ID:", self.account_id_label)
        info_layout.addRow("Name:", self.account_name_label)
        info_layout.addRow("Type:", self.account_type_label)
        info_layout.addRow("Currency:", self.account_currency_label)
        info_layout.addRow("Leverage:", self.account_leverage_label)
        
        info_group.setLayout(info_layout)
        
        # Balance info group
        balance_group = QGroupBox("Balance Information")
        balance_layout = QFormLayout()
        
        self.balance_label = QLabel()
        self.equity_label = QLabel()
        self.margin_label = QLabel()
        self.free_margin_label = QLabel()
        self.margin_level_label = QLabel()
        
        balance_layout.addRow("Balance:", self.balance_label)
        balance_layout.addRow("Equity:", self.equity_label)
        balance_layout.addRow("Margin:", self.margin_label)
        balance_layout.addRow("Free Margin:", self.free_margin_label)
        balance_layout.addRow("Margin Level:", self.margin_level_label)
        
        balance_group.setLayout(balance_layout)
        
        # Add to layout
        layout.addWidget(info_group)
        layout.addWidget(balance_group)
        layout.addStretch()
    
    def create_balance_tab(self):
        """Create the Balance tab"""
        self.balance_tab = QWidget()
        layout = QVBoxLayout(self.balance_tab)
        
        # Deposit/Withdrawal group
        trans_group = QGroupBox("Account Transactions")
        trans_layout = QVBoxLayout()
        
        # Deposit form
        deposit_layout = QHBoxLayout()
        self.deposit_amount = QDoubleSpinBox()
        self.deposit_amount.setRange(0.01, 1000000.0)
        self.deposit_amount.setDecimals(2)
        self.deposit_amount.setPrefix("$")
        
        deposit_btn = QPushButton("Deposit")
        deposit_btn.clicked.connect(self.deposit_funds)
        
        deposit_layout.addWidget(QLabel("Amount:"))
        deposit_layout.addWidget(self.deposit_amount)
        deposit_layout.addWidget(deposit_btn)
        
        # Withdrawal form
        withdrawal_layout = QHBoxLayout()
        self.withdrawal_amount = QDoubleSpinBox()
        self.withdrawal_amount.setRange(0.01, 1000000.0)
        self.withdrawal_amount.setDecimals(2)
        self.withdrawal_amount.setPrefix("$")
        
        withdrawal_btn = QPushButton("Withdraw")
        withdrawal_btn.clicked.connect(self.withdraw_funds)
        
        withdrawal_layout.addWidget(QLabel("Amount:"))
        withdrawal_layout.addWidget(self.withdrawal_amount)
        withdrawal_layout.addWidget(withdrawal_btn)
        
        # Add to transaction layout
        trans_layout.addLayout(deposit_layout)
        trans_layout.addLayout(withdrawal_layout)
        trans_group.setLayout(trans_layout)
        
        # Balance history chart (placeholder)
        chart_group = QGroupBox("Balance History")
        chart_layout = QVBoxLayout()
        
        # This would be replaced with an actual chart widget
        chart_placeholder = QLabel("Balance history chart will be displayed here")
        chart_placeholder.setAlignment(Qt.AlignmentFlag.AlignCenter)
        chart_placeholder.setStyleSheet("color: #888; font-style: italic;")
        chart_placeholder.setMinimumHeight(200)
        
        chart_layout.addWidget(chart_placeholder)
        chart_group.setLayout(chart_layout)
        
        # Add to main layout
        layout.addWidget(trans_group)
        layout.addWidget(chart_group)
    
    def create_history_tab(self):
        """Create the History tab"""
        self.history_tab = QWidget()
        layout = QVBoxLayout(self.history_tab)
        
        # History table
        self.history_table = QTableWidget()
        self.history_table.setColumnCount(6)
        self.history_table.setHorizontalHeaderLabels([
            "Date/Time", "Type", "Amount", "Balance", "Comment", "Ticket"
        ])
        
        # Configure table
        self.history_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.history_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        
        # Set column widths
        header = self.history_table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.ResizeMode.Interactive)
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)  # Date/Time
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)  # Type
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)  # Amount
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)  # Balance
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.Stretch)  # Comment
        header.setSectionResizeMode(5, QHeaderView.ResizeMode.ResizeToContents)  # Ticket
        
        # Add to layout
        layout.addWidget(self.history_table)
    
    def create_settings_tab(self):
        """Create the Settings tab"""
        self.settings_tab = QWidget()
        layout = QVBoxLayout(self.settings_tab)
        
        # Risk settings group
        risk_group = QGroupBox("Risk Settings")
        risk_layout = QFormLayout()
        
        self.risk_per_trade = QDoubleSpinBox()
        self.risk_per_trade.setRange(0.1, 10.0)
        self.risk_per_trade.setValue(1.0)
        self.risk_per_trade.setSuffix("%")
        
        self.max_positions = QSpinBox()
        self.max_positions.setRange(1, 100)
        self.max_positions.setValue(10)
        
        self.max_drawdown = QDoubleSpinBox()
        self.max_drawdown.setRange(1.0, 100.0)
        self.max_drawdown.setValue(10.0)
        self.max_drawdown.setSuffix("%")
        
        risk_layout.addRow("Risk per Trade:", self.risk_per_trade)
        risk_layout.addRow("Max Open Positions:", self.max_positions)
        risk_layout.addRow("Max Daily Drawdown:", self.max_drawdown)
        
        risk_group.setLayout(risk_layout)
        
        # Notification settings group
        notif_group = QGroupBox("Notifications")
        notif_layout = QVBoxLayout()
        
        self.email_notifs = QCheckBox("Enable Email Notifications")
        self.sound_alerts = QCheckBox("Enable Sound Alerts")
        self.push_notifs = QCheckBox("Enable Push Notifications")
        
        notif_layout.addWidget(self.email_notifs)
        notif_layout.addWidget(self.sound_alerts)
        notif_layout.addWidget(self.push_notifs)
        
        notif_group.setLayout(notif_layout)
        
        # Save button
        save_btn = QPushButton("Save Settings")
        save_btn.clicked.connect(self.save_settings)
        
        # Add to layout
        layout.addWidget(risk_group)
        layout.addWidget(notif_group)
        layout.addStretch()
        layout.addWidget(save_btn, alignment=Qt.AlignmentFlag.AlignRight)
    
    def load_account_data(self):
        """Load account data into the UI"""
        if not self.account_data:
            return
        
        # Summary tab
        self.account_id_label.setText(str(self.account_data.get('login', '')))
        self.account_name_label.setText(self.account_data.get('name', ''))
        self.account_type_label.setText(self.account_data.get('type', ''))
        self.account_currency_label.setText(self.account_data.get('currency', ''))
        self.account_leverage_label.setText(f"1:{self.account_data.get('leverage', 0)}")
        
        # Balance information
        self.balance_label.setText(f"{self.account_data.get('balance', 0):.2f} {self.account_data.get('currency', '')}")
        self.equity_label.setText(f"{self.account_data.get('equity', 0):.2f} {self.account_data.get('currency', '')}")
        self.margin_label.setText(f"{self.account_data.get('margin', 0):.2f} {self.account_data.get('currency', '')}")
        self.free_margin_label.setText(f"{self.account_data.get('free_margin', 0):.2f} {self.account_data.get('currency', '')}")
        
        margin_level = self.account_data.get('margin_level', 0)
        self.margin_level_label.setText(f"{margin_level:.2f}%")
        
        # Color margin level based on value
        if margin_level < 100:
            self.margin_level_label.setStyleSheet("color: #F44336; font-weight: bold;")
        elif margin_level < 200:
            self.margin_level_label.setStyleSheet("color: #FFC107;")
        else:
            self.margin_level_label.setStyleSheet("color: #4CAF50;")
        
        # Load history
        self.load_history_data()
    
    def load_history_data(self):
        """Load account history data"""
        history = self.account_data.get('history', [])
        self.history_table.setRowCount(0)
        
        for item in history:
            row = self.history_table.rowCount()
            self.history_table.insertRow(row)
            
            # Format time
            time_str = datetime.fromtimestamp(item.get('time', 0)).strftime("%Y-%m-%d %H:%M:%S")
            
            # Add items to the table
            self.history_table.setItem(row, 0, QTableWidgetItem(time_str))
            self.history_table.setItem(row, 1, QTableWidgetItem(item.get('type', '')))
            
            # Format amount with color
            amount = item.get('amount', 0)
            amount_item = QTableWidgetItem(f"{amount:.2f} {self.account_data.get('currency', '')}")
            amount_item.setForeground(QColor("#4CAF50") if amount >= 0 else QColor("#F44336"))
            self.history_table.setItem(row, 2, amount_item)
            
            self.history_table.setItem(row, 3, QTableWidgetItem(f"{item.get('balance', 0):.2f}"))
            self.history_table.setItem(row, 4, QTableWidgetItem(item.get('comment', '')))
            self.history_table.setItem(row, 5, QTableWidgetItem(str(item.get('ticket', ''))))
    
    def deposit_funds(self):
        """Handle deposit request"""
        amount = self.deposit_amount.value()
        if amount <= 0:
            QMessageBox.warning(self, "Invalid Amount", "Please enter a valid amount to deposit.")
            return
            
        reply = QMessageBox.question(
            self,
            "Confirm Deposit",
            f"Are you sure you want to deposit ${amount:.2f}?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            self.deposit_requested.emit(amount)
            QMessageBox.information(self, "Deposit Requested", "Your deposit request has been submitted.")
    
    def withdraw_funds(self):
        """Handle withdrawal request"""
        amount = self.withdrawal_amount.value()
        if amount <= 0:
            QMessageBox.warning(self, "Invalid Amount", "Please enter a valid amount to withdraw.")
            return
            
        reply = QMessageBox.question(
            self,
            "Confirm Withdrawal",
            f"Are you sure you want to withdraw ${amount:.2f}?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            self.withdrawal_requested.emit(amount)
            QMessageBox.information(self, "Withdrawal Requested", "Your withdrawal request has been submitted.")
    
    def save_settings(self):
        """Save account settings"""
        # In a real application, this would save the settings to a config file or server
        QMessageBox.information(self, "Settings Saved", "Your account settings have been saved successfully.")
    
    def refresh_account_data(self):
        """Refresh the account data"""
        # This would typically fetch fresh data from the trading platform
        # For now, we'll just reload the existing data
        self.load_account_data()
    
    def closeEvent(self, event):
        """Handle dialog close event"""
        self.refresh_timer.stop()
        super().closeEvent(event)


if __name__ == "__main__":
    import sys
    from PyQt6.QtWidgets import QApplication
    import random
    import time
    
    # Sample account data
    account_data = {
        'login': 12345678,
        'name': 'John Doe',
        'type': 'Standard',
        'currency': 'USD',
        'leverage': 100,
        'balance': 10000.00,
        'equity': 10245.67,
        'margin': 2450.89,
        'free_margin': 7794.78,
        'margin_level': 418.15,
        'history': []
    }
    
    # Generate sample history
    balance = 8000.00
    for i in range(30):
        amount = round(random.uniform(10.0, 500.0), 2)
        if random.random() > 0.5:
            amount = -amount
        
        balance += amount
        
        account_data['history'].append({
            'time': int(time.time()) - (30 - i) * 86400,  # Last 30 days
            'type': 'Deposit' if amount > 0 else 'Withdrawal',
            'amount': amount,
            'balance': balance,
            'comment': f'Transaction {i+1}',
            'ticket': 3000000 + i
        })
    
    app = QApplication(sys.argv)
    dialog = AccountDialog(account_data)
    dialog.show()
    sys.exit(app.exec())
