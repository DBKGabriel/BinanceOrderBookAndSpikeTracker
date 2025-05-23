import threading
import time

class CommandController:
    def __init__(self, trade_model, gui_view, console_view, visualizer=None, main_app=None):
        """
        Initialize the command controller.
        
        Args:
            trade_model: Model for trade data
            gui_view: GUI view for displaying trade history
            console_view: Console view for output
            visualizer: Optional visualization view
        """
        self.trade_model = trade_model
        self.gui_view = gui_view
        self.console_view = console_view
        self.visualizer = visualizer
        self.running = False
        self.command_thread = None
        self.main_app = main_app

    def start_listener(self):
        """Start the command listener thread."""
        self.running = True
        self.command_thread = threading.Thread(target=self._command_loop, daemon=True)
        self.command_thread.start()
        self.console_view.print_info("Command listener started. " \
        "Type 'help' for available commands." \
        "Type 'exit' to exit application.", persistent=True)
    
    def _command_loop(self):
        """Command listener loop."""
        help_text = """
Available Commands:
------------------
show                  - Show trade history dashboard
viz on               - Turn on 3D visualization
viz off              - Turn off 3D visualization
save [symbol]        - Save trade history for a symbol to CSV
flush                - Flush pending database records
help                 - Show this help message
exit                 - Exit the application
        """
        
        while self.running:
            try:
                command = input("\nEnter command: ").strip().lower()
                
                if command == "show":
                    self._handle_show_command()
                elif command == "viz on":
                    self._handle_viz_command(True)
                elif command == "viz off":
                    self._handle_viz_command(False)
                elif command.startswith("save"):
                    self._handle_save_command(command)
                elif command == "flush":
                    self._handle_flush_command()
                elif command == "help":
                    self.console_view.print_message(help_text)
                elif command == "exit":
                    self.running = False
                    self.console_view.print_info("Exiting application...")
                    if self.main_app:
                        self.main_app.signal_exit()  # <-- Add this line
                    break
                else:
                    self.console_view.print_warning(f"Unknown command: {command}")
                    self.console_view.print_message("Type 'help' for available commands.")
            
            except EOFError:
                # Handle Ctrl+D
                self.running = False
                break
            except KeyboardInterrupt:
                # Handle Ctrl+C
                self.running = False
                break
            except Exception as e:
                self.console_view.print_error(f"Command error: {e}")
        
        # Signal that the command loop has ended
        self.console_view.print_info("Command listener stopped.")
    
    def _handle_show_command(self):
        """Handle the 'show' command."""
        self.console_view.print_info("Opening trade history dashboard...")
        
        # Define callback for symbol selection
        def symbol_selected(symbol):
            trades = self.trade_model.get_trades(symbol)
            self.gui_view.show_trade_details(symbol, trades)
        
        # Show symbol list window
        threading.Thread(
            target=lambda: self.gui_view.show_symbol_list(
                self.trade_model.symbols, 
                symbol_selected
            ).mainloop(),
            daemon=True
        ).start()
    
    def _handle_viz_command(self, enable):
        """
        Handle visualization commands.
        
        Args:
            enable: Boolean to enable/disable visualization
        """
        if not self.visualizer:
            self.console_view.print_warning("Visualization not available.")
            return
        
        if enable:
            if self.visualizer.running:
                self.console_view.print_info("Visualization is already running.")
            else:
                self.console_view.print_info("Starting 3D visualization...")
                success = self.visualizer.start()
                if success:
                    self.console_view.print_success("Visualization started. Open http://127.0.0.1:8050 in your browser.")
                else:
                    self.console_view.print_error("Failed to start visualization. Make sure you have required packages installed.")
        else:
            if self.visualizer.running:
                self.console_view.print_info("Stopping visualization...")
                self.visualizer.stop()
                self.console_view.print_success("Visualization stopped.")
            else:
                self.console_view.print_info("Visualization is not running.")
    
    def _handle_save_command(self, command):
        """
        Handle the 'save' command.
        
        Args:
            command: The full command string
        """
        parts = command.split()
        if len(parts) > 1:
            symbol = parts[1].upper()
            if symbol in self.trade_model.symbols:
                filename = self.trade_model.save_trades_to_csv(symbol)
                if filename:
                    self.console_view.print_success(f"Trade history for {symbol} saved to {filename}")
                else:
                    self.console_view.print_warning(f"No trade history to save for {symbol}")
            else:
                self.console_view.print_error(f"Unknown symbol: {symbol}")
                self.console_view.print_message(f"Available symbols: {', '.join(self.trade_model.symbols)}")
        else:
            self.console_view.print_warning("Please specify a symbol to save.")
            self.console_view.print_message(f"Example: save BTCUSDT")
    
    def _handle_flush_command(self):
        """Handle the 'flush' command."""
        
        # Use context manager to access a protected method
        database_manager = self.get_database_manager()
        if database_manager:
            self.console_view.print_info("Flushing pending database records...")
            database_manager.flush()
            self.console_view.print_success("Database records flushed.")
        else:
            self.console_view.print_error("Database manager not accessible.")
    
    def stop(self):
        """Stop the command listener."""
        self.running = False
        if self.command_thread and self.command_thread.is_alive():
            self.command_thread.join(timeout=1)
    
    def get_database_manager(self):
        """Get the database manager from the application context."""
        # This is a placeholder method that should be overridden by the application
        return None
