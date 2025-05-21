# ADR 001: Refactoring to MVC Architecture

## Context: The Hobby Project Turned Monolithic Monster

Well I have a statistical modeling idea for markets based on my background in the neurobiology of economic decision-making. But I realized that to test my theory I needed better quality market data. So I dived in headfirst and wrote this Binance Order Book & Spike Tracker script that connects to the Binance.US WebSocket API, tracks and records trades and order book data for cryptocurrencies. Then, in stereotypical form, I hyperfixated on silly details like UI, color schemes, etc. Long story short, it works! Yay! But also, oof. It's a rough read; just a 300+ line monolithic script with everything jumbled together.

Currently, the script:
- Has a lot of hard coded local variables and parameters
- Has global variables scattered everywhere
- Mixes WebSocket handling with data processing
- Combines UI code with business logic
- Has database operations intertwined with data processing
- Uses direct function calls between unrelated components
- Lacks any clear separation between different parts of the application


This worked fine when I was just hacking it together to get something working, but now I want to actually use this thing for more than proof of data-gather concept, as well as maybe adding features like:
- 3D visualization
- User-defined settings at startup
- Database query improvements
- Batch processing for better performance

And scrolling up and down the file, trying to figure out which part affects what whenever I try to update or add something new is just annoying.

## Problem: Growing Pains

The main issues with the current approach:
It's hard to maintain, since it's functionally a rube goldberg machine of a script. It's unit test-proof, since it's as fragile as and has as much interdependence as a food-web. It's just a nightmare to conceptualize. And I have to copy-paste ad nauseum anytime I want to use this elsewhere.

## The solution?
MVC!

I'm going to refactor this mama's whole architecture into Model-View-Controller (MVC) format.

1. **Models**: Will encapsulate all the data structures and business logic:
   - `TradeModel`: Trade history and processing
   - `OrderBookModel`: Order book data management
   - `DatabaseModel`: Database operations and persistence

2. **Views**: Will handle all user interfaces:
   - `ConsoleView`: Command-line output
   - `GuiView`: Tkinter windows for trade history
   - `VisualizationView`: New 3D visualization of market data

3. **Controllers**: Will coordinate between models and views:
   - `WebSocketController`: Handle WebSocket events and update models
   - `CommandController`: Process user commands and control the application flow

This approach will make the code:
- Easier to understand (each component has a specific role)
- More maintainable (changes to one component won't break others)
- More testable (I can test the models without the UI)
- More extensible (adding a new view won't require touching the data processing)

## Alternatives Considered

I explored a few other options before settling on MVC:

1. **Simple Modularization**: Just breaking the code into separate files without a formal architecture. This would help with file size but wouldn't address the deeper issues of component coupling.

2. **Event-Based Architecture**: Using a publish/subscribe model where components communicate through events. This would be cleaner for UI updates but might be overkill for the current scope.

3. **Object-Oriented Without MVC**: Creating classes for each component but without the formal MVC separation. This would be better than the current approach but wouldn't give as clear a separation of concerns.

4. **Microservices**: Separating components into entirely different processes that communicate over a local protocol. Definitely overkill for a script of this size!

MVC strikes the right balance - it's a well-established pattern that provides clear separation of concerns without introducing unnecessary complexity for a project of this size. 

## Implementation Plan
This whole process will also give me the chance to clean up the code and add some missing QOL features (e.g., database indexing) as I go along. Here's hoping I actually take that opportunity!

 Here's how I'm going to tackle this refactoring. 

1. **Directory Structure**: Create a proper package structure with separate directories for models, views, controllers, and utilities.

2. **Models First**: I'll extract the data structures and business logic into model classes
   - trade history management --> `TradeModel`
   - order book data --> `OrderBookModel`
   - improved data storage with indexing and batch processing --> `DatabaseManager`

3. **Views Second**: Separate the UI components:
   - terminal output --> `ConsoleView`
   - Tkinter code --> `GuiView`
   - Implement 3D visualization --> `VisualizationView`

4. **Controllers Last**: Create controllers to tie everything together:
   - Implement Binance API interaction --> `WebSocketController`
   - User commands --> `CommandController`

5. **Configuration**: Add a config module for user-defined settings at startup

6. **Unit Tests**: Add tests for critical components, especially models

7. **Documentation**: I guess I should update the README and add inline documentation

This incremental approach will let me refactor one component at a time while keeping the application functional throughout the process. I'll be able to commit logical chunks of work rather than one massive change.

## Consequences

### Positive

- Cleaner, more maintainable code
- Easier to add new features
- Better separation of concerns
- Possibility to test components in isolation
- More professional structure that better showcases my coding style
- Learning experience in applying software architecture principles

### Negative

- Initial time investment for refactoring
- More files to manage
- Slightly more complex structure to understand for very simple changes
- I'm probably over-engineering this. But hey, I've never been one for half-measures ¯\_(ツ)_/¯ 

The trade-offs are worth it though, especially as I plan to continue developing this project and potentially use it as a portfolio piece.

## Notes

This refactoring is as much about learning good software design principles as it is about improving the actual code. It's a personal project, so I have the freedom to experiment with architecture patterns that I might want to use in professional settings later.

I'll document the process along the way, which will help both my future self and anyone looking at this project as part of my portfolio.

Also, this thing's current name is too long (BinanceOrderBookAndSpikeTracker? Blehg.) I'm shortening it to crypto_monitor