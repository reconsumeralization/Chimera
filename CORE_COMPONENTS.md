# Core Components Implementation

This document provides an overview of the core components implemented as part of Phase 2 of Project Chimera.

## Context Cache Implementation

The Context Cache is a critical component that stores and retrieves IDE context data, enabling intelligent assistance based on the user's current development context.

### Key Features

- **Efficient Context Storage**: Stores snapshots of the user's IDE context, including files, diagnostics, and editor state.
- **Flexible Querying**: Provides methods for querying the cache to retrieve context relevant to specific tasks or queries.
- **Persistence**: Supports both in-memory and persistent storage of context data.
- **Database Integration**: Uses SQLite for efficient storage and retrieval of context metadata.
- **Automatic Cleanup**: Implements TTL-based and size-based cleanup strategies to manage memory usage.
- **Thread Safety**: Uses asyncio locks to ensure thread safety in concurrent environments.

### Technical Implementation

- `ContextCacheService`: Main service class for storing and retrieving context data.
- `ContextCacheOptions`: Configuration options for the cache service.
- Database schema with tables for snapshots, files, and diagnostics.
- JSON serialization for snapshot content storage.

## Rule Engine Implementation

The Rule Engine evaluates rules against context snapshots to provide intelligent recommendations and actions based on the user's code and environment.

### Key Features

- **Rule Management**: Supports adding, updating, and deleting rule sets.
- **Condition Types**: Supports various condition types, including file patterns, language detection, content matching, file size, and diagnostic severity.
- **Action Types**: Supports different action types, including notifications, suggestions, code actions, and documentation links.
- **Efficient Evaluation**: Evaluates rules against context snapshots with optimized performance.
- **JSON Configuration**: Uses JSON files for rule set storage and loading.

### Technical Implementation

- `RuleEngineService`: Main service class for managing and evaluating rules.
- Rule sets, rules, conditions, and actions defined as Pydantic models.
- Flexible condition evaluation with support for pattern matching, regex, and other condition types.
- Action execution framework for different types of actions.

## Database Service Implementation

The Database Service provides a unified interface for database operations, supporting both SQLite and PostgreSQL backends.

### Key Features

- **Backend Flexibility**: Supports both SQLite and PostgreSQL databases.
- **Async Operations**: Uses SQLAlchemy's async API for non-blocking database operations.
- **Session Management**: Provides context managers for database sessions.
- **Error Handling**: Implements robust error handling for database operations.
- **Connection Pooling**: Uses connection pooling for efficient resource usage.

### Technical Implementation

- `DatabaseService`: Main service class for database operations.
- `Base`: SQLAlchemy declarative base class for ORM models.
- Async context managers for session handling.
- Support for raw SQL queries and ORM operations.

## AI Client Implementation

The AI Client connects Project Chimera to advanced AI capabilities, specifically using Google's Gemini models for code understanding, generation, and analysis.

### Key Features

- **Core Model Integration**: Uses gemini-2.5-pro-exp-03-25 as the designated core model.
- **Rate Limiting**: Implements built-in rate limiting to manage API usage (5 RPM).
- **Specialized Use Cases**: Provides tailored methods for code generation, explanation, analysis, and test generation.
- **Context Integration**: Seamlessly incorporates IDE context into AI prompts.
- **Streaming Support**: Supports both streaming and non-streaming responses.
- **Model Overrides**: Allows overriding the default model for specific requests.

### Technical Implementation

- `AIClient`: Main service class for interacting with AI models.
- Uses Google's official `google-generativeai` Python SDK.
- Implements specialized prompt templates for different coding tasks.
- Asynchronous design with proper error handling and logging.
- Thread-safe rate limiting implementation.

## Service Factory Implementation

The Service Factory creates and manages core services, ensuring proper initialization and shutdown.

### Key Features

- **Centralized Initialization**: Provides a centralized way to initialize all core services.
- **Dependency Management**: Manages dependencies between services.
- **Configuration Integration**: Uses the application's configuration system to configure services.
- **Resource Cleanup**: Ensures proper cleanup of resources on shutdown.

### Technical Implementation

- `ServiceFactory`: Main factory class for creating and managing services.
- Global singleton instance accessible via helper functions.
- Async initialization and cleanup methods for all services.

## Schema Definitions

The schemas package defines the structure of data exchanged between different components of the system.

### Key Features

- **Type Safety**: Uses Pydantic models for type-safe data validation.
- **Data Validation**: Implements validators for data integrity.
- **Documentation**: Includes comprehensive docstrings and examples.
- **Serialization Support**: Supports JSON serialization and deserialization.

### Technical Implementation

- Context schemas: `ContextSnapshot`, `FileData`, `DiagnosticItem`, etc.
- Rule schemas: `Rule`, `RuleCondition`, `RuleAction`, etc.
- API schemas: `APIRequest`, `APIResponse`, etc.

## Configuration System

The configuration system manages application settings, loading them from environment variables and configuration files.

### Key Features

- **Environment Integration**: Loads settings from environment variables.
- **Config File Support**: Supports loading settings from `.env` files.
- **Validation**: Validates settings against expected types and constraints.
- **Defaults**: Provides sensible default values for all settings.

### Technical Implementation

- `ChimeraSettings`: Pydantic settings class with all application settings.
- Cached singleton instance accessible via `get_settings()`.
- Validators for specific settings like `log_level`, `db_type`, and `ai_temperature`.
- Comprehensive configuration for all services, including AI-specific settings.

## Next Steps

The following areas are suggested for future development:

1. **Context Analysis**: Enhance context analysis with semantic understanding of code.
2. **Rule Actions**: Implement more sophisticated action types, such as code generation and refactoring.
3. **Machine Learning Integration**: Integrate machine learning models for more intelligent suggestions.
4. **User Feedback Loop**: Implement a feedback system to improve suggestions over time.
5. **Performance Optimization**: Optimize cache and rule evaluation for larger codebases.
6. **AI Caching**: Implement efficient caching of AI responses to reduce API calls and improve responsiveness.
7. **DTGS Integration**: Connect the AI client to the DTGS (Dynamic Tool Generation System) for code execution. 