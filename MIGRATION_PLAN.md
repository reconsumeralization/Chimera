# Project Chimera Migration Plan

This document outlines the plan for migrating the existing monolithic codebase to the new modular structure with strict separation of concerns.

## Migration Phases

### Phase 1: Setup Basic Structure ✅

- [x] Create the new directory structure
- [x] Create package `__init__.py` files
- [x] Add README.md files for each directory
- [x] Create pyproject.toml for package management
- [x] Update main README.md

### Phase 2: Refactor Code (In Progress)

- [x] Move scripts to the scripts directory
  - [x] Move Windows scripts (.bat) to scripts/windows/
  - [x] Move Unix scripts (.sh) to scripts/unix/
  - [x] Move Python utility scripts to scripts/common/
  - [x] Update scripts to reference new file locations

- [x] Refactor MCP server implementation
  - [x] Extract base MCP functionality to src/chimera_stdio_mcp/base.py
  - [x] Move tool implementations to src/chimera_stdio_mcp/tools/
  - [x] Create server entry point in src/chimera_stdio_mcp/server.py

- [x] Refactor data collection functionality
  - [x] Move data collector to src/chimera_data/collectors/
  - [ ] Move anonymization logic to src/chimera_data/processors/
  - [ ] Create database models in src/chimera_data/db_data/

- [ ] Refactor core functionality
  - [x] Create network utilities in src/chimera_core/utils/
  - [x] Create logging configuration in src/chimera_core/utils/
  - [ ] Create context cache implementation in src/chimera_core/services/
  - [ ] Implement API endpoints in src/chimera_core/api/
  - [ ] Move database operations to src/chimera_core/db_core/

- [x] Refactor UI implementation
  - [x] Move FastAPI routes to src/chimera_ui/routes/
  - [x] Implement API endpoints for UI in src/chimera_ui/api/
  - [x] Create main UI server in src/chimera_ui/server.py
  - [ ] Move templates to templates/ directory
  - [ ] Move static files to static/ directory

- [ ] Create shared schemas
  - [ ] Context snapshot schema in src/schemas/context.py
  - [ ] API request/response models in src/schemas/api.py
  - [ ] Rule definitions in src/schemas/rules.py

### Phase 3: Update Imports and References

- [ ] Update import statements in all files
- [ ] Create proper package exports in __init__.py files
- [ ] Update relative import paths to absolute package paths
- [ ] Ensure script references point to correct locations

### Phase 4: Documentation and Testing

- [ ] Create initial tests for each package
- [ ] Document API interfaces between packages
- [ ] Update package READMEs with detailed information
- [ ] Create end-to-end tests for critical workflows
- [ ] Create example documentation for extension

## Implementation Guidelines

### General Rules

1. Maintain strict separation between packages
2. Keep dependencies between packages minimal and explicit
3. Use the schemas package for cross-package data structures
4. Each package should have its own configuration
5. Maintain backward compatibility where possible
6. Ensure tests cover critical functionality

### Package-Specific Guidelines

#### chimera_core

- Core IDE integration functionality
- Should have minimal dependencies on other packages
- Configuration should control whether data collection is enabled
- Clear interfaces for extension

#### chimera_data

- Data collection and processing functionality
- Must be able to be completely disabled
- All data handling should be privacy-conscious
- Clear documentation of what data is collected

#### chimera_stdio_mcp

- MCP implementations communicated via stdio
- Tool implementations should be modular
- Should not depend on chimera_core or chimera_ui

#### chimera_ui

- Web UI for developer dashboard
- Should provide clear UI for all functionality
- API endpoints for UI interactions
- Should be testable in isolation

## Testing Strategy

1. Unit tests for each component
2. Integration tests for interactions within a package
3. End-to-end tests for complete workflows
4. Mock external dependencies
5. Test data collection with special focus on privacy

## Communication Plan

1. Regular updates on migration progress
2. Code reviews for each package
3. Documentation of API changes
4. Training sessions for new architecture

## Timeline

- Phase 1: Setup Basic Structure - COMPLETED
- Phase 2: Refactor Code - IN PROGRESS (ETA: 2 weeks)
- Phase 3: Update Imports and References - (ETA: 1 week)
- Phase 4: Documentation and Testing - (ETA: 1 week)

Total estimated time: 1 month 