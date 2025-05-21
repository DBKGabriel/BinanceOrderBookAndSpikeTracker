import tkinter as tk
from tkinter import ttk, scrolledtext
import threading

class GuiView:
    def __init__(self):
        """Initialize the GUI view."""
        self.windows = {}
    
    def show_trade_details(self, symbol, trades):
        """
        Shows details about a symbol's activity.
        
        Args:
            symbol: Cryptocurrency symbol
            trades: List of trades to display
        """
        window = tk.Toplevel()
        window.title(f"Trade History for {symbol}")
        window.geometry("800x600")
        text_area = scrolledtext.ScrolledText(window, wrap=tk.WORD, width=100, height=30)
        text_area.pack(expand=True, fill='both')
        
        display_str = f"=== Trade History for {symbol} ===\n\n"
        if trades:
            for trade in trades:
                display_str += f"{trade['time']} - Price: ${trade['price']:.2f}, Volume: {trade['volume']}\n"
        else:
            display_str += "No trades recorded yet.\n"
        
        text_area.insert(tk.END, display_str)
        text_area.config(state='disabled')
        
        close_button = tk.Button(window, text="Close", command=window.destroy)
        close_button.pack(pady=5)
        
        # Store window reference to prevent garbage collection
        self.windows[f"trade_{symbol}"] = window
    
    def show_symbol_list(self, symbols, callback):
        """
        Show a list of symbols that the user can select.
        
        Args:
            symbols: List of cryptocurrency symbols
            callback: Function to call when a symbol is selected
        """
        window = tk.Tk()
        window.title("Available Cryptos - Trade History")
        window.geometry("300x300")
        window.lift()
        window.attributes('-topmost', True)
        window.after(0, lambda: window.attributes('-topmost', False))
        
        label = tk.Label(window, text="Select a crypto to view its trade history:")
        label.pack(pady=10)
        
        for symbol in symbols:
            btn = tk.Button(
                window, 
                text=symbol, 
                command=lambda s=symbol: callback(s)
            )
            btn.pack(pady=5)
        
        close_button = tk.Button(window, text="Close", command=window.destroy)
        close_button.pack(pady=10)
        
        # Store window reference
        self.windows["symbol_list"] = window
        
        return window
