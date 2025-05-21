# Binance Order Book & Spike Tracker

This script monitors real-time cryptocurrency market activity  on Binance.US, including trade executions, 5-deep bids and asks on the order book, and spikes in price. This is the first step of a long-term project, with the eventual goal of developing a model to predict / identify opportunities for quick, profitable trades.

# Overview

This script connects to Binance.US WebSocket API to monitor multiple cryptocurrency trading pairs simultaneously. It provides live trade updates, tracks order book changes, detects price spikes, and stores historical data for analysis.

## Features
- Multi-Currency Tracking
- **Real-time price, color-coded updates**: red for drops, green for rises
- **Price spike detection**: Automatically flags significant price movements (≥0.5%)
- **Data storage in SQLite database**: Either creates or appends to the existing db for persistent storage
- **CSV export functionality**: exports a csv with executed trades after a certain threshold of trades occur
- **Interactive UI**: Tkinter GUI for viewing historical trade data; command-line interface for accessing features
    - Type `show` at the prompt to open the trade history dashboard

## Technical Details

The application leverages several technologies:
- WebSocket connections for real-time data streaming
- Multi-threading for simultaneous data processing and user interaction
- SQLite for efficient data storage and retrieval
- Time zone conversion between UTC and Eastern Time, since I'm in the midwest

## Dependencies
- websocket-client
- pytz
- colorama
- sqlite3

## Project Status
This is version 1.0 of the tracker. Planned  future updates include:
1) User defined inputs at script execution to customize:
    - price spike threshold
    - currency pairs to track
    - database name
2) Advanced charting and visualization
3) Integration with trading systems
4) Email/SMS alerts for significant market movements
5) Support for exchanges beyond binance and trading pairs

## Contributing

Contributions, suggestions, and feedback are welcome. Feel free to fork this repository and submit pull requests with improvements.