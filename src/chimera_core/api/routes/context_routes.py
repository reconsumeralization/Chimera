"""API routes for context management.

This module provides the API routes for context management, including
storing and retrieving context snapshots.
"""

from datetime import datetime
from typing import Dict, List, Optional, Any

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import ValidationError

from src.chimera_core.api.dependencies import ContextService, RuleService, APIKey
from src.schemas.context import ContextQuery, ContextResponse, ContextSnapshot

# Create the router
router = APIRouter(prefix="/context", tags=["context"])


@router.post("/snapshot", status_code=status.HTTP_201_CREATED, dependencies=[Depends(APIKey)])
async def store_context_snapshot(
    snapshot: ContextSnapshot,
    context_cache: ContextService,
    rule_engine: RuleService
) -> Dict[str, Any]:
    """Store a context snapshot and evaluate rules against it.
    
    This endpoint receives a snapshot of the user's IDE context, stores it
    in the context cache, and evaluates rules against it. If any rules match,
    the corresponding actions are triggered.
    """
    try:
        # Store the snapshot
        snapshot_id = await context_cache.store_snapshot(snapshot)
        
        # Evaluate rules against the snapshot
        rule_results = await rule_engine.evaluate_rules(snapshot)
        
        return {
            "snapshot_id": snapshot_id,
            "timestamp": datetime.now().isoformat(),
            "rule_matches": len(rule_results),
            "actions_triggered": sum(1 for result in rule_results if result.action_executed)
        }
    
    except ValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Invalid snapshot data: {str(e)}"
        )
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to store context snapshot: {str(e)}"
        )


@router.get("/snapshot/{snapshot_id}", dependencies=[Depends(APIKey)])
async def get_context_snapshot(
    snapshot_id: str,
    context_cache: ContextService
) -> ContextSnapshot:
    """Retrieve a context snapshot by its ID."""
    try:
        snapshot = await context_cache.get_snapshot(snapshot_id)
        
        if not snapshot:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Snapshot with ID {snapshot_id} not found"
            )
        
        return snapshot
    
    except Exception as e:
        if isinstance(e, HTTPException):
            raise
        
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve context snapshot: {str(e)}"
        )


@router.post("/query", response_model=ContextResponse, dependencies=[Depends(APIKey)])
async def query_context(
    query: ContextQuery,
    context_cache: ContextService
) -> ContextResponse:
    """Query the context cache for files matching the query."""
    try:
        # Execute the query
        response = await context_cache.query_context(query)
        
        return response
    
    except ValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Invalid query: {str(e)}"
        )
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to query context: {str(e)}"
        )


@router.get("/stats", dependencies=[Depends(APIKey)])
async def get_context_stats(
    context_cache: ContextService
) -> Dict[str, Any]:
    """Get statistics about the context cache."""
    try:
        stats = await context_cache.get_stats()
        
        return stats
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get context stats: {str(e)}"
        ) 