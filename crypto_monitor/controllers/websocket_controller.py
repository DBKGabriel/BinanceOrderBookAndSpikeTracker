import websocket
import json
import threading
import time
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
        
        # Connection management
        self.reconnect_attempts = 0
        self.max_reconnect_attempts = 10
        self.base_retry_delay = 5  # seconds
        self.max_retry_delay = 300  # 5 minutes max
        self.last_connection_attempt = 0
        self.connection_successful = False
        self.reconnect_thread = None
    
    def connect(self):
        """Connect to the Binance.US WebSocket API."""
        if self.exit_flag.is_set():
            return
            
        current_time = time.time()
        
        # Prevent too frequent connection attempts
        if current_time - self.last_connection_attempt < 1:
            return
            
        self.last_connection_attempt = current_time
        
        # Build streams string
        lower_symbols = [symbol.lower() for symbol in self.symbols]
        streams = "/".join(
            [f"{symbol}@trade" for symbol in lower_symbols] +
            [f"{symbol}@depth5" for symbol in lower_symbols]
        )
        ws_url = f"wss://stream.binance.us:9443/stream?streams={streams}"
        
        try:
            # Create WebSocket
            self.ws = websocket.WebSocketApp(
                ws_url,
                on_open=self.on_open,
                on_message=self.on_message,
                on_error=self.on_error,
                on_close=self.on_close
            )
            
            # Start WebSocket in a separate thread
            self.console_view.print_info(f"Connecting to Binance.US WebSocket (attempt {self.reconnect_attempts + 1})...")
            threading.Thread(target=self.ws.run_forever, daemon=True).start()
            
        except Exception as e:
            self.console_view.print_error(f"Failed to create WebSocket connection: {e}")
            self._schedule_reconnect()
    
    def on_open(self, ws):
        """Handle WebSocket open event."""
        self.console_view.print_success("Connected to Binance.US combined stream.")
        self.reconnect_attempts = 0
        self.connection_successful = True
    
    def on_message(self, ws, message):
        """Handle incoming WebSocket messages."""
        try:
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
                
        except json.JSONDecodeError as e:
            self.console_view.print_error(f"Failed to parse WebSocket message: {e}")
        except Exception as e:
            self.console_view.print_error(f"Error processing WebSocket message: {e}")
    
    def process_trade(self, symbol, data):
        """Process a trade message."""
        try:
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
                    
        except (KeyError, ValueError, TypeError) as e:
            self.console_view.print_error(f"Error processing trade data for {symbol}: {e}")
    
    def process_order_book(self, symbol, data):
        """Process an order book message."""
        try:
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
            
        except (KeyError, ValueError, TypeError) as e:
            self.console_view.print_error(f"Error processing order book data for {symbol}: {e}")
    
    def on_error(self, ws, error):
        """Handle WebSocket error."""
        error_msg = str(error)
        
        # Check for specific network errors
        if "11001" in error_msg or "getaddrinfo failed" in error_msg:
            self.console_view.print_error("DNS resolution failed. Check your internet connection.")
        elif "10061" in error_msg or "Connection refused" in error_msg:
            self.console_view.print_error("Connection refused by server.")
        elif "timeout" in error_msg.lower():
            self.console_view.print_error("Connection timeout.")
        else:
            self.console_view.print_error(f"WebSocket Error: {error}")
        
        # Don't attempt immediate reconnection on repeated failures
        if not self.connection_successful:
            self.reconnect_attempts += 1
    
    def on_close(self, ws, close_status_code, close_msg):
        """Handle WebSocket close."""
        if self.exit_flag.is_set():
            self.console_view.print_info("WebSocket connection closed.")
            return
        
        # Log the close event
        if close_status_code:
            self.console_view.print_warning(f"WebSocket closed with status code: {close_status_code}")
        if close_msg:
            self.console_view.print_warning(f"Close message: {close_msg}")
        
        # Only attempt reconnection if we haven't exceeded max attempts
        if self.reconnect_attempts < self.max_reconnect_attempts:
            self._schedule_reconnect()
        else:
            self.console_view.print_error(f"Max reconnection attempts ({self.max_reconnect_attempts}) reached. Stopping reconnection attempts.")
            self.console_view.print_info("You can try restarting the application or check your network connection.")
    
    def _schedule_reconnect(self):
        """Schedule a reconnection attempt with exponential backoff."""
        if self.exit_flag.is_set():
            return
            
        # Calculate delay with exponential backoff
        delay = min(
            self.base_retry_delay * (2 ** self.reconnect_attempts),
            self.max_retry_delay
        )
        
        self.console_view.print_info(f"Scheduling reconnection in {delay} seconds...")
        
        # Cancel any existing reconnect thread
        if self.reconnect_thread and self.reconnect_thread.is_alive():
            return
        
        def delayed_reconnect():
            if not self.exit_flag.wait(delay):  # Wait for delay or exit signal
                self.reconnect_attempts += 1
                self.connect()
        
        self.reconnect_thread = threading.Thread(target=delayed_reconnect, daemon=True)
        self.reconnect_thread.start()
    
    def reset_connection_state(self):
        """Reset connection state (useful for manual reconnection)."""
        self.reconnect_attempts = 0
        self.connection_successful = False
        self.console_view.print_info("Connection state reset.")
    
    def close(self):
        """Close the WebSocket connection."""
        self.console_view.print_info("Shutting down WebSocket connection...")
        self.exit_flag.set()
        
        # Cancel any pending reconnection
        if self.reconnect_thread and self.reconnect_thread.is_alive():
            self.reconnect_thread.join(timeout=1)
        
        # Close WebSocket
        if self.ws:
            self.ws.close()
            
        self.console_view.print_info("WebSocket connection closed.")