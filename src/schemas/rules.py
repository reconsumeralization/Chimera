"""
Rule schema definitions for Project Chimera.

This module contains Pydantic models that define the schemas for rules,
rule conditions, and rule actions used by the rule engine.
"""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Union

from pydantic import BaseModel, Field, field_validator


class RuleConditionType(str, Enum):
    """Types of rule conditions."""
    
    FILE_PATTERN = "FILE_PATTERN"
    LANGUAGE = "LANGUAGE"
    CONTENT_MATCH = "CONTENT_MATCH"
    FILE_COUNT = "FILE_COUNT"
    FILE_SIZE = "FILE_SIZE"
    DIAGNOSTIC_SEVERITY = "DIAGNOSTIC_SEVERITY"
    CUSTOM = "CUSTOM"


class RuleActionType(str, Enum):
    """Types of rule actions."""
    
    NOTIFICATION = "NOTIFICATION"
    DOCUMENT_LINK = "DOCUMENT_LINK"
    CODE_ACTION = "CODE_ACTION"
    TRIGGER_AI_PROMPT = "TRIGGER_AI_PROMPT"
    CUSTOM = "CUSTOM"


class RulePriority(str, Enum):
    """Priority levels for rules."""
    
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class RuleCondition(BaseModel):
    """A condition that must be met for a rule to match."""
    
    type: RuleConditionType
    value: str = ""
    operator: Optional[str] = None
    param: Optional[str] = None
    description: Optional[str] = None
    
    class Config:
        json_schema_extra = {
            "example": {
                "type": "CONTENT_MATCH",
                "value": "import\\s+os",
                "description": "Check if the file imports the os module"
            }
        }


class RuleAction(BaseModel):
    """An action to take when a rule matches."""
    
    type: RuleActionType
    value: str = ""
    param: Optional[str] = None
    description: Optional[str] = None
    
    class Config:
        json_schema_extra = {
            "example": {
                "type": "NOTIFICATION",
                "value": "This file contains security-sensitive code",
                "description": "Show a notification about security"
            }
        }


class Rule(BaseModel):
    """A rule to evaluate against context data."""
    
    id: str
    name: str
    description: Optional[str] = None
    enabled: bool = True
    priority: RulePriority = RulePriority.MEDIUM
    conditions: List[RuleCondition] = Field(default_factory=list)
    actions: List[RuleAction] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)
    
    @field_validator('conditions')
    def validate_conditions(cls, v):
        """Validate that there is at least one condition."""
        if not v:
            raise ValueError("Rule must have at least one condition")
        return v
    
    @field_validator('actions')
    def validate_actions(cls, v):
        """Validate that there is at least one action."""
        if not v:
            raise ValueError("Rule must have at least one action")
        return v
    
    class Config:
        json_schema_extra = {
            "example": {
                "id": "security-001",
                "name": "Security Sensitive Import",
                "description": "Detect imports of security-sensitive modules",
                "enabled": True,
                "priority": "HIGH",
                "conditions": [
                    {
                        "type": "CONTENT_MATCH",
                        "value": "import\\s+(os|subprocess|shutil)",
                        "description": "Check for imports of system modules"
                    }
                ],
                "actions": [
                    {
                        "type": "NOTIFICATION",
                        "value": "This file imports system modules that could pose security risks",
                        "description": "Show a security notification"
                    }
                ],
                "metadata": {
                    "tags": ["security", "imports"],
                    "severity": "high"
                }
            }
        }


class RuleSet(BaseModel):
    """A set of related rules."""
    
    id: str
    name: str
    description: Optional[str] = None
    version: str = "1.0.0"
    enabled: bool = True
    rules: List[Rule] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)
    
    class Config:
        json_schema_extra = {
            "example": {
                "id": "security-rules",
                "name": "Security Rules",
                "description": "Rules to enforce security best practices",
                "version": "1.0.0",
                "enabled": True,
                "rules": [
                    {
                        "id": "security-001",
                        "name": "Security Sensitive Import",
                        "description": "Detect imports of security-sensitive modules",
                        "enabled": True,
                        "priority": "HIGH",
                        "conditions": [
                            {
                                "type": "CONTENT_MATCH",
                                "value": "import\\s+(os|subprocess|shutil)"
                            }
                        ],
                        "actions": [
                            {
                                "type": "NOTIFICATION",
                                "value": "This file imports system modules that could pose security risks"
                            }
                        ]
                    }
                ],
                "metadata": {
                    "author": "Chimera Team",
                    "category": "security"
                }
            }
        }


class RuleMatch(BaseModel):
    """A match for a rule."""
    
    rule_id: str
    rule_set_id: str
    rule_name: str
    actions: List[RuleAction]
    priority: RulePriority = RulePriority.MEDIUM
    context: Dict[str, Any] = Field(default_factory=dict)
    
    class Config:
        json_schema_extra = {
            "example": {
                "rule_id": "security-001",
                "rule_set_id": "security-rules",
                "rule_name": "Security Sensitive Import",
                "actions": [
                    {
                        "type": "NOTIFICATION",
                        "value": "This file imports system modules that could pose security risks"
                    }
                ],
                "priority": "HIGH",
                "context": {
                    "matched_files": ["app.py", "utils.py"],
                    "matched_line_count": 2
                }
            }
        }


class RuleEvaluationResult(BaseModel):
    """The result of evaluating rules against a context snapshot."""
    
    matches: List[RuleMatch] = Field(default_factory=list)
    match_count: int = 0
    timestamp: datetime = Field(default_factory=datetime.now)
    metadata: Dict[str, Any] = Field(default_factory=dict)
    
    class Config:
        json_schema_extra = {
            "example": {
                "matches": [
                    {
                        "rule_id": "security-001",
                        "rule_set_id": "security-rules",
                        "rule_name": "Security Sensitive Import",
                        "actions": [
                            {
                                "type": "NOTIFICATION",
                                "value": "This file imports system modules that could pose security risks"
                            }
                        ],
                        "priority": "HIGH",
                        "context": {
                            "matched_files": ["app.py"],
                            "matched_line_count": 1
                        }
                    }
                ],
                "match_count": 1,
                "timestamp": "2023-05-01T12:00:00",
                "metadata": {
                    "duration_ms": 25,
                    "rules_evaluated": 10
                }
            }
        } 