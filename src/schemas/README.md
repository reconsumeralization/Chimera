# Schemas

Shared schema definitions for Project Chimera using Pydantic models.

## Overview

The schemas package contains Pydantic models that define the structure of data exchanged between different components of Project Chimera. These schemas serve as contracts for the API endpoints, ensure type safety, and provide validation for data flowing through the system.

## Schema Categories

### Context Schemas

Located in `context.py`, these schemas define the structure of IDE context data, including:

- **FileData**: Represents data for a single file, including attributes such as path, content, language, etc.
- **EditorSelection**: Captures the user's current selection in the editor.
- **DiagnosticItem**: Represents diagnostic messages from the editor (errors, warnings, etc.).
- **ContextSnapshot**: A snapshot of the user's context in the IDE, containing files, diagnostics, selections, etc.
- **ContextQuery**: A model for querying context based on specific criteria.
- **ContextResponse**: Represents the response to a context query.

### API Schemas

Located in `api.py`, these schemas define the structure of API requests and responses, including:

- **APIStatus**: An enumeration for response status codes.
- **APIErrorCode**: An enumeration for various error codes.
- **APIRequest**: A base class for all API requests.
- **APIResponse**: A base class for all API responses.
- Various request and response models for specific API endpoints.

### Rule Schemas

Located in `rules.py`, these schemas define the structure of rules and rule sets used by the rule engine:

- **RuleConditionType**: Types of conditions that can be applied in rules.
- **RuleActionType**: Types of actions that can be triggered by rules.
- **RulePriority**: Priority levels for rules.
- **RuleCondition**: A condition that must be met for a rule to trigger.
- **RuleAction**: An action to take when a rule is triggered.
- **Rule**: A rule that can be triggered based on context conditions.
- **RuleSet**: A set of rules grouped together.
- **RuleMatch**: A match of a rule against a context.
- **RuleEvaluationResult**: The result of evaluating rules against a context.

## Usage

To use these schemas in your code:

```python
from src.schemas.context import ContextSnapshot, FileData
from src.schemas.rules import Rule, RuleCondition, RuleAction
from src.schemas.api import APIResponse

# Create a file data object
file_data = FileData(
    path="src/main.py",
    content="print('Hello, world!')",
    language="python",
    last_modified=datetime.utcnow(),
    size_bytes=200,
    is_open=True,
    is_dirty=False
)

# Create a context snapshot
snapshot = ContextSnapshot(
    timestamp=datetime.utcnow(),
    workspace_root="/path/to/workspace",
    active_file="src/main.py",
    files={"src/main.py": file_data},
    diagnostics=[],
    selections=[],
    metadata={"source": "vscode"}
)

# Validate the snapshot
print(snapshot.model_dump_json(indent=2))
```

## Extending Schemas

To add a new schema or extend an existing one:

1. Identify the appropriate file or create a new one if the schema doesn't fit existing categories.
2. Define your schema using Pydantic models with appropriate type hints.
3. Add validation logic as needed using Pydantic validators.
4. Add example JSON representations in the schema's `Config.json_schema_extra` if appropriate.
5. Update this README if you create a new category.

## Best Practices

When working with schemas:

- Always use explicit types rather than `Any` when possible.
- Add proper docstrings to document each field.
- Use validators to enforce additional constraints beyond type checking.
- Consider the serialization/deserialization needs when designing models.
- Keep backward compatibility in mind when modifying existing schemas.
- Use appropriate default values and make fields optional when sensible. 