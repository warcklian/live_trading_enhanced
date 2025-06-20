"""
Application-wide settings and configuration.
"""
import os
from pathlib import Path
from typing import Dict, Any, Optional
import json

# Base directory
BASE_DIR = Path(__file__).parent.parent
DATA_DIR = BASE_DIR / 'data'
LOG_DIR = BASE_DIR / 'logs'

# Ensure directories exist
for directory in [DATA_DIR, LOG_DIR]:
    directory.mkdir(exist_ok=True, parents=True)

# Default settings
DEFAULT_SETTINGS = {
    'app': {
        'name': 'Live Trading App',
        'version': '1.0.0',
        'theme': 'dark',
        'language': 'en',
        'auto_save': True,
        'auto_save_interval': 5,  # minutes
    },
    'trading': {
        'default_lot_size': 0.1,
        'default_risk_per_trade': 1.0,  # %
        'default_slippage': 3,  # pips
        'max_open_positions': 10,
        'max_position_size': 10.0,  # lots
    },
    'risk_management': {
        'use_stop_loss': True,
        'use_take_profit': True,
        'default_risk_reward': 2.0,
        'use_trailing_stop': False,
        'trailing_stop_atr': 2.0,
        'use_break_even': True,
        'break_even_atr': 1.0,
        'max_daily_drawdown': 5.0,  # %
        'max_daily_trades': 50,
    },
    'mt5': {
        'path': 'C:\\Program Files\\MetaTrader 5\\terminal64.exe',
        'server': '',
        'login': '',
        'password': '',
        'timeout': 30,  # seconds
        'auto_connect': False,
        'demo_account': True,
    },
    'charts': {
        'theme': 'dark',
        'show_volume': True,
        'show_grid': True,
        'show_indicators': True,
        'default_timeframe': 'M15',
        'price_precision': 5,
    },
}

class Settings:
    """Application settings manager."""
    
    _instance = None
    _settings_file = DATA_DIR / 'settings.json'
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(Settings, cls).__new__(cls)
            cls._instance._settings = {}
            cls._instance.load()
        return cls._instance
    
    def load(self) -> None:
        """Load settings from file or use defaults."""
        try:
            if self._settings_file.exists():
                with open(self._settings_file, 'r') as f:
                    self._settings = json.load(f)
            else:
                self._settings = DEFAULT_SETTINGS.copy()
                self.save()
        except Exception as e:
            print(f"Error loading settings: {e}")
            self._settings = DEFAULT_SETTINGS.copy()
    
    def save(self) -> None:
        """Save current settings to file."""
        try:
            with open(self._settings_file, 'w') as f:
                json.dump(self._settings, f, indent=4)
        except Exception as e:
            print(f"Error saving settings: {e}")
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get a setting value by dot notation key."""
        keys = key.split('.')
        value = self._settings
        
        try:
            for k in keys:
                value = value[k]
            return value
        except (KeyError, TypeError):
            return default
    
    def set(self, key: str, value: Any) -> None:
        """Set a setting value by dot notation key."""
        keys = key.split('.')
        settings = self._settings
        
        for k in keys[:-1]:
            if k not in settings:
                settings[k] = {}
            settings = settings[k]
        
        settings[keys[-1]] = value
        self.save()
    
    def reset(self) -> None:
        """Reset all settings to defaults."""
        self._settings = DEFAULT_SETTINGS.copy()
        self.save()

# Global settings instance
settings = Settings()

# Helper functions
def get_setting(key: str, default: Any = None) -> Any:
    """Helper function to get a setting."""
    return settings.get(key, default)

def set_setting(key: str, value: Any) -> None:
    """Helper function to set a setting."""
    settings.set(key, value)

def reset_settings() -> None:
    """Helper function to reset all settings to defaults."""
    settings.reset()
