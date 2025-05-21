import sqlite3
import threading
import os
import json
import time
from datetime import datetime

class DatabaseManager:
    def __init__(self, db_name="order_book_data.db", batch_size=100, batch_timeout=5):
        """
        Initialize the database manager with batching and persistence.
        
        Args:
            db_name: Name of the database file
            batch_size: Number of records to batch before committing
            batch_timeout: Maximum time (seconds) to hold records before committing
        """
        self.db_name = db_name
        self.batch_size = batch_size
        self.batch_timeout = batch_timeout
        self.conn = None
        self.lock = threading.Lock()
        self.batch_records = []
        self.last_commit_time = time.time()
        self.shutdown_flag = threading.Event()
        self.batch_thread = None
        self.pending_file = f"{db_name}.pending"
        
        # Load any pending records from previous run
        self._load_pending_records()
        
        # Initialize the database
        self._init_db()
        
        # Start batch processing thread
        self._start_batch_thread()
    
    def _init_db(self):
        """Initialize the SQLite database with proper indexes."""
        self.conn = sqlite3.connect(self.db_name, check_same_thread=False)
        c = self.conn.cursor()
        
        # Create table if it doesn't exist
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
        
        # Add indexes for commonly queried columns
        c.execute("CREATE INDEX IF NOT EXISTS idx_timestamp ON order_book_records(timestamp)")
        c.execute("CREATE INDEX IF NOT EXISTS idx_symbol ON order_book_records(symbol)")
        c.execute("CREATE INDEX IF NOT EXISTS idx_timestamp_symbol ON order_book_records(timestamp, symbol)")
        c.execute("CREATE INDEX IF NOT EXISTS idx_order_level ON order_book_records(order_level)")
        c.execute("CREATE INDEX IF NOT EXISTS idx_trade_flag ON order_book_records(TradeNY_N)")
        
        self.conn.commit()
    
    def _load_pending_records(self):
        """Load any pending records from previous run."""
        if os.path.exists(self.pending_file):
            try:
                with open(self.pending_file, 'r') as f:
                    self.batch_records = json.load(f)
                print(f"Loaded {len(self.batch_records)} pending records from previous run")
            except Exception as e:
                print(f"Error loading pending records: {e}")
                self.batch_records = []
            
            # Delete the pending file after loading
            try:
                os.remove(self.pending_file)
            except:
                pass
    
    def _save_pending_records(self):
        """Save pending records to a file in case of crash."""
        if self.batch_records:
            try:
                with open(self.pending_file, 'w') as f:
                    json.dump(self.batch_records, f)
            except Exception as e:
                print(f"Error saving pending records: {e}")
    
    def _start_batch_thread(self):
        """Start the background thread for batch processing."""
        self.batch_thread = threading.Thread(target=self._batch_processor, daemon=True)
        self.batch_thread.start()
    
    def _batch_processor(self):
        """Background thread to process batches of records."""
        while not self.shutdown_flag.is_set():
            current_time = time.time()
            time_since_commit = current_time - self.last_commit_time
            
            with self.lock:
                # Check if we should commit based on batch size or timeout
                if (len(self.batch_records) >= self.batch_size or 
                    (len(self.batch_records) > 0 and time_since_commit >= self.batch_timeout)):
                    self._commit_batch()
            
            # Save pending records periodically
            self._save_pending_records()
            
            # Sleep to avoid consuming too much CPU
            time.sleep(0.1)
    
    def _commit_batch(self):
        """Commit the current batch of records to the database."""
        if not self.batch_records:
            return
        
        try:
            c = self.conn.cursor()
            c.executemany("""
                INSERT INTO order_book_records 
                (timestamp, symbol, order_level, price, amount, total, TradeNY_N)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, self.batch_records)
            self.conn.commit()
            print(f"Committed {len(self.batch_records)} records to database")
            self.batch_records = []
            self.last_commit_time = time.time()
        except sqlite3.Error as e:
            print(f"Database error: {e}")
            self.conn.rollback()
    
    def add_record(self, timestamp, symbol, order_level, price, amount, total, trade_flag):
        """Add a single record to the batch."""
        with self.lock:
            self.batch_records.append((timestamp, symbol, order_level, price, amount, total, trade_flag))
    
    def add_order_book(self, symbol, timestamp, bids, asks, last_price, trade_flag):
        """Add order book data to the batch."""
        with self.lock:
            # Add asks
            for i, ask in enumerate(asks[:5]):
                price, amount = float(ask[0]), float(ask[1])
                total = price * amount
                self.batch_records.append(
                    (timestamp, symbol, f"Ask{i+1}", price, amount, total, trade_flag)
                )
            
            # Add last price
            if last_price is not None:
                self.batch_records.append(
                    (timestamp, symbol, "Last", last_price, 1.0, last_price * 1.0, trade_flag)
                )
            
            # Add bids
            for i, bid in enumerate(bids[:5]):
                price, amount = float(bid[0]), float(bid[1])
                total = price * amount
                self.batch_records.append(
                    (timestamp, symbol, f"Bid{i+1}", price, amount, total, trade_flag)
                )
    
    def flush(self):
        """Force commit all pending records."""
        with self.lock:
            self._commit_batch()
    
    def close(self):
        """Clean up resources and ensure all records are saved."""
        self.shutdown_flag.set()
        if self.batch_thread and self.batch_thread.is_alive():
            self.batch_thread.join(timeout=5)
        
        # Commit any remaining records
        with self.lock:
            self._commit_batch()
        
        # Save any records that couldn't be committed
        self._save_pending_records()
        
        # Close database connection
        if self.conn:
            self.conn.close()
