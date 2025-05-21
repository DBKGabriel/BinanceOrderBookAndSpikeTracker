import threading

class OrderBookModel:
    def __init__(self, symbols):
        """
        Initialize the order book model.
        
        Args:
            symbols: List of cryptocurrency symbols to track
        """
        self.symbols = [symbol.upper() for symbol in symbols]
        self.order_book_history = {symbol: [] for symbol in self.symbols}
        self.lock = threading.Lock()
    
    def update_order_book(self, symbol, timestamp, bids, asks):
        """
        Update the order book for a symbol.
        
        Args:
            symbol: Cryptocurrency symbol
            timestamp: Update timestamp
            bids: List of bids [price, amount]
            asks: List of asks [price, amount]
        """
        symbol = symbol.upper()
        with self.lock:
            if symbol not in self.order_book_history:
                return
            
            self.order_book_history[symbol].append({
                "timestamp": timestamp,
                "bids": bids[:5],  # Store top 5 bids
                "asks": asks[:5]   # Store top 5 asks
            })
    
    def get_latest_order_book(self, symbol):
        """Get the latest order book for a symbol."""
        symbol = symbol.upper()
        with self.lock:
            if symbol not in self.order_book_history or not self.order_book_history[symbol]:
                return None
            return self.order_book_history[symbol][-1]
