import MetaTrader5 as mt5
from datetime import datetime, timedelta
import pandas as pd
from typing import Optional, List, Dict, Any, Tuple
import time

class MT5Client:
    def __init__(self, server: str = "", login: int = None, password: str = "", path: str = ""):
        """
        Initialize MT5 client with connection parameters
        
        Args:
            server: MT5 server name
            login: MT5 account number
            password: MT5 account password
            path: Path to MetaTrader5 terminal executable (optional)
        """
        self.server = server
        self.login = login
        self.password = password
        self.path = path
        self.initialized = False
        self.symbols_info = {}
        
    def get_available_symbols(self) -> List[str]:
        """
        Get list of available symbols from MT5
        
        Returns:
            List of available symbol names
        """
        if not self.initialized:
            print("MT5 not initialized. Cannot get symbols.")
            return []
            
        try:
            # Get all symbols and ensure they are synchronized
            symbols = mt5.symbols_get()
            if symbols is None:
                error = mt5.last_error()
                print(f"Failed to get symbols. Error: {error}")
                return []
                
            # Get only synchronized symbols
            available_symbols = []
            for symbol in symbols:
                # Intentar sincronizar el símbolo
                if not mt5.symbol_select(symbol.name, True):
                    print(f"Failed to synchronize {symbol.name}")
                    continue
                    
                # Verificar que el símbolo está realmente disponible
                symbol_info = mt5.symbol_info(symbol.name)
                if symbol_info is not None and symbol_info.visible:
                    available_symbols.append(symbol.name)
            
            if not available_symbols:
                print("Warning: No synchronized symbols found. Make sure you're connected to your broker.")
            else:
                # Sort alphabetically
                available_symbols.sort()
                print(f"Found {len(available_symbols)} synchronized symbols")
                print("First few available symbols:", available_symbols[:5])
                
            return available_symbols
            
        except Exception as e:
            print(f"Error getting available symbols: {str(e)}")
            return []
        
    def check_new_bar(self, symbol: str, timeframe: str, last_bar_time: datetime) -> bool:
        """Verifica si ha comenzado una nueva vela según el timeframe
        
        Args:
            symbol: Símbolo a verificar
            timeframe: Timeframe en formato string ('M1', 'M5', 'M15', etc)
            last_bar_time: Tiempo de la última vela procesada
            
        Returns:
            bool: True si hay una nueva vela, False en caso contrario
        """
        # Convertir timeframe a minutos
        timeframe_minutes = self._timeframe_to_minutes(timeframe)
        if timeframe_minutes == 0:
            return False
            
        current_time = datetime.now()
        
        # Calcular el tiempo transcurrido desde la última barra
        elapsed_minutes = (current_time - last_bar_time).total_seconds() / 60
        
        # Verificar si ha pasado suficiente tiempo para una nueva vela
        if elapsed_minutes >= timeframe_minutes:
            # Calcular el timestamp exacto del inicio de la nueva barra
            current_bar_start = current_time - timedelta(
                minutes=current_time.minute % timeframe_minutes,
                seconds=current_time.second,
                microseconds=current_time.microsecond
            )
            return current_bar_start > last_bar_time
            
        return False
        
    def _timeframe_to_minutes(self, timeframe: str) -> int:
        """Convierte el timeframe a minutos"""
        timeframe_map = {
            'M1': 1,
            'M5': 5,
            'M15': 15,
            'M30': 30,
            'H1': 60,
            'H4': 240,
            'D1': 1440,
            'W1': 10080,
            'MN1': 43200
        }
        return timeframe_map.get(timeframe.upper(), 0)
        
    def initialize(self) -> bool:
        """Initialize connection to MT5 terminal"""
        # Shutdown any existing connection
        if self.initialized:
            mt5.shutdown()
            self.initialized = False

        # Initialize MT5
        if not mt5.initialize(path=self.path):
            print(f"MT5 initialize() failed, error code = {mt5.last_error()}")
            return False
            
        # If credentials are provided, attempt to log in
        if self.login and self.password and self.server:
            print(f"Attempting to connect to account {self.login} on {self.server}...")
            
            # Try to log in
            authorized = mt5.login(
                login=self.login,
                password=self.password,
                server=self.server
            )
            
            if not authorized:
                print(f"Login failed, error code = {mt5.last_error()}")
                mt5.shutdown()
                return False
                
            print(f"Successfully connected to account {self.login}")
        else:
            print("Warning: No login credentials provided. Using existing MT5 connection.")

        # Verify terminal info and connection
        terminal_info = mt5.terminal_info()
        if terminal_info is None:
            print("Failed to get terminal info")
            mt5.shutdown()
            return False

        # Enable symbols synchronization
        print("Synchronizing symbols...")
        symbols = mt5.symbols_get()
        if symbols is None:
            print("Failed to get symbols")
            mt5.shutdown()
            return False

        # Force synchronization for each symbol
        synchronized_count = 0
        for symbol in symbols:
            if mt5.symbol_select(symbol.name, True):
                synchronized_count += 1
            else:
                print(f"Failed to synchronize {symbol.name}")

        if synchronized_count == 0:
            print("Failed to synchronize any symbols")
            mt5.shutdown()
            return False

        print(f"Connected to {terminal_info.company}")
        print(f"Build: {terminal_info.build}")
        print(f"Synchronized {len(symbols)} symbols")
            
        self.initialized = True
        return True
    
    def shutdown(self) -> None:
        """Shutdown MT5 connection"""
        if self.initialized:
            mt5.shutdown()
            self.initialized = False
    

    
    def _get_timeframe_constant(self, timeframe: str) -> int:
        """
        Convert timeframe string to MT5 timeframe constant
        
        Args:
            timeframe: Timeframe string (e.g., 'M1', 'M5', 'M15', 'H1', 'H4', 'D1', 'W1', 'MN1')
            
        Returns:
            MT5 timeframe constant (e.g., mt5.TIMEFRAME_M15)
        """
        timeframe_map = {
            'M1': mt5.TIMEFRAME_M1,
            'M5': mt5.TIMEFRAME_M5,
            'M15': mt5.TIMEFRAME_M15,
            'M30': mt5.TIMEFRAME_M30,
            'H1': mt5.TIMEFRAME_H1,
            'H4': mt5.TIMEFRAME_H4,
            'D1': mt5.TIMEFRAME_D1,
            'W1': mt5.TIMEFRAME_W1,
            'MN1': mt5.TIMEFRAME_MN1
        }
        return timeframe_map.get(timeframe.upper(), mt5.TIMEFRAME_M15)  # Default to M15 if not found
    
    def get_historical_data(self, symbol: str, timeframe, 
                              count: int = 1000) -> Optional[pd.DataFrame]:
        """
        Get historical data for a symbol
        
        Args:
            symbol: Symbol name (e.g., 'XAUUSD' for gold)
            timeframe: MT5 timeframe constant (e.g., mt5.TIMEFRAME_M15) or string (e.g., 'M15')
            count: Number of bars to retrieve
            
        Returns:
            DataFrame with historical data or None if error
        """
        if not self.initialized:
            print("Error: MT5 not initialized")
            return None
            
        try:
            # Convert string timeframe to MT5 constant if needed
            if isinstance(timeframe, str):
                timeframe = self._get_timeframe_constant(timeframe)
            
            # First, try to select the symbol
            selected = mt5.symbol_select(symbol, True)
            if not selected:
                error = mt5.last_error()
                print(f"Failed to select {symbol}. Error: {error}")
                print("Available symbols:", mt5.symbols_get())
                return None
                
            print(f"Successfully selected {symbol}")
            
            # Get symbol info to check if it's valid
            symbol_info = mt5.symbol_info(symbol)
            if symbol_info is None:
                print(f"No symbol info for {symbol}")
                return None
                
            print(f"Symbol info for {symbol}:")
            print(f"  Bid: {symbol_info.bid}, Ask: {symbol_info.ask}")
            print(f"  Spread: {symbol_info.ask - symbol_info.bid if symbol_info.ask and symbol_info.bid else 'N/A'}")
            
            # Try to get rates
            print(f"Requesting {count} bars of data for {symbol}...")
            rates = mt5.copy_rates_from_pos(symbol, timeframe, 0, count)
            
            if rates is None or len(rates) == 0:
                error = mt5.last_error()
                print(f"No data received for {symbol}. Error: {error}")
                print("Trying with a smaller count...")
                
                # Try with smaller count if first attempt fails
                rates = mt5.copy_rates_from_pos(symbol, timeframe, 0, 100)
                if rates is None or len(rates) == 0:
                    error = mt5.last_error()
                    print(f"Still no data. Last error: {error}")
                    return None
                    
            print(f"Successfully retrieved {len(rates)} bars for {symbol}")
            
            # Convert to DataFrame
            df = pd.DataFrame(rates)
            if len(df) == 0:
                print("Warning: Empty DataFrame after conversion")
                return None
                
            # Convert timestamp to datetime
            df['time'] = pd.to_datetime(df['time'], unit='s')
            df.set_index('time', inplace=True)
            
            print(f"Data for {symbol} (first 5 rows):\n", df.head())
            return df
            
        except Exception as e:
            print(f"Error in get_historical_data for {symbol}: {str(e)}")
            import traceback
            traceback.print_exc()
            return None
    
    def get_live_price(self, symbol: str) -> Optional[Dict[str, float]]:
        """Get current price for a symbol"""
        if not self.initialized:
            return None
            
        tick = mt5.symbol_info_tick(symbol)
        if tick is None:
            return None
            
        return {
            'bid': tick.bid,
            'ask': tick.ask,
            'last': tick.last,
            'volume': tick.volume,
            'time': pd.to_datetime(tick.time, unit='s')
        }
    
    def place_order(self, symbol: str, order_type: str, volume: float, 
                   price: Optional[float] = None, sl: float = 0.0, 
                   tp: float = 0.0, comment: str = "") -> Optional[int]:
        """
        Place an order in MT5
        
        Args:
            symbol: Symbol to trade
            order_type: 'buy', 'sell', 'buy_limit', 'sell_limit', 'buy_stop', 'sell_stop'
            volume: Trade volume in lots
            price: Execution price (None for market orders)
            sl: Stop loss price
            tp: Take profit price
            comment: Order comment
            
        Returns:
            Order ticket if successful, None otherwise
        """
        if not self.initialized:
            return None
            
        # Prepare the request
        request = {
            "symbol": symbol,
            "volume": volume,
            "sl": sl,
            "tp": tp,
            "deviation": 10,
            "magic": 234000,
            "comment": comment,
            "type_time": mt5.ORDER_TIME_GTC,
            "type_filling": mt5.ORDER_FILLING_IOC,
        }
        
        # Set order type
        order_types = {
            'buy': mt5.ORDER_TYPE_BUY,
            'sell': mt5.ORDER_TYPE_SELL,
            'buy_limit': mt5.ORDER_TYPE_BUY_LIMIT,
            'sell_limit': mt5.ORDER_TYPE_SELL_LIMIT,
            'buy_stop': mt5.ORDER_TYPE_BUY_STOP,
            'sell_stop': mt5.ORDER_TYPE_SELL_STOP
        }
        
        if order_type not in order_types:
            print(f"Invalid order type: {order_type}")
            return None
            
        request["type"] = order_types[order_type]
        
        # Set price if provided, otherwise use market price
        if price is not None:
            request["price"] = price
        
        # Send the order
        result = mt5.order_send(request)
        
        if result.retcode != mt5.TRADE_RETCODE_DONE:
            print(f"Order failed: {result.comment}")
            return None
            
        return result.order
    
    def get_open_positions(self, symbol: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Get open positions
        
        Args:
            symbol: Optional symbol filter
            
        Returns:
            List of open positions
        """
        if not self.initialized:
            return []
            
        positions = mt5.positions_get(symbol=symbol) if symbol else mt5.positions_get()
        if positions is None:
            return []
            
        return [{
            'ticket': pos.ticket,
            'symbol': pos.symbol,
            'type': 'buy' if pos.type == mt5.ORDER_TYPE_BUY else 'sell',
            'volume': pos.volume,
            'open_price': pos.price_open,
            'sl': pos.sl,
            'tp': pos.tp,
            'profit': pos.profit,
            'time': pd.to_datetime(pos.time, unit='s')
        } for pos in positions]
    
    def close_position(self, ticket: int) -> bool:
        """
        Close an open position
        
        Args:
            ticket: Position ticket number
            
        Returns:
            True if successful, False otherwise
        """
        if not self.initialized:
            return False
            
        # Get the position
        position = mt5.positions_get(ticket=ticket)
        if not position:
            print(f"Position {ticket} not found")
            return False
            
        position = position[0]
        
        # Prepare the close request
        request = {
            "action": mt5.TRADE_ACTION_DEAL,
            "symbol": position.symbol,
            "volume": position.volume,
            "type": mt5.ORDER_TYPE_SELL if position.type == mt5.ORDER_TYPE_BUY else mt5.ORDER_TYPE_BUY,
            "position": position.ticket,
            "deviation": 10,
            "magic": 234000,
            "comment": "Closed by Python script",
            "type_time": mt5.ORDER_TIME_GTC,
            "type_filling": mt5.ORDER_FILLING_IOC,
        }
        
        # Send the close request
        result = mt5.order_send(request)
        
        if result.retcode != mt5.TRADE_RETCODE_DONE:
            print(f"Close position failed: {result.comment}")
            return False
            
        return True
    
    def modify_position(self, ticket: int, sl: Optional[float] = None, 
                        tp: Optional[float] = None) -> bool:
        """
        Modify stop loss and/or take profit of an open position
        
        Args:
            ticket: Position ticket number
            sl: New stop loss price (None to keep unchanged)
            tp: New take profit price (None to keep unchanged)
            
        Returns:
            True if successful, False otherwise
        """
        if not self.initialized:
            return False
            
        # Get the position
        position = mt5.positions_get(ticket=ticket)
        if not position:
            print(f"Position {ticket} not found")
            return False
            
        position = position[0]
        
        # If both SL and TP are None, nothing to do
        if sl is None and tp is None:
            return True
            
        # Prepare the modification request
        request = {
            "action": mt5.TRADE_ACTION_SLTP,
            "symbol": position.symbol,
            "position": position.ticket,
            "sl": sl if sl is not None else position.sl,
            "tp": tp if tp is not None else position.tp,
        }
        
        # Send the modification request
        result = mt5.order_send(request)
        
        if result.retcode != mt5.TRADE_RETCODE_DONE:
            print(f"Modify position failed: {result.comment}")
            return False
            
        return True
