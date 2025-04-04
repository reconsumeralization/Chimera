"""API routes for context management.

This module provides the API routes for context management, including
storing and retrieving context snapshots.
"""

import logging
import uuid
from typing import Dict, Any

from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks

from ...schemas.context_schemas import (
    ContextSnapshotSchema, ContextQuery, ContextSnapshotResponse, ContextStats
)
from ...services.context_cache_service import ContextCacheService
from ...services.rule_engine_service import RuleEngineService
from ..dependencies import ContextServiceDep, RuleEngineServiceDep

logger = logging.getLogger(__name__)

# Create the router
router = APIRouter(prefix="/context", tags=["context"])


@router.post(
    "/snapshot", 
    response_model=Dict[str, Any], # Simple ack response
    status_code=status.HTTP_202_ACCEPTED,
    summary="Receive and store a context snapshot"
)
async def store_context_snapshot(
    snapshot_data: ContextSnapshotSchema,
    background_tasks: BackgroundTasks,
    context_service: ContextServiceDep,
    rule_engine_service: RuleEngineServiceDep,
):
    """
    Receives a context snapshot from the client (e.g., VS Code extension),
    stores it, and triggers background processing (like rule evaluation).
    """
    try:
        logger.info(f"Received snapshot for workspace: {snapshot_data.workspace_path}")
        # Store snapshot immediately (in-memory + trigger DB save)
        snapshot_id = await context_service.store_snapshot(snapshot_data)
        logger.info(f"Snapshot stored with ID: {snapshot_id}")
        
        # Trigger rule evaluation in the background
        background_tasks.add_task(
            rule_engine_service.evaluate_rules_for_snapshot, 
            snapshot_id=snapshot_id,
            snapshot_data=snapshot_data # Pass data for rules to use
        )
        logger.debug(f"Rule evaluation task added for snapshot {snapshot_id}")
        
        return {"message": "Snapshot received and processing initiated", "snapshot_id": str(snapshot_id)}
    
    except Exception as e:
        logger.exception(f"Error processing snapshot: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to process snapshot: {str(e)}"
        )

@router.post(
    "/query", 
    response_model=ContextSnapshotResponse, # Or a specific query result schema
    summary="Query relevant context based on criteria"
)
async def query_context(
    query: ContextQuery,
    context_service: ContextServiceDep,
):
    """
    Queries the stored context snapshots based on the provided criteria.
    (Currently retrieves the latest snapshot, will be expanded for DB queries).
    """
    try:
        logger.info(f"Received context query for task: {query.task_description}")
        # TODO: Implement sophisticated DB querying based on query parameters
        # For now, just return the latest snapshot or specific one by ID if provided
        if query.snapshot_id:
            snapshot = await context_service.get_snapshot(query.snapshot_id)
            if not snapshot:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Snapshot not found")
            return snapshot
        else:
            # Placeholder: Get latest or most relevant based on query (needs DB impl)
            latest_snapshot = await context_service.get_latest_snapshot() # Assumes this method exists
            if not latest_snapshot:
                 raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No snapshots available")
            return latest_snapshot

    except HTTPException as http_exc:
        raise http_exc # Re-raise FastAPI specific exceptions
    except Exception as e:
        logger.exception(f"Error during context query: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to query context: {str(e)}"
        )

@router.get(
    "/snapshot/{snapshot_id}", 
    response_model=ContextSnapshotResponse, 
    summary="Get a specific context snapshot by ID"
)
async def get_specific_snapshot(
    snapshot_id: uuid.UUID,
    context_service: ContextServiceDep,
):
    """
    Retrieves a specific context snapshot using its unique ID.
    """
    try:
        logger.info(f"Requesting snapshot with ID: {snapshot_id}")
        snapshot = await context_service.get_snapshot(snapshot_id)
        if not snapshot:
            logger.warning(f"Snapshot with ID {snapshot_id} not found.")
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Snapshot not found")
        logger.debug(f"Returning snapshot {snapshot_id}")
        return snapshot
    except Exception as e:
        logger.exception(f"Error retrieving snapshot {snapshot_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve snapshot: {str(e)}"
        )

@router.get(
    "/stats", 
    response_model=ContextStats, 
    summary="Get statistics about the stored context"
)
async def get_context_stats(
    context_service: ContextServiceDep,
):
    """
    Retrieves statistics about the context cache (e.g., number of snapshots).
    """
    try:
        logger.info("Requesting context statistics")
        stats = await context_service.get_stats()
        logger.debug(f"Returning context stats: {stats}")
        return stats
    except Exception as e:
        logger.exception(f"Error retrieving context stats: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get context stats: {str(e)}"
        ) 