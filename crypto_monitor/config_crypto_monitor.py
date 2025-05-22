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
        default=DEFAULT_CRYPTO_SYMBOLS,
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
    return parser.parse_args()
