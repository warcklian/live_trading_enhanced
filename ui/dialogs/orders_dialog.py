from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem,
    QPushButton, QHeaderView, QLabel, QMessageBox, QMenu, QAbstractItemView
)
from PyQt6.QtCore import Qt, pyqtSignal, QTimer
from PyQt6.QtGui import QAction, QColor, QBrush
from datetime import datetime

class OrdersDialog(QDialog):
    """Dialog for managing pending orders"""
    
    # Signals
    delete_order_signal = pyqtSignal(int)  # ticket
    modify_order_signal = pyqtSignal(dict)  # order data
    
    def __init__(self, orders_data, parent=None):
        super().__init__(parent)
        self.orders_data = orders_data or []
        self.setWindowTitle("Pending Orders")
        self.setMinimumSize(1000, 500)
        
        self.init_ui()
        self.load_orders()
        
        # Setup auto-refresh
        self.refresh_timer = QTimer(self)
        self.refresh_timer.timeout.connect(self.refresh_orders)
        self.refresh_timer.start(5000)  # Refresh every 5 seconds
    
    def init_ui(self):
        """Initialize the UI components"""
        layout = QVBoxLayout(self)
        
        # Summary bar
        self.summary_bar = QLabel("0 pending orders")
        self.summary_bar.setStyleSheet("padding: 5px; background-color: #f0f0f0;")
        
        # Orders table
        self.orders_table = QTableWidget()
        self.orders_table.setColumnCount(10)
        self.orders_table.setHorizontalHeaderLabels([
            "Ticket", "Symbol", "Type", "Volume", "Price", "S/L", "T/P", "Current", "Time", "Comment"
        ])
        
        # Configure table
        self.orders_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.orders_table.setSelectionMode(QTableWidget.SelectionMode.ExtendedSelection)
        self.orders_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.orders_table.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.orders_table.customContextMenuRequested.connect(self.show_context_menu)
        
        # Set column widths
        header = self.orders_table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.ResizeMode.Interactive)
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)  # Ticket
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)  # Symbol
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)  # Type
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)  # Volume
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)  # Price
        header.setSectionResizeMode(5, QHeaderView.ResizeMode.ResizeToContents)  # S/L
        header.setSectionResizeMode(6, QHeaderView.ResizeMode.ResizeToContents)  # T/P
        header.setSectionResizeMode(7, QHeaderView.ResizeMode.ResizeToContents)  # Current
        header.setSectionResizeMode(8, QHeaderView.ResizeMode.ResizeToContents)  # Time
        header.setSectionResizeMode(9, QHeaderView.ResizeMode.Stretch)  # Comment
        
        # Buttons
        btn_layout = QHBoxLayout()
        
        self.refresh_btn = QPushButton("Refresh")
        self.refresh_btn.clicked.connect(self.refresh_orders)
        
        self.delete_btn = QPushButton("Delete")
        self.delete_btn.clicked.connect(self.delete_selected_orders)
        
        self.modify_btn = QPushButton("Modify")
        self.modify_btn.clicked.connect(self.modify_order)
        
        self.delete_all_btn = QPushButton("Delete All")
        self.delete_all_btn.clicked.connect(self.delete_all_orders)
        
        btn_layout.addWidget(self.refresh_btn)
        btn_layout.addStretch()
        btn_layout.addWidget(self.delete_btn)
        btn_layout.addWidget(self.modify_btn)
        btn_layout.addWidget(self.delete_all_btn)
        
        # Add to layout
        layout.addWidget(self.summary_bar)
        layout.addWidget(self.orders_table)
        layout.addLayout(btn_layout)
    
    def load_orders(self):
        """Load orders into the table"""
        self.orders_table.setRowCount(0)
        
        if not self.orders_data:
            self.summary_bar.setText("No pending orders")
            return
        
        for order in self.orders_data:
            row = self.orders_table.rowCount()
            self.orders_table.insertRow(row)
            
            # Add items to the table
            self.orders_table.setItem(row, 0, QTableWidgetItem(str(order.get('ticket', ''))))
            self.orders_table.setItem(row, 1, QTableWidgetItem(order.get('symbol', '')))
            
            # Set order type with color coding
            order_type = self.get_order_type(order.get('type', 0))
            type_item = QTableWidgetItem(order_type)
            type_item.setForeground(QColor("#4CAF50") if 'buy' in order_type.lower() else QColor("#F44336"))
            self.orders_table.setItem(row, 2, type_item)
            
            self.orders_table.setItem(row, 3, QTableWidgetItem(f"{order.get('volume', 0):.2f}"))
            self.orders_table.setItem(row, 4, QTableWidgetItem(f"{order.get('price_open', 0):.5f}"))
            self.orders_table.setItem(row, 5, QTableWidgetItem(f"{order.get('sl', 0):.5f}" if order.get('sl') > 0 else "-"))
            self.orders_table.setItem(row, 6, QTableWidgetItem(f"{order.get('tp', 0):.5f}" if order.get('tp') > 0 else "-"))
            self.orders_table.setItem(row, 7, QTableWidgetItem(f"{order.get('price_current', 0):.5f}"))
            
            # Format time
            time_str = datetime.fromtimestamp(order.get('time_setup', 0)).strftime("%Y-%m-%d %H:%M")
            self.orders_table.setItem(row, 8, QTableWidgetItem(time_str))
            
            # Comment
            self.orders_table.setItem(row, 9, QTableWidgetItem(order.get('comment', '')))
            
            # Store the full order data in the row
            for col in range(self.orders_table.columnCount()):
                if self.orders_table.item(row, col):
                    self.orders_table.item(row, col).setData(Qt.ItemDataRole.UserRole, order)
        
        # Update summary
        self.summary_bar.setText(f"{len(self.orders_data)} pending order(s)")
    
    def refresh_orders(self):
        """Refresh the orders data"""
        # This would typically fetch fresh data from the trading platform
        # For now, we'll just reload the existing data
        self.load_orders()
    
    def show_context_menu(self, position):
        """Show context menu for the selected order"""
        menu = QMenu(self)
        
        delete_action = QAction("Delete Order", self)
        delete_action.triggered.connect(self.delete_selected_orders)
        
        modify_action = QAction("Modify Order", self)
        modify_action.triggered.connect(self.modify_order)
        
        menu.addAction(delete_action)
        menu.addAction(modify_action)
        
        menu.exec(self.orders_table.viewport().mapToGlobal(position))
    
    def delete_selected_orders(self):
        """Delete the selected orders"""
        selected_rows = set()
        
        # Get unique rows from selected items
        for item in self.orders_table.selectedItems():
            selected_rows.add(item.row())
        
        if not selected_rows:
            QMessageBox.warning(self, "No Selection", "Please select at least one order to delete.")
            return
        
        # Confirm action
        reply = QMessageBox.question(
            self,
            "Confirm Delete",
            f"Are you sure you want to delete {len(selected_rows)} order(s)?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            for row in selected_rows:
                ticket_item = self.orders_table.item(row, 0)
                if ticket_item:
                    ticket = int(ticket_item.text())
                    self.delete_order_signal.emit(ticket)
    
    def delete_all_orders(self):
        """Delete all pending orders"""
        if not self.orders_data:
            return
            
        reply = QMessageBox.question(
            self,
            "Confirm Delete All",
            f"Are you sure you want to delete all {len(self.orders_data)} pending orders?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            for order in self.orders_data:
                self.delete_order_signal.emit(order.get('ticket'))
    
    def modify_order(self):
        """Modify the selected order"""
        selected = self.orders_table.selectedItems()
        if not selected:
            QMessageBox.warning(self, "No Selection", "Please select an order to modify.")
            return
        
        # Get the first selected row's order data
        row = selected[0].row()
        order_data = self.orders_table.item(row, 0).data(Qt.ItemDataRole.UserRole)
        
        if order_data:
            self.modify_order_signal.emit(order_data)
    
    def get_order_type(self, type_code):
        """Convert order type code to string"""
        types = {
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
    
    # Sample orders data
    symbols = ["EURUSD", "GBPUSD", "USDJPY", "AUDUSD", "USDCAD", "NZDUSD", "USDCHF"]
    orders = []
    
    for i in range(5):
        symbol = random.choice(symbols)
        order_type = random.choice([2, 3, 4, 5])  # 2=Buy Limit, 3=Sell Limit, 4=Buy Stop, 5=Sell Stop
        price = round(random.uniform(1.0, 1.5), 5)
        
        orders.append({
            'ticket': 2000000 + i,
            'symbol': symbol,
            'type': order_type,
            'volume': round(random.uniform(0.1, 5.0), 2),
            'price_open': price,
            'sl': price * (0.999 if order_type in [2, 4] else 1.001) if random.random() > 0.3 else 0,
            'tp': price * (1.002 if order_type in [2, 4] else 0.998) if random.random() > 0.3 else 0,
            'price_current': price + (random.uniform(-0.001, 0.001) if order_type in [2, 4] else random.uniform(-0.001, 0.001)),
            'time_setup': int(time.time()) - random.randint(60, 86400),
            'comment': f'Order {i+1}'
        })
    
    app = QApplication(sys.argv)
    dialog = OrdersDialog(orders)
    dialog.show()
    sys.exit(app.exec())
