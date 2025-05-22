import argparse

# Default configuration settings

# List of crypto symbols to track (lowercase for Binance.US API)
DEFAULT_CRYPTO_SYMBOLS = ["btcusdt", "ethusdt", "xrpusdt", "ltcusdt", "dogeusdt"]

# Maximum trades to keep in memory per symbol
MAX_TRADES = 500

# Database settings
DEFAULT_DB_NAME = "order_book_data.db"
BATCH_SIZE = 100  # Number of records to batch before committing
BATCH_TIMEOUT = 5  # Maximum time (seconds) to hold records before committing

# Console display settings
COLUMN_WIDTHS = {
    "TIME": 20,
    "SYMBOL": 10,
    "PRICE": 15,
    "CHANGE (%)": 15,
    "VOLUME": 15,
    "SPIKE": 10
}

# Visualization settings
VISUALIZATION_ENABLED = False

def get_symbols_interactively(): 
    """
    If the user doesn't define which symbols 
    to track at the command line execution, 
    an interactive prompt asks them to input
    which to track to track or else accept the default list.
    """
    default_symbols = DEFAULT_CRYPTO_SYMBOLS
    
    prompt = f'''Input which cryptocurrency pairs to track, in quotes and separated by commas,
or press enter to record default list {[s.upper() for s in default_symbols]}: '''
    
    try:
        user_input = input(prompt).strip()
        
        if not user_input:
            print(f"Tracking {[s.upper() for s in default_symbols]}")
            return default_symbols
        
        # Parse the input - handle quotes and commas
        symbols = [s.strip().strip('"\'').lower() for s in user_input.split(',')]
        symbols = [s for s in symbols if s]  # Remove empty strings
        
        if symbols:
            print(f"Tracking {[s.upper() for s in symbols]}")
            return symbols
        else:
            print("No valid symbols entered. Using default symbols.")
            print(f"Tracking {[s.upper() for s in default_symbols]}")
            return default_symbols
            
    except (EOFError, KeyboardInterrupt):
        print("\nUsing default symbols.")
        print(f"Tracking {[s.upper() for s in default_symbols]}")
        return default_symbols
    except Exception as e:
        print(f"Error processing input: {e}")
        print("Using default symbols.")
        print(f"Tracking {[s.upper() for s in default_symbols]}")
        return default_symbols

def parse_arguments():
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(description="Cryptocurrency Market Data Monitor")
    parser.add_argument(
        "--db-name", 
        default=DEFAULT_DB_NAME,
        help="Database file name"
    )
    parser.add_argument(
        "--symbols", 
        nargs="+", 
        default=None,  # Changed to None so we can detect when not provided
        help="Crypto symbols to track (e.g., btcusdt ethusdt)"
    )
    parser.add_argument(
        "--viz", 
        action="store_true",
        default=VISUALIZATION_ENABLED,
        help="Enable 3D visualization at startup"
    )
    parser.add_argument(
        "--batch-size", 
        type=int,
        default=BATCH_SIZE,
        help="Database batch size"
    )
    args = parser.parse_args()

    # Handle symbol selection
    if args.symbols:
        # Symbols provided via command line
        symbols = [s.lower() for s in args.symbols]
        print(f"Tracking {[s.upper() for s in symbols]}")
        args.symbols = symbols
    else:
        # No symbols provided - prompt interactively
        args.symbols = get_symbols_interactively()
    
    return args
