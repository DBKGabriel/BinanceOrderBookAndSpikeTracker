crypto_monitor/
├── .gitignore
├── MVC-Structure-Diagram.md
├── README.md
├── requirements.txt
├── Project_Structure_Diagram.md
├── architecture/
    └── adr-001-mvc-refactoring.md
├── crypto_monitor/
    ├── main.py                             # Application entry point
    ├── config.py                           # Configuration and argument parsing
    ├── models/                             # Data layer
    │   ├── database.py                     # Database operations with batching
    │   ├── trade_model.py                  # Trade data management
    │   └── order_book_model.py             # Order book data management
    ├── views/                              # Presentation layer
    │   ├── console_view.py                 # Terminal interface
    │   ├── gui_view.py                     # Tkinter windows
    │   └── visualization.py                # 3D market visualization
    ├── controllers/                        # Logic layer
    │   ├── websocket_controller.py         # WebSocket communication
    │   └── command_controller.py           # User command processing
    └── utils/                              # Shared utilities
        └── time_utils.py                       # Time conversion functions