from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem,
    QPushButton, QHeaderView, QLabel, QMessageBox, QMenu, QAbstractItemView
)
from PyQt6.QtCore import Qt, pyqtSignal, QTimer
from PyQt6.QtGui import QAction, QColor, QBrush
from datetime import datetime
import numpy as np

class PositionsDialog(QDialog):
    """Dialog for managing open positions"""
    
    # Signals
    close_position_signal = pyqtSignal(int)  # ticket
    modify_position_signal = pyqtSignal(dict)  # position data
    
    def __init__(self, positions_data, parent=None):
        super().__init__(parent)
        self.positions_data = positions_data or []
        self.setWindowTitle("Open Positions")
        self.setMinimumSize(1000, 600)
        
        self.init_ui()
        self.load_positions()
        
        # Setup auto-refresh
        self.refresh_timer = QTimer(self)
        self.refresh_timer.timeout.connect(self.refresh_positions)
        self.refresh_timer.start(5000)  # Refresh every 5 seconds
    
    def init_ui(self):
        """Initialize the UI components"""
        layout = QVBoxLayout(self)
        
        # Summary bar
        self.summary_bar = QLabel("0 positions | P/L: $0.00 | Equity: $0.00")
        self.summary_bar.setStyleSheet("padding: 5px; background-color: #f0f0f0;")
        
        # Positions table
        self.positions_table = QTableWidget()
        self.positions_table.setColumnCount(10)
        self.positions_table.setHorizontalHeaderLabels([
            "Ticket", "Symbol", "Type", "Volume", "Entry", "Current", "S/L", "T/P", "P/L", "Time"
        ])
        
        # Configure table
        self.positions_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.positions_table.setSelectionMode(QTableWidget.SelectionMode.ExtendedSelection)
        self.positions_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.positions_table.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.positions_table.customContextMenuRequested.connect(self.show_context_menu)
        
        # Set column widths
        header = self.positions_table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.ResizeMode.Interactive)
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)  # Ticket
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)  # Symbol
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)  # Type
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)  # Volume
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)  # Entry
        header.setSectionResizeMode(5, QHeaderView.ResizeMode.ResizeToContents)  # Current
        header.setSectionResizeMode(6, QHeaderView.ResizeMode.ResizeToContents)  # S/L
        header.setSectionResizeMode(7, QHeaderView.ResizeMode.ResizeToContents)  # T/P
        header.setSectionResizeMode(8, QHeaderView.ResizeMode.ResizeToContents)  # P/L
        header.setSectionResizeMode(9, QHeaderView.ResizeMode.Stretch)  # Time
        
        # Buttons
        btn_layout = QHBoxLayout()
        
        self.refresh_btn = QPushButton("Refresh")
        self.refresh_btn.clicked.connect(self.refresh_positions)
        
        self.close_btn = QPushButton("Close Position")
        self.close_btn.clicked.connect(self.close_selected_positions)
        
        self.modify_btn = QPushButton("Modify")
        self.modify_btn.clicked.connect(self.modify_position)
        
        self.close_all_btn = QPushButton("Close All")
        self.close_all_btn.clicked.connect(self.close_all_positions)
        
        btn_layout.addWidget(self.refresh_btn)
        btn_layout.addStretch()
        btn_layout.addWidget(self.close_btn)
        btn_layout.addWidget(self.modify_btn)
        btn_layout.addWidget(self.close_all_btn)
        
        # Add to layout
        layout.addWidget(self.summary_bar)
        layout.addWidget(self.positions_table)
        layout.addLayout(btn_layout)
    
    def load_positions(self):
        """Load positions into the table"""
        self.positions_table.setRowCount(0)
        
        if not self.positions_data:
            self.summary_bar.setText("No open positions")
            return
        
        total_pl = 0.0
        total_volume = 0.0
        
        for pos in self.positions_data:
            row = self.positions_table.rowCount()
            self.positions_table.insertRow(row)
            
            # Calculate P/L percentage if needed
            pl = pos.get('profit', 0)
            total_pl += pl
            total_volume += pos.get('volume', 0)
            
            # Add items to the table
            self.positions_table.setItem(row, 0, QTableWidgetItem(str(pos.get('ticket', ''))))
            self.positions_table.setItem(row, 1, QTableWidgetItem(pos.get('symbol', '')))
            
            # Set position type with color coding
            pos_type = self.get_position_type(pos.get('type', 0))
            type_item = QTableWidgetItem(pos_type)
            type_item.setForeground(QColor("#4CAF50") if 'buy' in pos_type.lower() else QColor("#F44336"))
            self.positions_table.setItem(row, 2, type_item)
            
            self.positions_table.setItem(row, 3, QTableWidgetItem(f"{pos.get('volume', 0):.2f}"))
            self.positions_table.setItem(row, 4, QTableWidgetItem(f"{pos.get('price_open', 0):.5f}"))
            self.positions_table.setItem(row, 5, QTableWidgetItem(f"{pos.get('price_current', 0):.5f}"))
            self.positions_table.setItem(row, 6, QTableWidgetItem(f"{pos.get('sl', 0):.5f}" if pos.get('sl') > 0 else "-"))
            self.positions_table.setItem(row, 7, QTableWidgetItem(f"{pos.get('tp', 0):.5f}" if pos.get('tp') > 0 else "-"))
            
            # Color P/L based on profit/loss
            pl_item = QTableWidgetItem(f"{pl:.2f} {pos.get('currency', '')}")
            pl_item.setForeground(QColor("#4CAF50") if pl >= 0 else QColor("#F44336"))
            pl_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            self.positions_table.setItem(row, 8, pl_item)
            
            # Format time
            time_str = datetime.fromtimestamp(pos.get('time', 0)).strftime("%Y-%m-%d %H:%M:%S")
            self.positions_table.setItem(row, 9, QTableWidgetItem(time_str))
            
            # Store the full position data in the row
            for col in range(self.positions_table.columnCount()):
                if self.positions_table.item(row, col):
                    self.positions_table.item(row, col).setData(Qt.ItemDataRole.UserRole, pos)
        
        # Update summary
        self.summary_bar.setText(
            f"{len(self.positions_data)} positions | "
            f"Total P/L: ${total_pl:.2f} | "
            f"Total Volume: {total_volume:.2f} lots"
        )
    
    def refresh_positions(self):
        """Refresh the positions data"""
        # This would typically fetch fresh data from the trading platform
        # For now, we'll just reload the existing data
        self.load_positions()
    
    def show_context_menu(self, position):
        """Show context menu for the selected position"""
        menu = QMenu(self)
        
        close_action = QAction("Close Position", self)
        close_action.triggered.connect(self.close_selected_positions)
        
        modify_action = QAction("Modify Position", self)
        modify_action.triggered.connect(self.modify_position)
        
        details_action = QAction("View Details", self)
        details_action.triggered.connect(self.view_position_details)
        
        menu.addAction(close_action)
        menu.addAction(modify_action)
        menu.addSeparator()
        menu.addAction(details_action)
        
        menu.exec(self.positions_table.viewport().mapToGlobal(position))
    
    def close_selected_positions(self):
        """Close the selected positions"""
        selected_rows = set()
        
        # Get unique rows from selected items
        for item in self.positions_table.selectedItems():
            selected_rows.add(item.row())
        
        if not selected_rows:
            QMessageBox.warning(self, "No Selection", "Please select at least one position to close.")
            return
        
        # Confirm action
        reply = QMessageBox.question(
            self,
            "Confirm Close",
            f"Are you sure you want to close {len(selected_rows)} position(s)?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            for row in selected_rows:
                ticket_item = self.positions_table.item(row, 0)
                if ticket_item:
                    ticket = int(ticket_item.text())
                    self.close_position_signal.emit(ticket)
    
    def close_all_positions(self):
        """Close all open positions"""
        if not self.positions_data:
            return
            
        reply = QMessageBox.question(
            self,
            "Confirm Close All",
            f"Are you sure you want to close all {len(self.positions_data)} positions?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            for pos in self.positions_data:
                self.close_position_signal.emit(pos.get('ticket'))
    
    def modify_position(self):
        """Modify the selected position"""
        selected = self.positions_table.selectedItems()
        if not selected:
            QMessageBox.warning(self, "No Selection", "Please select a position to modify.")
            return
        
        # Get the first selected row's position data
        row = selected[0].row()
        pos_data = self.positions_table.item(row, 0).data(Qt.ItemDataRole.UserRole)
        
        if pos_data:
            self.modify_position_signal.emit(pos_data)
    
    def view_position_details(self):
        """View details of the selected position"""
        selected = self.positions_table.selectedItems()
        if not selected:
            return
        
        # Get the first selected row's position data
        row = selected[0].row()
        pos_data = self.positions_table.item(row, 0).data(Qt.ItemDataRole.UserRole)
        
        if pos_data:
            from .trade_details_dialog import TradeDetailsDialog
            dialog = TradeDetailsDialog(pos_data, self)
            dialog.exec()
    
    def get_position_type(self, type_code):
        """Convert position type code to string"""
        types = {
            0: "Buy",
            1: "Sell",
            2: "Buy Limit",
            3: "Sell Limit",
            4: "Buy Stop",
            5: "Sell Stop"
        }
        return types.get(type_code, f"Unknown ({type_code})")
    
    def closeEvent(self, event):
        """Handle dialog close event"""
        self.refresh_timer.stop()
        super().closeEvent(event)


if __name__ == "__main__":
    import sys
    from PyQt6.QtWidgets import QApplication
    import random
    import time
    
    # Sample positions data
    symbols = ["EURUSD", "GBPUSD", "USDJPY", "AUDUSD", "USDCAD", "NZDUSD", "USDCHF"]
    positions = []
    
    for i in range(10):
        symbol = random.choice(symbols)
        pos_type = random.choice([0, 1])  # 0 = buy, 1 = sell
        price = round(random.uniform(1.0, 1.5), 5)
        volume = round(random.uniform(0.1, 5.0), 2)
        
        positions.append({
            'ticket': 1000000 + i,
            'symbol': symbol,
            'type': pos_type,
            'volume': volume,
            'price_open': price,
            'price_current': price + (random.uniform(-0.001, 0.001) if pos_type == 0 else random.uniform(-0.001, 0.001)),
            'sl': price * (0.999 if pos_type == 0 else 1.001) if random.random() > 0.3 else 0,
            'tp': price * (1.002 if pos_type == 0 else 0.998) if random.random() > 0.3 else 0,
            'profit': random.uniform(-50, 100),
            'swap': random.uniform(-1, 1),
            'commission': random.uniform(0.5, 5.0),
            'currency': symbol[3:],
            'time': int(time.time()) - random.randint(60, 86400),
            'comment': f'Comment {i+1}'
        })
    
    app = QApplication(sys.argv)
    dialog = PositionsDialog(positions)
    dialog.show()
    sys.exit(app.exec())
