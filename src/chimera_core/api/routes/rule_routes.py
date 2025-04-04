"""API routes for rule management.

This module provides the API routes for rule management, including
listing rules and evaluating rules against context.
"""

from typing import Dict, List, Optional, Any

from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from pydantic import ValidationError

from src.chimera_core.api.dependencies import ContextService, RuleService, APIKey
from src.chimera_core.services.rule_engine import RuleEvaluationResult
from src.schemas.rules import Rule, RuleSet

# Create the router
router = APIRouter(prefix="/rules", tags=["rules"])


@router.get("/sets", response_model=List[str], dependencies=[Depends(APIKey)])
async def list_rule_sets(
    rule_engine: RuleService
) -> List[str]:
    """List all available rule sets."""
    try:
        rule_sets = await rule_engine.list_rule_sets()
        
        return rule_sets
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list rule sets: {str(e)}"
        )


@router.get("/sets/{rule_set_id}", response_model=RuleSet, dependencies=[Depends(APIKey)])
async def get_rule_set(
    rule_set_id: str,
    rule_engine: RuleService
) -> RuleSet:
    """Get a rule set by ID."""
    try:
        rule_set = await rule_engine.get_rule_set(rule_set_id)
        
        if not rule_set:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Rule set with ID {rule_set_id} not found"
            )
        
        return rule_set
    
    except Exception as e:
        if isinstance(e, HTTPException):
            raise
        
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get rule set: {str(e)}"
        )


@router.get("/", response_model=List[Rule], dependencies=[Depends(APIKey)])
async def list_rules(
    rule_engine: RuleService,
    rule_set_id: Optional[str] = None
) -> List[Rule]:
    """List all rules, optionally filtered by rule set ID."""
    try:
        rules = await rule_engine.list_rules(rule_set_id)
        
        return rules
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list rules: {str(e)}"
        )


@router.post("/evaluate/{snapshot_id}", response_model=List[RuleEvaluationResult], dependencies=[Depends(APIKey)])
async def evaluate_rules_against_snapshot(
    snapshot_id: str,
    background_tasks: BackgroundTasks,
    rule_engine: RuleService,
    context_cache: ContextService
) -> List[RuleEvaluationResult]:
    """Evaluate rules against a specific context snapshot."""
    try:
        # Get the snapshot
        snapshot = await context_cache.get_snapshot(snapshot_id)
        
        if not snapshot:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Snapshot with ID {snapshot_id} not found"
            )
        
        # Evaluate rules
        results = await rule_engine.evaluate_rules(snapshot)
        
        # Execute actions in the background
        for result in results:
            if result.matched and not result.action_executed:
                background_tasks.add_task(
                    rule_engine.execute_action,
                    rule=result.rule,
                    snapshot=snapshot
                )
                result.action_executed = True
                result.messages.append("Action scheduled for execution")
        
        return results
    
    except Exception as e:
        if isinstance(e, HTTPException):
            raise
        
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to evaluate rules: {str(e)}"
        )


@router.post("/validate", response_model=Dict[str, Any], dependencies=[Depends(APIKey)])
async def validate_rule(
    rule: Rule,
    rule_engine: RuleService
) -> Dict[str, Any]:
    """Validate a rule without saving it."""
    try:
        validation_result = await rule_engine.validate_rule(rule)
        
        return validation_result
    
    except ValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Invalid rule: {str(e)}"
        )
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to validate rule: {str(e)}"
        ) 