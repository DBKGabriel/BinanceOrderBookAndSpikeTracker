from collections import deque
import csv
from datetime import datetime
import threading

class TradeModel:
    def __init__(self, symbols, max_trades=500):
        """
        Initialize the trade model.
        
        Args:
            symbols: List of cryptocurrency symbols to track
            max_trades: Maximum number of trades to keep in memory per symbol
        """
        self.symbols = [symbol.upper() for symbol in symbols]
        self.max_trades = max_trades
        self.trade_history = {symbol: deque(maxlen=max_trades) for symbol in self.symbols}
        self.last_trade_price = {symbol: None for symbol in self.symbols}
        self.trade_occurred_in_bin = {symbol: False for symbol in self.symbols}
        self.lock = threading.Lock()
    
    def add_trade(self, symbol, price, volume, timestamp):
        """
        Add a trade to the history.
        
        Args:
            symbol: Cryptocurrency symbol
            price: Trade price
            volume: Trade volume
            timestamp: Trade timestamp
            
        Returns:
            Boolean indicating if max trades has been reached
        """
        symbol = symbol.upper()
        with self.lock:
            if symbol not in self.trade_history:
                return False
            
            self.trade_history[symbol].append({
                "price": price,
                "volume": volume,
                "time": timestamp
            })
            self.last_trade_price[symbol] = price
            self.trade_occurred_in_bin[symbol] = True
            
            return len(self.trade_history[symbol]) >= self.max_trades
    
    def get_latest_trade(self, symbol):
        """Get the latest trade for a symbol."""
        symbol = symbol.upper()
        with self.lock:
            if symbol not in self.trade_history or not self.trade_history[symbol]:
                return None
            return self.trade_history[symbol][-1]
    
    def get_trades(self, symbol):
        """Get all trades for a symbol."""
        symbol = symbol.upper()
        with self.lock:
            if symbol not in self.trade_history:
                return []
            return list(self.trade_history[symbol])
    
    def get_trade_status(self, symbol):
        """Check if a trade occurred in the current bin for a symbol."""
        symbol = symbol.upper()
        with self.lock:
            return self.trade_occurred_in_bin.get(symbol, False)
    
    def reset_trade_status(self, symbol):
        """Reset the trade status for a symbol."""
        symbol = symbol.upper()
        with self.lock:
            self.trade_occurred_in_bin[symbol] = False
    
    def get_last_price(self, symbol):
        """Get the last trade price for a symbol."""
        symbol = symbol.upper()
        with self.lock:
            return self.last_trade_price.get(symbol)
    
    def save_trades_to_csv(self, symbol):
        """
        Save trades for a symbol to a CSV file.
        
        Args:
            symbol: Cryptocurrency symbol
            
        Returns:
            Filename or None if no trades to save
        """
        symbol = symbol.upper()
        with self.lock:
            if symbol not in self.trade_history or not self.trade_history[symbol]:
                return None
            
            trades_to_save = list(self.trade_history[symbol])
            self.trade_history[symbol].clear()
        
        if not trades_to_save:
            return None
            
        filename = f"trade_history_{symbol}.csv"
        file_exists = False
        
        try:
            with open(filename, "r") as _:
                file_exists = True
        except FileNotFoundError:
            pass
            
        with open(filename, "a", newline="") as f:
            writer = csv.writer(f)
            if not file_exists:
                writer.writerow(["Time (ET)", "Symbol", "Price", "Volume"])
            for trade in trades_to_save:
                writer.writerow([trade["time"], symbol, trade["price"], trade["volume"]])
        
        return filename
