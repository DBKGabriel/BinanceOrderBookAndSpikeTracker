import sys
from colorama import Fore, Style, init

# Initialize colorama
init()

class ConsoleView:
    def __init__(self, col_widths=None):
        """
        Initialize the console view.
        
        Args:
            col_widths: Dictionary of column widths for formatting
        """
        self.col_widths = col_widths or {
            "TIME": 20,
            "SYMBOL": 10,
            "PRICE": 15,
            "CHANGE (%)": 15,
            "VOLUME": 15,
            "SPIKE": 10
        }
    
    def print_header(self, version="1.0"):
        """Print the header for the console output."""
        sys.stdout.write("\033c")  # Clears the console
        print(f"{Fore.CYAN} Live Trade Updates from Binance.US (v{version}){Style.RESET_ALL}\n")
        
        header_row = (
            f"{'TIME (ET)'.center(self.col_widths['TIME'])}"
            f"{'SYMBOL'.center(self.col_widths['SYMBOL'])}"
            f"{'PRICE'.center(self.col_widths['PRICE'])}"
            f"{'CHANGE (%)'.center(self.col_widths['CHANGE (%)'])}"
            f"{'VOLUME'.center(self.col_widths['VOLUME'])}"
            f"{'SPIKE'.center(self.col_widths['SPIKE'])}"
        )
        print(header_row)
        print("-" * sum(self.col_widths.values()))
    
    def print_trade_updates(self, symbols, trade_model):
        """
        Print trade updates for all symbols.
        
        Args:
            symbols: List of cryptocurrency symbols
            trade_model: The trade model containing trade data
        """
        self.print_header()
        
        for symbol in symbols:
            trades = trade_model.get_trades(symbol)
            if trades:
                latest_trade = trades[-1]
                prev_price = trades[-2]["price"] if len(trades) > 1 else latest_trade["price"]
                change = ((latest_trade["price"] - prev_price) / prev_price * 100) if prev_price != 0 else 0.0
                color = Fore.GREEN if change > 0 else (Fore.RED if change < 0 else Style.RESET_ALL)
                spike_alert = f"{Fore.YELLOW}[SPIKE]{Style.RESET_ALL}" if abs(change) >= 0.5 else ""
                price_str = f"${latest_trade['price']:.2f}"
                change_str = f"{change:.2f}%"
                volume_str = f"{latest_trade['volume']:.6f}"
                
                print(
                    f"{latest_trade['time'].center(self.col_widths['TIME'])}"
                    f"{symbol.center(self.col_widths['SYMBOL'])}"
                    f"{color + price_str.center(self.col_widths['PRICE']) + Style.RESET_ALL}"
                    f"{color + change_str.center(self.col_widths['CHANGE (%)']) + Style.RESET_ALL}"
                    f"{volume_str.center(self.col_widths['VOLUME'])}"
                    f"{spike_alert.center(self.col_widths['SPIKE'])}"
                )
            else:
                print("{:^20}{:^10}{:^15}{:^15}{:^15}{:^10}".format(
                    " ", symbol, " ", " ", " ", " "
                ))
        
        sys.stdout.flush()
    
    def print_message(self, message, color=None):
        """Print a message to the console."""
        if color:
            print(f"{color}{message}{Style.RESET_ALL}")
        else:
            print(message)
        sys.stdout.flush()
    
    def print_error(self, message):
        """Print an error message to the console."""
        self.print_message(f"[ERROR] {message}", Fore.RED)
    
    def print_success(self, message):
        """Print a success message to the console."""
        self.print_message(f"[SUCCESS] {message}", Fore.GREEN)
    
    def print_info(self, message):
        """Print an info message to the console."""
        self.print_message(f"[INFO] {message}", Fore.CYAN)
    
    def print_warning(self, message):
        """Print a warning message to the console."""
        self.print_message(f"[WARNING] {message}", Fore.YELLOW)
