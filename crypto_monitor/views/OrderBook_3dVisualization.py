import threading
import time
from datetime import datetime
import numpy as np

class VisualizationView:
    def __init__(self, symbols):
        """
        Initialize the visualization view.
        
        Args:
            symbols: List of cryptocurrency symbols to track
        """
        self.symbols = symbols
        self.running = False
        self.app = None
        self.fig = None
        self.update_thread = None
        self.last_update = {sym: datetime.now() for sym in symbols}
        self.symbol_markers = {
            'BTCUSDT': 'circle',
            'ETHUSDT': 'square',
            'XRPUSDT': 'diamond',
            'LTCUSDT': 'cross',
            'DOGEUSDT': 'pentagon',
        }
        
        # We'll define a placeholder for symbols that aren't in our predefined list
        for symbol in symbols:
            if symbol not in self.symbol_markers:
                self.symbol_markers[symbol] = 'circle'
    
    def start(self):
        """Start the visualization."""
        if self.running:
            return
        
        try:
            import plotly.graph_objects as go
            from plotly.subplots import make_subplots
            import dash
            from dash import dcc, html
            from dash.dependencies import Input, Output
            import pandas as pd
            
            # Setup the plot
            self.fig = make_subplots(
                rows=1, cols=1,
                specs=[[{'type': 'scatter3d'}]]
            )
            
            # Initial empty plot for each symbol, bid/ask type
            for symbol in self.symbols:
                marker = self.symbol_markers.get(symbol, 'circle')
                
                # Add traces for bids (green)
                self.fig.add_trace(
                    go.Scatter3d(
                        x=[], y=[], z=[],
                        mode='markers',
                        marker=dict(
                            size=5,
                            color='green',
                            symbol=marker
                        ),
                        name=f'{symbol} Bids'
                    )
                )
                
                # Add traces for asks (red)
                self.fig.add_trace(
                    go.Scatter3d(
                        x=[], y=[], z=[],
                        mode='markers',
                        marker=dict(
                            size=5,
                            color='red',
                            symbol=marker
                        ),
                        name=f'{symbol} Asks'
                    )
                )
                
                # Add traces for last trades (blue)
                self.fig.add_trace(
                    go.Scatter3d(
                        x=[], y=[], z=[],
                        mode='markers',
                        marker=dict(
                            size=8,
                            color='blue',
                            symbol=marker
                        ),
                        name=f'{symbol} Trades'
                    )
                )
            
            # Update layout
            self.fig.update_layout(
                title="Real-time Cryptocurrency Order Book & Trades",
                scene=dict(
                    xaxis_title="Time",
                    yaxis_title="Price",
                    zaxis_title="Volume",
                    aspectmode='auto'
                ),
                legend=dict(
                    yanchor="top",
                    y=0.99,
                    xanchor="left",
                    x=0.01
                ),
                autosize=True,
                height=900
            )
            
            # Create Dash app
            self.app = dash.Dash(__name__)
            self.app.layout = html.Div([
                html.H1("Cryptocurrency Market Visualization"),
                dcc.Graph(id='live-graph', figure=self.fig),
                dcc.Interval(
                    id='interval-component',
                    interval=1*1000,  # in milliseconds (1 second)
                    n_intervals=0
                )
            ])
            
            @self.app.callback(
                Output('live-graph', 'figure'),
                [Input('interval-component', 'n_intervals')]
            )
            def update_graph(n):
                return self.fig
            
            self.running = True
            self.update_thread = threading.Thread(target=self._update_loop, daemon=True)
            self.update_thread.start()
            
            # Run the server in a separate thread
            threading.Thread(
                target=lambda: self.app.run_server(debug=False, use_reloader=False),
                daemon=True
            ).start()
            
            return True
        except Exception as e:
            print(f"Error starting visualization: {e}")
            return False
    
    def update_visualization(self, symbol, timestamp, bids, asks, last_trade):
        """
        Update the visualization with new data.
        
        Args:
            symbol: Cryptocurrency symbol
            timestamp: Update timestamp
            bids: List of bids [price, amount]
            asks: List of asks [price, amount]
            last_trade: Last trade data (price, volume)
        """
        if not self.running or not self.fig:
            return
        
        try:
            import pandas as pd
            
            # Convert timestamp to numeric for x-axis
            if isinstance(timestamp, str):
                time_num = pd.to_datetime(timestamp).timestamp()
            else:
                time_num = timestamp.timestamp()
            
            # Find trace indices for this symbol
            symbol_idx = self.symbols.index(symbol)
            bid_idx = symbol_idx * 3
            ask_idx = symbol_idx * 3 + 1
            trade_idx = symbol_idx * 3 + 2
            
            # Add time decay - points fade out over time
            # Keep only data from the last 5 minutes
            cutoff_time = time_num - 300  # 5 minutes in seconds
            
            # Update bids (green)
            x_bids = list(self.fig.data[bid_idx].x)
            y_bids = list(self.fig.data[bid_idx].y)
            z_bids = list(self.fig.data[bid_idx].z)
            
            # Remove old points
            valid_indices = [i for i, x in enumerate(x_bids) if x >= cutoff_time]
            x_bids = [x_bids[i] for i in valid_indices] if valid_indices else []
            y_bids = [y_bids[i] for i in valid_indices] if valid_indices else []
            z_bids = [z_bids[i] for i in valid_indices] if valid_indices else []
            
            # Add new bids
            for bid in bids[:5]:  # Top 5 bids
                price, amount = float(bid[0]), float(bid[1])
                x_bids.append(time_num)
                y_bids.append(price)
                z_bids.append(amount)
            
            # Update asks (red) - similar logic
            x_asks = list(self.fig.data[ask_idx].x)
            y_asks = list(self.fig.data[ask_idx].y)
            z_asks = list(self.fig.data[ask_idx].z)
            
            valid_indices = [i for i, x in enumerate(x_asks) if x >= cutoff_time]
            x_asks = [x_asks[i] for i in valid_indices] if valid_indices else []
            y_asks = [y_asks[i] for i in valid_indices] if valid_indices else []
            z_asks = [z_asks[i] for i in valid_indices] if valid_indices else []
            
            for ask in asks[:5]:  # Top 5 asks
                price, amount = float(ask[0]), float(ask[1])
                x_asks.append(time_num)
                y_asks.append(price)
                z_asks.append(amount)
            
            # Update last trade (blue)
            if last_trade is not None:
                # Keep only the 20 most recent trades
                x_trades = list(self.fig.data[trade_idx].x)[-19:] if self.fig.data[trade_idx].x else []
                y_trades = list(self.fig.data[trade_idx].y)[-19:] if self.fig.data[trade_idx].y else []
                z_trades = list(self.fig.data[trade_idx].z)[-19:] if self.fig.data[trade_idx].z else []
                
                price = last_trade["price"] if isinstance(last_trade, dict) else last_trade
                volume = last_trade["volume"] if isinstance(last_trade, dict) else 1.0
                
                x_trades.append(time_num)
                y_trades.append(price)
                z_trades.append(volume)
                
                self.fig.data[trade_idx].x = x_trades
                self.fig.data[trade_idx].y = y_trades
                self.fig.data[trade_idx].z = z_trades
            
            # Update bid and ask data
            self.fig.data[bid_idx].x = x_bids
            self.fig.data[bid_idx].y = y_bids
            self.fig.data[bid_idx].z = z_bids
            
            self.fig.data[ask_idx].x = x_asks
            self.fig.data[ask_idx].y = y_asks
            self.fig.data[ask_idx].z = z_asks
            
            # Update the timestamp
            self.last_update[symbol] = datetime.now()
        except Exception as e:
            print(f"Error updating visualization: {e}")
    
    def _update_loop(self):
        """Background thread for regular plot updates."""
        while self.running:
            # Automatic updates can happen here if needed
            time.sleep(0.1)
    
    def stop(self):
        """Stop the visualization."""
        self.running = False
        if self.update_thread and self.update_thread.is_alive():
            self.update_thread.join(timeout=1)
