# Live Trading Platform with PyQt

![Python](https://img.shields.io/badge/python-3.8+-blue.svg)
![PyQt6](https://img.shields.io/badge/PyQt6-6.0+-green.svg)
![MT5](https://img.shields.io/badge/MT5-Integration-orange.svg)

A professional-grade trading platform built with PyQt6 and MetaTrader 5 (MT5) integration, featuring advanced charting, risk management, and automated trading capabilities.

## 📋 Table of Contents

- [Overview](#-overview)
- [Features](#-features)
- [Project Structure](#-project-structure)
- [Installation](#-installation)
- [Configuration](#-configuration)
- [Usage](#-usage)
- [Modules Documentation](#-modules-documentation)
  - [Core Modules](#core-modules)
  - [UI Components](#ui-components)
  - [Dialogs](#dialogs)
  - [Utilities](#utilities)
- [Trading Strategy](#-trading-strategy)
- [Risk Management](#-risk-management)
- [Contributing](#-contributing)
- [License](#-license)

## 🌟 Overview

This trading platform is designed for both manual and automated trading with MetaTrader 5. It provides a user-friendly interface for market analysis, trade execution, and portfolio management, along with advanced features for algorithmic trading strategies.

## ✨ Features

- **Real-time Market Data**: Stream live prices and updates from MT5
- **Advanced Charting**: Interactive charts with technical indicators
- **Risk Management**: Comprehensive position sizing and risk controls
- **Multiple Timeframe Analysis**: View and analyze multiple timeframes simultaneously
- **Automated Trading**: Implement and backtest trading strategies
- **Portfolio Management**: Monitor and manage multiple trading accounts
- **Custom Indicators**: Extensible system for technical indicators
- **Backtesting**: Test strategies on historical data
- **Alerts & Notifications**: Custom price and indicator alerts

## 📁 Project Structure

```
live_trading_PyQt/
├── config/                 # Configuration files
│   ├── __init__.py
│   └── settings.py         # Application settings and constants
├── core/                   # Core trading functionality
│   ├── __init__.py
│   ├── mt5_client.py       # MT5 connection and operations
│   ├── risk_manager.py     # Enhanced risk management
│   ├── strategy.py         # Trading strategy implementation
│   └── models.py           # Data models and enums
├── ui/                     # UI components
│   ├── __init__.py
│   ├── main_window.py      # Main application window
│   ├── symbol_widget.py    # Widget for individual symbols
│   ├── chart_widget.py     # Chart visualization
│   └── dialogs/            # Various dialogs
│       ├── account_dialog.py
│       ├── add_symbol_dialog.py
│       ├── orders_dialog.py
│       ├── positions_dialog.py
│       ├── settings_dialog.py
│       └── trade_details_dialog.py
├── utils/                  # Utility functions
│   ├── __init__.py
│   ├── data_processing.py  # Data processing utilities
│   └── indicators.py       # Technical indicators
├── main.py                 # Application entry point
└── requirements_qt.txt     # Python dependencies
```

## 🛠️ Installation

1. **Prerequisites**
   - Python 3.8 or higher
   - MetaTrader 5 terminal installed
   - Git (optional, for development)

2. **Clone the repository**
   ```bash
   git clone https://github.com/yourusername/live_trading_PyQt.git
   cd live_trading_PyQt
   ```

3. **Create and activate a virtual environment (recommended)**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

4. **Install dependencies**
   ```bash
   pip install -r requirements_qt.txt
   ```

5. **Install MetaTrader 5 Python package**
   ```bash
   pip install MetaTrader5
   ```

## ⚙️ Configuration

1. **Edit the configuration**
   - Copy `config/settings.example.py` to `config/settings.py`
   - Update the settings according to your MT5 account and preferences

2. **MT5 Configuration**
   - Ensure MT5 is installed and running
   - Update the MT5 path in settings if not in the default location
   - Make sure your MT5 account has sufficient permissions for automated trading

## 🚀 Usage

1. **Start the application**
   ```bash
   python main.py
   ```

2. **Connect to MT5**
   - Click on 'File' > 'Connect to MT5'
   - Enter your MT5 account credentials
   - Select the server and click 'Connect'

3. **Add Symbols**
   - Click on 'Symbols' > 'Add Symbol'
   - Search and select the desired symbols
   - Configure the trading parameters and click 'Add'

4. **Analyze and Trade**
   - View real-time charts with technical indicators
   - Place manual trades using the trading panel
   - Monitor open positions and account status

## 📚 Modules Documentation

### Core Modules

#### `core/mt5_client.py`
Handles all communication with the MetaTrader 5 terminal.
- **Key Features**:
  - Establish and manage MT5 connection
  - Fetch historical and real-time market data
  - Execute trades and manage orders
  - Retrieve account information and positions
  - Subscribe to market data updates

#### `core/risk_manager.py`
Implements comprehensive risk management for trading operations.
- **Key Features**:
  - Position sizing based on account risk percentage
  - Stop loss and take profit calculation
  - Trailing stop functionality
  - Daily loss limits and drawdown protection
  - Risk/reward ratio management

#### `core/strategy.py`
Contains the trading strategy implementation.
- **Key Features**:
  - Signal generation based on technical indicators
  - Entry and exit rules
  - Backtesting framework
  - Performance metrics calculation
  - Strategy optimization

#### `core/models.py`
Defines the data models and enums used throughout the application.
- **Key Classes**:
  - `SymbolConfig`: Configuration for trading symbols
  - `Order`: Represents a trading order
  - `Position`: Represents an open position
  - `Trade`: Completed trade with P&L information
  - `AccountInfo`: Account details and statistics

### UI Components

#### `ui/main_window.py`
Main application window and entry point for the UI.
- **Key Features**:
  - Application menu and toolbar
  - Tabbed interface for multiple symbols
  - Status bar with connection and account information
  - Theme and layout management

#### `ui/symbol_widget.py`
Widget for displaying and interacting with a single trading symbol.
- **Key Features**:
  - Price chart with technical indicators
  - Order entry panel
  - Position management
  - Account summary

#### `ui/chart_widget.py`
Interactive charting component using Plotly.
- **Key Features**:
  - Multiple timeframe support
  - Technical indicators overlay
  - Drawing tools
  - Customizable appearance
  - Crosshair and measurement tools

### Dialogs

#### `ui/dialogs/account_dialog.py`
Account information and management dialog.
- **Key Features**:
  - Account balance and equity display
  - Transaction history
  - Account settings
  - Deposit/withdrawal functionality

#### `ui/dialogs/add_symbol_dialog.py`
Dialog for adding new trading symbols.
- **Key Features**:
  - Symbol search and selection
  - Timeframe selection
  - Risk parameters configuration
  - Strategy assignment

#### `ui/dialogs/orders_dialog.py`
Management of pending orders.
- **Key Features**:
  - View all pending orders
  - Modify or cancel orders
  - Order history
  - Filtering and sorting

#### `ui/dialogs/positions_dialog.py`
Management of open positions.
- **Key Features**:
  - View all open positions
  - Close or modify positions
  - Position details
  - Real-time P&L calculation

#### `ui/dialogs/settings_dialog.py`
Application settings configuration.
- **Key Features**:
  - General application settings
  - Connection parameters
  - Risk management settings
  - Chart and display options

#### `ui/dialogs/trade_details_dialog.py`
Detailed view of a specific trade.
- **Key Features**:
  - Trade execution details
  - Performance metrics
  - Chart of trade progression
  - Notes and tags

### Utilities

#### `utils/indicators.py`
Technical indicators implementation.
- **Key Indicators**:
  - Moving Averages (SMA, EMA, WMA)
  - Oscillators (RSI, MACD, Stochastics)
  - Volatility indicators (Bollinger Bands, ATR)
  - Volume indicators
  - Custom indicator support

#### `utils/data_processing.py`
Data manipulation and processing utilities.
- **Key Features**:
  - Data cleaning and normalization
  - Resampling and aggregation
  - Feature engineering
  - Outlier detection and handling
  - Performance optimization

## 📈 Trading Strategy

The platform implements a sophisticated trading strategy with the following components:

1. **Signal Generation**
   - Technical indicators analysis
   - Price action patterns
   - Volume analysis
   - Market regime detection

2. **Risk Management**
   - Position sizing based on account risk
   - Stop loss and take profit levels
   - Trailing stops
   - Maximum drawdown protection

3. **Execution**
   - Smart order routing
   - Slippage control
   - Partial fills handling
   - Order type optimization

## 🛡️ Risk Management

The platform includes a comprehensive risk management system:

1. **Pre-Trade Risk**
   - Maximum position size limits
   - Maximum number of open positions
   - Trading session restrictions
   - News event filters

2. **Real-Time Risk**
   - Margin level monitoring
   - Drawdown limits
   - Volatility adjustments
   - Correlation analysis

3. **Post-Trade Analysis**
   - Trade journaling
   - Performance metrics
   - Risk-adjusted returns
   - Strategy optimization

## 🤝 Contributing

Contributions are welcome! Please follow these steps:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 📧 Contact

For questions or support, please contact [your-email@example.com](mailto:your-email@example.com)

---

<div align="center">
  <sub>Built with ❤️ and ☕ by Your Name</sub>
</div>
