# Cryptocurrency Market Monitor

## Overview

This application connects to Binance.US WebSocket API to monitor multiple cryptocurrency trading pairs simultaneously. It provides live trade updates, tracks changes to the order book , detects price spikes, and stores historical data for analysis. This program is a refactored version of my original single script monolith. It's almost certainly over-engineered, but this endeavor was moreso an excercise in using a modern MVC architecture. , it has been refactored into a maintainable MVC (Model-View-Controller) architecture with advanced features.

## Project Status
This is version 2.0 of the tracker. Planned  future updates include:
1) User defined inputs at script execution to customize:
    - price spike threshold
    - currency pairs to track
    - database name
    - order book depth of bids and asks to track
2) Advanced charting and visualization
3) Integration with trading systems
4) Email/SMS alerts for significant market movements
5) Support for exchanges beyond binance and trading pairs

## Features
- **Multi-Currency Tracking**(Bitcoin, Ethereum, XRP, Litecoin, Dogecoin by default)
- **Order book monitoring** (5-deep bids and asks)
- **Real-time, color-coded price updates**: red for drops, green for rises
- **Price spike detection**: Automatically flags significant price movements (≥0.5%)
- **Data storage in SQLite database**: Either creates or appends to the existing db for persistent storage
   - SQLite db improvements: added indexing for fast queries; batch exports; crash recover
- **Automated trade record export**: exports a csv with executed trades after a certain threshold of trades occur


### User Interface
- **Live console dashboard** with formatted tables and real-time updates
- **Interactive GUI** (Tkinter) for viewing detailed trade history
- **3D visualization** (optional) showing bids (green), asks (red), and trades (blue)
- **Command-line interface** for application control
   - `show` = opens the trade history dashboard
   - `help` = shows available commands

### Architecture
- **MVC Pattern** for clean separation of concerns
- **Modular design** with separate models, views, and controllers
- **Thread-safe operations** for concurrent data processing
- **Graceful error handling** and automatic reconnection

### 3D Visualization

When enabled, the 3D visualization shows:
- **Green markers**: Bid orders
- **Red markers**: Ask orders  
- **Blue markers**: Executed trades
- **Distinct shapes**: Each cryptocurrency has a unique marker shape

### Project Structure
```
crypto_monitor/
├── main.py                 # Application entry point
├── config.py               # Configuration and argument parsing
├── models/                 # Data layer
│   ├── database.py         # Database operations with batching
│   ├── trade_model.py      # Trade data management
│   └── order_book_model.py # Order book data management
├── views/                  # Presentation layer
│   ├── console_view.py     # Terminal interface
│   ├── gui_view.py         # Tkinter windows
│   └── visualization.py    # 3D market visualization
├── controllers/            # Logic layer
│   ├── websocket_controller.py  # WebSocket communication
│   └── command_controller.py    # User command processing
└── utils/                  # Shared utilities
    └── time_utils.py       # Time conversion functions
```

### Key Tech
- **WebSocket connections** for real-time data streaming
- **Multi-threading** for concurrent data processing and user interaction
- **SQLite** with optimized indexing for efficient data storage
- **Plotly & Dash** for interactive 3D visualization
- **Tkinter** for desktop GUI components
- **Colorama** for cross-platform colored terminal output

## Installation

### Prerequisites
- Python 3.7 or higher
- pip package manager

## Dependencies
- websocket-client
- pytz
- colorama
- sqlite3
- plotly
- dash
- pandas
- numpy

## Database Schema

The application stores order book data with the following structure:

```sql
CREATE TABLE order_book_records (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp TEXT,
    symbol TEXT,
    order_level TEXT,  -- Ask1-5, Bid1-5, or Last
    price REAL,
    amount REAL,
    total REAL,
    TradeNY_N TEXT     -- 'Y' if trade occurred, 'N' otherwise
)
```

Optimized with indexes on `timestamp`, `symbol`, `order_level`, and `TradeNY_N`.

## Project Evolution

**Version 1.0**: Original monolithic script with basic monitoring functionality

**Version 2.0**: Complete MVC refactor with enhanced features:
- Modular architecture for maintainability
- Batch database operations with crash recovery
- Improved error handling and reconnection logic

## Future Enhancements

- **Advanced technical indicators** and pattern recognition
- **Machine learning integration** for trade prediction
- **Email/SMS alerts** for significant market movements
- **Support for additional exchanges** beyond Binance.US
- **Portfolio tracking** and performance analysis
- **RESTful API** for external integrations
- **Docker containerization** for easy deployment

## Contributing

Contributions, suggestions, and feedback are welcome. Feel free to fork this repository and submit pull requests with improvements.
