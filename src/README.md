# Project Chimera Source Code

This directory contains the source code for Project Chimera, organized into distinct packages with clear separation of concerns.

## Package Structure

### `chimera_core/`
Core IDE integration functionality, including:
- Context caching
- Rule engine
- API endpoints for the IDE/extension
- Core database operations

This package contains the "Chimera Head" - the main functionality that interacts directly with the IDE.

### `chimera_data/`
Data collection and processing functionality, including:
- Collectors for various data types
- Data processors for anonymization and structuring
- Database operations specific to collected data
- Data export services

This package is entirely separable from the core functionality and can be disabled via configuration.

### `chimera_stdio_mcp/`
MCP implementations that communicate via stdio, including:
- Tools implementation
- Server implementation for MCP
- stdio communication layer

These are the Multi-Channel Protocols that interface with external tools.

### `chimera_ui/`
Web UI for the developer dashboard, including:
- FastAPI routes for rendering templates
- API endpoints for UI interactions
- Static assets and templates

### `schemas/`
Shared data models and schemas used across packages, including:
- Context snapshot schema
- API request/response models
- Rule definitions
- Shared database models

## Separation of Concerns

This structure is designed to maintain strict separation between:

1. Core IDE functionality (`chimera_core`) - Essential for the IDE integration
2. Data collection (`chimera_data`) - Optional functionality for logging and training 
3. MCP tools (`chimera_stdio_mcp`) - External tool integrations
4. User interface (`chimera_ui`) - Dashboard and visualization

Each package has its own configuration and can be developed, tested, and deployed independently.

## Development Guidelines

1. Keep dependencies between packages minimal and explicit
2. Use the shared schemas package for cross-package data structures
3. Each package should have its own tests in the corresponding tests directory
4. Configuration should be centralized but allow package-specific settings
5. Maintain backward compatibility within each package's public APIs 