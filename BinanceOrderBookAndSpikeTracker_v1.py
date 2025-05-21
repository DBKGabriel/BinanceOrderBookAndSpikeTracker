import websocket
import json
import sys
import time
import pytz
import csv
import threading
import tkinter as tk
from tkinter import ttk, scrolledtext
from datetime import datetime
from colorama import Fore, Style, init
from collections import deque
import sqlite3

# Initialize colorama for Windows compatibility
init()

# Define crypto tickers in Binance.US format (lowercase)
crypto_symbols = ["btcusdt", "ethusdt", "xrpusdt", "ltcusdt", "dogeusdt"]

# Define timezones
utc = pytz.utc
eastern = pytz.timezone("US/Eastern")

# Store recent trade history (max 500 trades per symbol)
MAX_TRADES = 500
trade_history = {symbol.upper(): deque(maxlen=MAX_TRADES) for symbol in crypto_symbols}

# Store full order book update history for each symbol (used for database insertion)
order_book_history = {symbol.upper(): [] for symbol in crypto_symbols}

# Track the most recent trade price per symbol
last_trade_price = {symbol.upper(): None for symbol in crypto_symbols}

# Track which bin the last trade occurred in per symbol
trade_occurred_in_bin = {symbol.upper(): False for symbol in crypto_symbols}

# Global SQL database connection
db_conn = None

# Column widths for formatting live update display in the console
col_widths = {
    "TIME": 20,
    "SYMBOL": 10,
    "PRICE": 15,
    "CHANGE (%)": 15,
    "VOLUME": 15,
    "SPIKE": 10
}

def init_db(db_name="order_book_data.db"):
    """
    Initialize (or open) the SQLite database and create the order_book_records table.
    """

    conn = sqlite3.connect(db_name)
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS order_book_records (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT,
            symbol TEXT,
            order_level TEXT,
            price REAL,
            amount REAL,
            total REAL,
            TradeNY_N TEXT
        )
    """)
    conn.commit()
    return conn


def print_live_updates():
    """Prints trade data to the terminal in a formatted table."""
    sys.stdout.write("\033c")
    print(f"{Fore.CYAN}✅ Live Binance.US Trade Updates (v2-2){Style.RESET_ALL}\n")
    
    header_row = (
        f"{'TIME (ET)'.center(col_widths['TIME'])}"
        f"{'SYMBOL'.center(col_widths['SYMBOL'])}"
        f"{'PRICE'.center(col_widths['PRICE'])}"
        f"{'CHANGE (%)'.center(col_widths['CHANGE (%)'])}"
        f"{'VOLUME'.center(col_widths['VOLUME'])}"
        f"{'SPIKE'.center(col_widths['SPIKE'])}"
    )
    print(header_row)
    print("-" * sum(col_widths.values()))
    
    for symbol in trade_history.keys():
        trades = trade_history[symbol]
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
                f"{latest_trade['time'].center(col_widths['TIME'])}"
                f"{symbol.center(col_widths['SYMBOL'])}"
                f"{color + price_str.center(col_widths['PRICE']) + Style.RESET_ALL}"
                f"{color + change_str.center(col_widths['CHANGE (%)']) + Style.RESET_ALL}"
                f"{volume_str.center(col_widths['VOLUME'])}"
                f"{spike_alert.center(col_widths['SPIKE'])}"
            )
        else:
            print("{:^20}{:^10}{:^15}{:^15}{:^15}{:^10}".format(" ", symbol, " ", " ", " ", " "))
    
    sys.stdout.flush()

def save_trades_to_csv(symbol):
    """
    Appends the trade history for a symbol to a CSV file once the maximum number of trades is reached.
    """
    filename = f"trade_history_{symbol}.csv"
    trades_to_save = list(trade_history[symbol])
    if not trades_to_save:
        return
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
    trade_history[symbol].clear()
    print(f"{Fore.YELLOW}[SAVED] Trade history exported for {symbol}{Style.RESET_ALL}")

def save_order_book_to_db(symbol, timestamp_et, bids, asks, last_price):
    global db_conn
    if not db_conn:
        return

    c = db_conn.cursor()
    
    # Determine TradeNY/N for this insertion based on current bin's trade status
    trade_flag = "Y" if trade_occurred_in_bin[symbol] else "N"

    # Insert asks
    for i, ask in enumerate(asks[:5]):
        price, amount = float(ask[0]), float(ask[1])
        total = price * amount
        c.execute("""
            INSERT INTO order_book_records (timestamp, symbol, order_level, price, amount, total, TradeNY_N)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (timestamp_et, symbol, f"Ask{i+1}", price, amount, total, trade_occurred_in_bin[symbol]))

    # Insert Last price row
    if last_price is not None:
        last_amount = 1.0
        last_total = last_price * last_amount
        c.execute("""
            INSERT INTO order_book_records (timestamp, symbol, order_level, price, amount, total, TradeNY_N)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (timestamp_et, symbol, "Last", last_price, last_amount, last_total, trade_occurred_in_bin[symbol]))

    # Insert top 5 bids
    for i, bid in enumerate(bids[:5]):
        price, amount = float(bid[0]), float(bid[1])
        total = price * amount
        c.execute("""
            INSERT INTO order_book_records (timestamp, symbol, order_level, price, amount, total, TradeNY_N)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (timestamp_et, symbol, f"Bid{i+1}", price, amount, total, trade_occurred_in_bin[symbol]))

    db_conn.commit()

    # Reset trade occurrence flag
    trade_occurred_in_bin[symbol] = False


#
# NEW: Interactive "show" command now displays recorded trades.
#
def show_trade_details(symbol):
    """
    Opens a Tkinter window that displays the recorded trades for the specified symbol.
    """
    window = tk.Toplevel()
    window.title(f"Trade History for {symbol}")
    window.geometry("800x600")
    text_area = scrolledtext.ScrolledText(window, wrap=tk.WORD, width=100, height=30)
    text_area.pack(expand=True, fill='both')
    
    display_str = f"=== Trade History for {symbol} ===\n\n"
    trades = trade_history[symbol]
    if trades:
        for trade in trades:
            display_str += f"{trade['time']} - Price: ${trade['price']:.2f}, Volume: {trade['volume']}\n"
    else:
        display_str += "No trades recorded yet.\n"
    
    text_area.insert(tk.END, display_str)
    text_area.config(state='disabled')
    
    close_button = tk.Button(window, text="Close", command=window.destroy)
    close_button.pack(pady=5)
    window.mainloop()

def open_trade_symbol_list_window():
    """
    Opens a Tkinter window that lists all monitored symbols.
    Clicking on a symbol opens its recorded trade history.
    """
    window = tk.Tk()
    window.title("Available Cryptos - Trade History")
    window.geometry("300x200")
    window.lift()
    window.attributes('-topmost', True)
    window.after(0, lambda: window.attributes('-topmost', False))
    
    label = tk.Label(window, text="Select a crypto to view its trade history:")
    label.pack(pady=10)
    
    for symbol in trade_history.keys():
        btn = tk.Button(window, text=symbol, command=lambda s=symbol: show_trade_details(s))
        btn.pack(pady=5)
    
    close_button = tk.Button(window, text="Close", command=window.destroy)
    close_button.pack(pady=5)
    window.mainloop()

#
# The command_listener now opens the trade history dashboard.
#
def command_listener():
    while True:
        command = input("\nEnter command (type 'show' to view trade history): ").strip().lower()
        if command == "show":
            print("Show command detected, opening trade history dashboard...")
            threading.Thread(target=open_trade_symbol_list_window, daemon=True).start()

def on_message(ws, message):
    global trade_occurred_in_bin
    data = json.loads(message)

    if data.get("stream"):
        stream_name = data["stream"]
        symbol = stream_name.split("@")[0].upper()
        data = data.get("data", {})
    else:
        symbol = data.get("s", "").upper()

    if symbol not in trade_history:
        return

    if data.get("e") == "trade":
        timestamp_utc = datetime.utcfromtimestamp(data["T"] / 1000).replace(tzinfo=utc)
        timestamp_et = timestamp_utc.astimezone(eastern).strftime("%Y-%m-%d %H:%M:%S")
        price = float(data["p"])
        volume = float(data["q"])
        trade_history[symbol].append({"price": price, "volume": volume, "time": timestamp_et})
        last_trade_price[symbol] = price
        
        # Set flag true as trade occurred in current timebin
        trade_occurred_in_bin[symbol] = True

        print_live_updates()
        if len(trade_history[symbol]) >= MAX_TRADES:
            save_trades_to_csv(symbol)

    elif data.get("e") == "depthUpdate" or ("bids" in data and "asks" in data):
        if "E" in data:
            timestamp_utc = datetime.utcfromtimestamp(data["E"] / 1000).replace(tzinfo=utc)
            timestamp_et = timestamp_utc.astimezone(eastern).strftime("%Y-%m-%d %H:%M:%S")
        else:
            timestamp_et = datetime.now(eastern).strftime("%Y-%m-%d %H:%M:%S")

        bids, asks = data["bids"], data["asks"]
        last_price = last_trade_price[symbol]

        save_order_book_to_db(symbol, timestamp_et, bids, asks, last_price)

        # Reset flag after saving the snapshot
        trade_occurred_in_bin[symbol] = False

def on_error(ws, error):
    print(f"{Fore.RED}[ERROR] WebSocket Error: {error}{Style.RESET_ALL}")

def on_close(ws, close_status_code, close_msg):
    print(f"{Fore.RED}[CLOSED] WebSocket closed.{Style.RESET_ALL}")

def on_open(ws):
    print(f"{Fore.GREEN}[CONNECTED] Connected to Binance.US combined stream.{Style.RESET_ALL}")

if __name__ == "__main__":
    db_conn = init_db("order_book_data.db")
    threading.Thread(target=command_listener, daemon=True).start()
    streams = "/".join(
        [f"{symbol}@trade" for symbol in crypto_symbols] +
        [f"{symbol}@depth5" for symbol in crypto_symbols]
    )
    binance_us_ws = f"wss://stream.binance.us:9443/stream?streams={streams}"
    ws = websocket.WebSocketApp(binance_us_ws,
                                on_open=on_open,
                                on_message=on_message,
                                on_error=on_error,
                                on_close=on_close)
    ws.run_forever()
