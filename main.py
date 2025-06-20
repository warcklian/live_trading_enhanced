import sys
import os
from PyQt6.QtWidgets import QApplication, QMessageBox, QInputDialog, QLineEdit
from PyQt6.QtCore import QTimer, QSettings
from ui.main_window import MainWindow
from core.mt5_client import MT5Client

def get_mt5_path():
    """Try to find the default MT5 terminal path"""
    # Try to use the default MT5 installation
    try:
        import winreg
        
        # Try to get the installation path from registry
        try:
            # 64-bit registry
            with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, 
                              r"SOFTWARE\MetaQuotes\MetaTrader 5", 0, 
                              winreg.KEY_READ | winreg.KEY_WOW64_64KEY) as key:
                path = winreg.QueryValueEx(key, 'Path')[0]
                exe_path = os.path.join(path, 'terminal64.exe' if os.name == 'nt' else 'terminal')
                if os.path.exists(exe_path):
                    return exe_path
        except WindowsError:
            try:
                # 32-bit registry
                with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, 
                                  r"SOFTWARE\MetaQuotes\MetaTrader 5") as key:
                    path = winreg.QueryValueEx(key, 'Path')[0]
                    exe_path = os.path.join(path, 'terminal64.exe' if os.name == 'nt' else 'terminal')
                    if os.path.exists(exe_path):
                        return exe_path
            except WindowsError:
                pass
                
        # If registry method fails, try common paths
        common_paths = [
            os.path.join(os.environ.get('APPDATA', ''), 'MetaQuotes', 'Terminal', 'D0E8209F77C8CF37AD8BF550E51FF075', 'terminal64.exe'),
            os.path.join(os.environ.get('APPDATA', ''), 'MetaQuotes', 'Terminal', 'D0E8209F77C8CF37AD8BF550E51FF075', 'terminal.exe'),
            r"C:\Program Files\MetaTrader 5\terminal64.exe",
            r"C:\Program Files (x86)\MetaTrader 5\terminal64.exe",
            r"C:\Program Files\MetaTrader 5\terminal.exe",
            r"C:\Program Files (x86)\MetaTrader 5\terminal.exe"
        ]
        
        for path in common_paths:
            if os.path.exists(path):
                return path
                
    except Exception as e:
        print(f"Warning: Could not automatically detect MT5 path: {e}")
    
    # If all else fails, prompt the user
    app = QApplication.instance() or QApplication(sys.argv)
    path, ok = QInputDialog.getText(
        None,
        "MT5 Terminal Path",
        "Enter path to MetaTrader 5 terminal executable:",
        QLineEdit.EchoMode.Normal,
        r"C:\Program Files\MetaQuotes\Terminal\D0E8209F77C8CF37AD8BF550E51FF075\terminal64.exe"
    )
    
    if ok and path and os.path.exists(path):
        return path
    return ""

def main():
    # Initialize the application
    app = QApplication(sys.argv)
    app.setApplicationName("SMC Strategy Live Trading")
    app.setOrganizationName("SMC Trading")
    
    # Load saved settings
    settings = QSettings("SMC Trading", "Live Trading")
    mt5_path = settings.value("mt5_path", "", type=str)
    mt5_server = settings.value("mt5_server", "", type=str)
    mt5_login = settings.value("mt5_login", "", type=str)
    
    # If no saved path, try to find it
    if not mt5_path or not os.path.exists(mt5_path):
        mt5_path = get_mt5_path()
        if not mt5_path:
            QMessageBox.critical(
                None,
                "MT5 Not Found",
                "Could not find MetaTrader 5 terminal. Please install MT5 and try again."
            )
            return 1
        settings.setValue("mt5_path", mt5_path)
    
    # Initialize MT5 client
    mt5_client = MT5Client(
        server=mt5_server,
        login=int(mt5_login) if mt5_login and mt5_login.isdigit() else None,
        password="",  # Will be prompted if needed
        path=mt5_path
    )
    
    # Try to connect to MT5
    if not mt5_client.initialize():
        # If connection fails, prompt for credentials
        from PyQt6.QtWidgets import QDialog, QVBoxLayout, QLabel, QLineEdit, QDialogButtonBox, QFormLayout
        
        class LoginDialog(QDialog):
            def __init__(self, parent=None):
                super().__init__(parent)
                self.setWindowTitle("MT5 Login")
                self.setMinimumWidth(300)
                
                layout = QVBoxLayout(self)
                form = QFormLayout()
                
                self.server_edit = QLineEdit(mt5_server or "")
                self.login_edit = QLineEdit(mt5_login or "")
                self.password_edit = QLineEdit()
                self.password_edit.setEchoMode(QLineEdit.EchoMode.Password)
                
                form.addRow("Server:", self.server_edit)
                form.addRow("Login:", self.login_edit)
                form.addRow("Password:", self.password_edit)
                
                buttons = QDialogButtonBox(
                    QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
                )
                buttons.accepted.connect(self.accept)
                buttons.rejected.connect(self.reject)
                
                layout.addLayout(form)
                layout.addWidget(buttons)
            
            def get_credentials(self):
                return {
                    'server': self.server_edit.text().strip(),
                    'login': self.login_edit.text().strip(),
                    'password': self.password_edit.text()
                }
        
        dialog = LoginDialog()
        if dialog.exec() == QDialog.DialogCode.Accepted:
            credentials = dialog.get_credentials()
            
            # Save credentials for next time
            settings.setValue("mt5_server", credentials['server'])
            settings.setValue("mt5_login", credentials['login'])
            
            # Try to connect with new credentials
            mt5_client = MT5Client(
                server=credentials['server'],
                login=int(credentials['login']) if credentials['login'].isdigit() else None,
                password=credentials['password'],
                path=mt5_path
            )
            
            if not mt5_client.initialize():
                QMessageBox.critical(
                    None,
                    "Connection Failed",
                    f"Failed to connect to MT5. Error: {mt5.last_error()}"
                )
                return 1
        else:
            return 0  # User cancelled
    
    # Create and show the main window
    window = MainWindow(mt5_client)
    window.show()
    
    # Start the application event loop
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
