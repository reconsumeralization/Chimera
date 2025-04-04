"""Rule engine service for Chimera Core.

This module provides a service for evaluating rules against context data.
"""
import json
import os
import re
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Union

import structlog

from ...schemas.context import ContextSnapshot
from ...schemas.rules import (
    Rule,
    RuleAction,
    RuleActionType,
    RuleCondition,
    RuleConditionType,
    RuleEvaluationResult,
    RuleMatch,
    RuleSet,
)

# Set up logging
logger = structlog.get_logger(__name__)


class RuleEngineService:
    """Service for evaluating rules against context data."""
    
    def __init__(self, rules_dir: str, context_cache_service=None, ai_client=None):
        """
        Initialize the rule engine service.
        
        Args:
            rules_dir: Directory containing rule files
            context_cache_service: Optional context cache service for retrieving context
            ai_client: Optional AI client for executing AI-related actions
        """
        self.rules_dir = rules_dir
        self.rule_sets: List[RuleSet] = []
        self.context_cache_service = context_cache_service
        self.ai_client = ai_client
        
        # Ensure rules directory exists
        os.makedirs(rules_dir, exist_ok=True)
        
        # Load rule sets from files
        self._load_rule_sets()
        
        logger.info(
            "Rule engine service initialized",
            rule_set_count=len(self.rule_sets),
            rules_dir=rules_dir,
        )
    
    def _load_rule_sets(self) -> None:
        """Load rule sets from files in the rules directory."""
        try:
            # Get a list of JSON files in the rules directory
            rule_files = [
                f for f in os.listdir(self.rules_dir)
                if f.endswith(".json") and os.path.isfile(os.path.join(self.rules_dir, f))
            ]
            
            # Load each rule file
            for file_name in rule_files:
                try:
                    file_path = os.path.join(self.rules_dir, file_name)
                    with open(file_path, "r") as f:
                        data = json.load(f)
                        
                        # Create rule set with validation
                        rule_set = RuleSet.model_validate(data)
                        self.rule_sets.append(rule_set)
                        
                        logger.info(
                            "Loaded rule set",
                            file_name=file_name,
                            rule_set_name=f"'{rule_set.name}'",
                            rule_count=len(rule_set.rules),
                        )
                
                except Exception as e:
                    logger.error(
                        "Failed to load rule file",
                        file_name=file_name,
                        error=str(e),
                    )
            
            logger.info(
                "Loaded rule sets",
                count=len(self.rule_sets),
                rule_file_count=len(rule_files),
            )
        
        except Exception as e:
            logger.error("Failed to load rule sets", error=str(e))
    
    def get_all_rule_sets(self) -> List[RuleSet]:
        """
        Get all loaded rule sets.
        
        Returns:
            List[RuleSet]: All loaded rule sets
        """
        return self.rule_sets
    
    def get_rule_set(self, rule_set_id: str) -> Optional[RuleSet]:
        """
        Get a rule set by ID.
        
        Args:
            rule_set_id: The ID of the rule set to get
            
        Returns:
            Optional[RuleSet]: The rule set, or None if not found
        """
        for rule_set in self.rule_sets:
            if rule_set.id == rule_set_id:
                return rule_set
        return None
    
    async def evaluate_rules(
        self, context: ContextSnapshot, ai_client=None
    ) -> List[RuleEvaluationResult]:
        """
        Evaluate all rules against a context snapshot.
        
        Args:
            context: The context snapshot to evaluate against
            ai_client: Optional AI client for executing AI-related actions, defaults to self.ai_client
            
        Returns:
            List[RuleEvaluationResult]: Results of rule evaluations
        """
        # Use instance's AI client if none provided
        ai_client = ai_client or self.ai_client
        
        results: List[RuleEvaluationResult] = []
        
        # Process each rule set
        for rule_set in self.rule_sets:
            # Skip disabled rule sets
            if not rule_set.enabled:
                continue
            
            # Track matches for this rule set
            matches: List[RuleMatch] = []
            
            # Process each rule
            for rule in rule_set.rules:
                # Skip disabled rules
                if not rule.enabled:
                    continue
                
                # Track matched conditions
                matched_conditions = []
                conditions_met = True
                
                # Evaluate each condition
                for condition in rule.conditions:
                    if self._evaluate_condition(condition, context):
                        matched_conditions.append(condition)
                    else:
                        conditions_met = False
                        break
                
                # If all conditions are met, create a match
                if conditions_met and matched_conditions:
                    match = RuleMatch(
                        rule_id=rule.id,
                        rule_set_id=rule_set.id,
                        rule_name=rule.name,
                        actions=rule.actions,
                        priority=rule.priority,
                    )
                    matches.append(match)
                    
                    logger.info(
                        "Rule matched",
                        rule_id=rule.id,
                        rule_name=rule.name,
                        rule_set_id=rule_set.id,
                        condition_count=len(matched_conditions)
                    )
            
            # Create the evaluation result for this rule set
            if matches:
                result = RuleEvaluationResult(
                    rule_set_id=rule_set.id,
                    rule_set_name=rule_set.name,
                    rule=matches[0].rule_name if matches else None,
                    matched=len(matches) > 0,
                    messages=[f"Matched {len(matches)} rules"],
                    matches=matches,
                    action_executed=False,
                    timestamp=context.timestamp,
                    metadata={
                        "context_file_count": len(context.files),
                        "active_file": context.active_file,
                    },
                )
                results.append(result)
        
        logger.info(
            "Rules evaluated",
            match_count=sum(len(result.matches) for result in results),
            rule_set_count=len(self.rule_sets),
            file_count=len(context.files),
        )
        
        return results
    
    def _evaluate_condition(self, condition: RuleCondition, context: ContextSnapshot) -> bool:
        """
        Evaluate a rule condition against a context snapshot.
        
        Args:
            condition: The condition to evaluate
            context: The context snapshot to evaluate against
            
        Returns:
            bool: True if the condition is met, False otherwise
        """
        try:
            # File pattern condition
            if condition.type == RuleConditionType.FILE_PATTERN:
                pattern = condition.value
                
                if not pattern:
                    return False
                
                # Check if any file matches the pattern
                for file in context.files:
                    if re.search(pattern, file.path):
                        return True
                
                return False
            
            # Language condition
            elif condition.type == RuleConditionType.LANGUAGE:
                language = condition.value
                
                if not language:
                    return False
                
                # Check if any file has the specified language
                for file in context.files:
                    if file.language and file.language.lower() == language.lower():
                        return True
                
                return False
            
            # Content match condition
            elif condition.type == RuleConditionType.CONTENT_MATCH:
                pattern = condition.value
                
                if not pattern:
                    return False
                
                # Check if any file content matches the pattern
                for file in context.files:
                    if file.content and re.search(pattern, file.content, re.MULTILINE):
                        return True
                
                return False
            
            # File count condition
            elif condition.type == RuleConditionType.FILE_COUNT:
                count_str = condition.value
                operator = condition.operator or "=="
                
                if not count_str or not count_str.isdigit():
                    return False
                
                count = int(count_str)
                file_count = len(context.files)
                
                if operator == "==":
                    return file_count == count
                elif operator == ">":
                    return file_count > count
                elif operator == ">=":
                    return file_count >= count
                elif operator == "<":
                    return file_count < count
                elif operator == "<=":
                    return file_count <= count
                else:
                    return False
            
            # File size condition
            elif condition.type == RuleConditionType.FILE_SIZE:
                size_str = condition.value
                operator = condition.operator or ">"
                pattern = condition.param  # File pattern
                
                if not size_str or not size_str.isdigit():
                    return False
                
                size = int(size_str) * 1024  # Convert KB to bytes
                
                for file in context.files:
                    # Skip if file doesn't match pattern
                    if pattern and not re.search(pattern, file.path):
                        continue
                    
                    # Skip if file size is not available
                    if not file.size_bytes:
                        continue
                    
                    if operator == "==":
                        if file.size_bytes == size:
                            return True
                    elif operator == ">":
                        if file.size_bytes > size:
                            return True
                    elif operator == ">=":
                        if file.size_bytes >= size:
                            return True
                    elif operator == "<":
                        if file.size_bytes < size:
                            return True
                    elif operator == "<=":
                        if file.size_bytes <= size:
                            return True
                
                return False
            
            # Diagnostic severity condition
            elif condition.type == RuleConditionType.DIAGNOSTIC_SEVERITY:
                severity = condition.value
                count_str = condition.param or "1"  # Minimum count
                
                if not severity or not count_str.isdigit():
                    return False
                
                min_count = int(count_str)
                matching_diagnostics = [
                    d for d in context.diagnostics
                    if d.severity and d.severity.lower() == severity.lower()
                ]
                
                return len(matching_diagnostics) >= min_count
            
            # Other condition types
            else:
                logger.warning(
                    "Unsupported condition type",
                    type=condition.type,
                )
                return False
        
        except Exception as e:
            logger.error(
                "Error evaluating condition",
                type=condition.type,
                value=condition.value,
                error=str(e),
            )
            return False
    
    async def _execute_action(
        self, 
        action: RuleAction, 
        context: ContextSnapshot, 
        rule: Union[Rule, RuleMatch], 
        ai_client=None
    ) -> None:
        """
        Execute a rule action.
        
        Args:
            action: The action to execute
            context: The context snapshot
            rule: The rule or match containing the action
            ai_client: Optional AI client for executing AI-related actions
        """
        # Skip if action is disabled
        if not action.enabled:
            return
        
        # Use the instance AI client if none provided
        ai_client = ai_client or self.ai_client
        
        try:
            action_type = action.action_type
            params = action.parameters or {}
            
            # Log action execution
            rule_id = getattr(rule, 'id', getattr(rule, 'rule_id', 'unknown'))
            rule_name = getattr(rule, 'name', getattr(rule, 'rule_name', 'unknown'))
            
            logger.info(
                "Executing action",
                action_type=action_type.value,
                rule_id=rule_id,
                rule_name=rule_name,
            )
            
            # Execute based on action type
            if action_type == RuleActionType.LOG:
                message = params.get("message", "Rule triggered")
                level = params.get("level", "info").lower()
                
                log_method = getattr(logger, level, logger.info)
                log_method(
                    message,
                    rule_id=rule_id,
                    rule_name=rule_name,
                    action_type=action_type.value,
                )
            
            elif action_type == RuleActionType.AI_ANALYSIS:
                if ai_client:
                    prompt = params.get("prompt", "Analyze the following code:")
                    file_path = params.get("file_path")
                    
                    if file_path and context.files:
                        # Find the file in context
                        file_content = None
                        for file in context.files:
                            if file.path == file_path and file.content:
                                file_content = file.content
                                break
                        
                        if file_content:
                            context_data = {
                                "files": [
                                    {
                                        "path": file_path,
                                        "content": file_content,
                                    }
                                ]
                            }
                            
                            # Call AI for analysis
                            analysis = await ai_client.analyze_code_issues(
                                code=file_content,
                                language=params.get("language", ""),
                                context=context_data,
                            )
                            
                            logger.info(
                                "AI analysis complete",
                                rule_id=rule_id,
                                rule_name=rule_name,
                                file_path=file_path,
                                analysis_length=len(analysis) if analysis else 0,
                            )
                        else:
                            logger.warning(
                                "File not found in context or has no content",
                                rule_id=rule_id,
                                rule_name=rule_name,
                                file_path=file_path,
                            )
                    else:
                        logger.warning(
                            "No file path specified or context has no files",
                            rule_id=rule_id,
                            rule_name=rule_name,
                        )
                else:
                    logger.warning(
                        "AI client not available for analysis",
                        rule_id=rule_id,
                        rule_name=rule_name,
                    )
            
            # Add more action types as needed
            
            logger.info(
                "Action executed successfully",
                action_type=action_type.value,
                rule_id=rule_id,
                rule_name=rule_name,
            )
        
        except Exception as e:
            logger.error(
                "Failed to execute action",
                action_type=action.action_type.value if hasattr(action, 'action_type') else "unknown",
                error=str(e),
            )
    
    async def execute_action(
        self, 
        rule: Rule,
        snapshot: ContextSnapshot,
        ai_client=None
    ) -> bool:
        """
        Execute actions for a rule.
        
        Args:
            rule: The rule containing actions to execute
            snapshot: The context snapshot
            ai_client: Optional AI client, defaults to self.ai_client
            
        Returns:
            bool: True if all actions executed successfully, False otherwise
        """
        # Use instance's AI client if none provided
        ai_client = ai_client or self.ai_client
        
        success = True
        for action in rule.actions:
            try:
                await self._execute_action(action, snapshot, rule, ai_client)
            except Exception as e:
                logger.error(
                    "Failed to execute action",
                    rule_id=rule.id,
                    rule_name=rule.name,
                    action_type=action.action_type.value,
                    error=str(e)
                )
                success = False
        
        return success 