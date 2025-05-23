import websocket
import json
import threading
from datetime import datetime
import pytz
from utils.time_utils import utc_to_eastern, format_timestamp

class WebSocketController:
    def __init__(self, trade_model, order_book_model, db_manager, console_view, visualizer=None):
        """
        Initialize the WebSocket controller.
        
        Args:
            trade_model: Model for trade data
            order_book_model: Model for order book data
            db_manager: Database manager
            console_view: Console view for output
            visualizer: Optional visualization view
        """
        self.trade_model = trade_model
        self.order_book_model = order_book_model
        self.db_manager = db_manager
        self.console_view = console_view
        self.visualizer = visualizer
        self.ws = None
        self.symbols = trade_model.symbols
        self.utc = pytz.utc
        self.eastern = pytz.timezone("US/Eastern")
        self.exit_flag = threading.Event()
    
    def connect(self):
        """Connect to the Binance.US WebSocket API."""
        # Build streams string
        lower_symbols = [symbol.lower() for symbol in self.symbols]
        streams = "/".join(
            [f"{symbol}@trade" for symbol in lower_symbols] +
            [f"{symbol}@depth5" for symbol in lower_symbols]
        )
        ws_url = f"wss://stream.binance.us:9443/stream?streams={streams}"
        
        # Create WebSocket
        self.ws = websocket.WebSocketApp(
            ws_url,
            on_open=self.on_open,
            on_message=self.on_message,
            on_error=self.on_error,
            on_close=self.on_close
        )
        
        # Start WebSocket in a separate thread
        threading.Thread(target=self.ws.run_forever, daemon=True).start()
    
    def on_open(self, ws):
        """Handle WebSocket open event."""
        self.console_view.print_success("Connected to Binance.US combined stream.")
        self.console_view.print_info("WebSocket connected and receiving data.", persistent=True)

    def on_message(self, ws, message):
        """Handle incoming WebSocket messages."""
        data = json.loads(message)
        
        if data.get("stream"):
            stream_name = data["stream"]
            symbol = stream_name.split("@")[0].upper()
            data = data.get("data", {})
        else:
            symbol = data.get("s", "").upper()
        
        if symbol not in self.symbols:
            return
        
        if data.get("e") == "trade":
            self.process_trade(symbol, data)
        elif data.get("e") == "depthUpdate" or ("bids" in data and "asks" in data):
            self.process_order_book(symbol, data)
    
    def process_trade(self, symbol, data):
        """Process a trade message."""
        timestamp_utc = datetime.utcfromtimestamp(data["T"] / 1000).replace(tzinfo=self.utc)
        timestamp_et = timestamp_utc.astimezone(self.eastern).strftime("%Y-%m-%d %H:%M:%S")
        price = float(data["p"])
        volume = float(data["q"])
        
        # Add trade to model
        max_reached = self.trade_model.add_trade(symbol, price, volume, timestamp_et)
        
        # Update console view
        self.console_view.print_trade_updates(self.symbols, self.trade_model)
        
        # Update visualization if active
        if self.visualizer and self.visualizer.running:
            # Get latest order book
            order_book = self.order_book_model.get_latest_order_book(symbol)
            bids = order_book["bids"] if order_book else []
            asks = order_book["asks"] if order_book else []
            
            self.visualizer.update_visualization(
                symbol, 
                timestamp_utc, 
                bids, 
                asks, 
                {"price": price, "volume": volume}
            )
        
        # Save to CSV if max trades reached
        if max_reached:
            filename = self.trade_model.save_trades_to_csv(symbol)
            if filename:
                self.console_view.print_info(f"Trade history exported for {symbol} to {filename}")
    
    def process_order_book(self, symbol, data):
        """Process an order book message."""
        if "E" in data:
            timestamp_utc = datetime.utcfromtimestamp(data["E"] / 1000).replace(tzinfo=self.utc)
            timestamp_et = timestamp_utc.astimezone(self.eastern).strftime("%Y-%m-%d %H:%M:%S")
        else:
            timestamp_utc = datetime.now(self.utc)
            timestamp_et = datetime.now(self.eastern).strftime("%Y-%m-%d %H:%M:%S")
        
        bids, asks = data["bids"], data["asks"]
        last_price = self.trade_model.get_last_price(symbol)
        
        # Update order book model
        self.order_book_model.update_order_book(symbol, timestamp_et, bids, asks)
        
        # Save to database
        trade_flag = "Y" if self.trade_model.get_trade_status(symbol) else "N"
        self.db_manager.add_order_book(symbol, timestamp_et, bids, asks, last_price, trade_flag)
        
        # Update visualization if active
        if self.visualizer and self.visualizer.running:
            self.visualizer.update_visualization(
                symbol, 
                timestamp_utc, 
                bids, 
                asks, 
                {"price": last_price, "volume": 1.0} if last_price else None
            )
        
        # Reset trade flag
        self.trade_model.reset_trade_status(symbol)
    
    def on_error(self, ws, error):
        """Handle WebSocket error."""
        self.console_view.print_error(f"WebSocket Error: {error}")
    
    def on_close(self, ws, close_status_code, close_msg):
        """Handle WebSocket close."""
        self.console_view.print_warning(f"WebSocket closed with status code: {close_status_code}, message: {close_msg}")
        
        # Attempt to reconnect if not an intentional close
        if not self.exit_flag.is_set():
            self.console_view.print_info("Attempting to reconnect...")
            self.connect()
    
    def close(self):
        """Close the WebSocket connection."""
        self.exit_flag.set()
        if self.ws:
            self.ws.close()
