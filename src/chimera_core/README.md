# Chimera Core

The core functionality of Project Chimera, providing context management, rule engine, and database services.

## Overview

Chimera Core is the central package of Project Chimera, providing essential services such as context management, rule processing, and database operations. It serves as the foundation for IDE integration and intelligent assistance.

## Components

### Services

- **Context Cache Service**: Stores and retrieves IDE context data, including files, diagnostics, and editor state. Provides efficient querying and retrieval of context relevant to the user's current task.
- **Rule Engine Service**: Manages and evaluates rules against context snapshots, triggering actions when conditions are met. Supports various condition types and action types.
- **Database Service**: Provides database operations for persistent storage, supporting both SQLite and PostgreSQL backends through SQLAlchemy.

### Configuration

The configuration system loads settings from environment variables and/or `.env` files, providing a centralized way to configure all aspects of Chimera Core.

### Factory

The service factory creates and initializes all core services, ensuring proper startup and shutdown sequences.

## Usage

### Basic Usage

```python
import asyncio
from src.chimera_core.factory import init_services, close_services

async def main():
    # Initialize all services
    factory = await init_services()
    
    # Get the context cache service
    context_cache = factory.get_service("context_cache")
    
    # Use the service
    stats = await context_cache.get_stats()
    print(f"Context cache stats: {stats}")
    
    # Clean up
    await close_services()

if __name__ == "__main__":
    asyncio.run(main())
```

### Advanced Usage

For more advanced usage, refer to the example scripts and the API documentation.

## API Reference

### ContextCacheService

Manages the collection and retrieval of IDE context data.

- `store_snapshot(snapshot)`: Store a new context snapshot
- `query_context(query)`: Query the context cache for relevant files
- `get_stats()`: Get statistics about the context cache
- `clear_cache()`: Clear the entire context cache

### RuleEngineService

Evaluates rules against context data to provide intelligent recommendations.

- `add_rule_set(rule_set)`: Add a new rule set to the engine
- `update_rule_set(rule_set)`: Update an existing rule set
- `delete_rule_set(rule_set_id)`: Delete a rule set
- `get_rule_set(rule_set_id)`: Get a rule set by ID
- `get_all_rule_sets()`: Get all rule sets
- `evaluate_rules(context)`: Evaluate all rules against a context snapshot

### DatabaseService

Provides database operations for persistent storage.

- `initialize()`: Initialize the database by creating tables
- `session()`: Get a database session (context manager)
- `execute(query, params)`: Execute a raw SQL query
- `check_connection()`: Check if the database connection is working
- `get_db_info()`: Get information about the database
- `close()`: Close the database connection

## Settings

Chimera Core settings can be configured through environment variables or a `.env` file. Common settings include:

- `MCP_SERVER_HOST`, `MCP_SERVER_PORT`: Host and port for the MCP server
- `UI_SERVER_HOST`, `UI_SERVER_PORT`: Host and port for the UI server
- `LOG_LEVEL`: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
- `DATA_DIRECTORY`: Directory for storing data
- `DB_TYPE`: Database type (sqlite, postgresql)
- `DEBUG`: Debug mode flag

For a complete list of settings, refer to the `ChimeraSettings` class in `config.py`.

## Development

To contribute to Chimera Core, please follow these guidelines:

1. Use explicit type annotations for all functions and methods
2. Write comprehensive docstrings for all modules, classes, and functions
3. Follow the established code style and patterns
4. Write unit tests for all new functionality
5. Update documentation when making significant changes 