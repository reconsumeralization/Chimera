"""API routes for rule management and evaluation."""

from typing import Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, status

from ...chimera_core.services.service_factory import ServiceFactory
from ...schemas.api import (
    APIErrorCode,
    APIRequest,
    APIResponse,
    APIStatus,
)
from ...schemas.rules import RuleSet

router = APIRouter(prefix="/rules", tags=["rules"])


async def get_service_factory() -> ServiceFactory:
    """
    Get the service factory.
    
    This function should be implemented to return the service factory from the application state.
    For now, it's a placeholder for dependency injection.
    """
    # This would normally be retrieved from app state
    # For example: return request.app.state.service_factory
    raise NotImplementedError("Service factory dependency not implemented")


@router.get("/sets", response_model=APIResponse)
async def get_rule_sets(
    service_factory: ServiceFactory = Depends(get_service_factory),
) -> APIResponse:
    """
    Get all rule sets.
    
    Returns:
        APIResponse: Response containing all rule sets
    """
    try:
        rule_engine = service_factory.get_rule_engine_service()
        
        if not rule_engine:
            return APIResponse(
                status=APIStatus.ERROR,
                message="Rule engine service not available",
                error_code=APIErrorCode.SERVER_ERROR,
            )
        
        rule_sets = rule_engine.get_all_rule_sets()
        
        return APIResponse(
            status=APIStatus.SUCCESS,
            message="Rule sets retrieved successfully",
            data={"rule_sets": [rs.model_dump() for rs in rule_sets]},
        )
    
    except Exception as e:
        return APIResponse(
            status=APIStatus.ERROR,
            message=f"Failed to retrieve rule sets: {str(e)}",
            error_code=APIErrorCode.SERVER_ERROR,
        )


@router.get("/sets/{rule_set_id}", response_model=APIResponse)
async def get_rule_set(
    rule_set_id: str,
    service_factory: ServiceFactory = Depends(get_service_factory),
) -> APIResponse:
    """
    Get a rule set by ID.
    
    Args:
        rule_set_id: ID of the rule set to retrieve
        
    Returns:
        APIResponse: Response containing the rule set
    """
    try:
        rule_engine = service_factory.get_rule_engine_service()
        
        if not rule_engine:
            return APIResponse(
                status=APIStatus.ERROR,
                message="Rule engine service not available",
                error_code=APIErrorCode.SERVER_ERROR,
            )
        
        rule_set = rule_engine.get_rule_set(rule_set_id)
        
        if not rule_set:
            return APIResponse(
                status=APIStatus.ERROR,
                message=f"Rule set with ID {rule_set_id} not found",
                error_code=APIErrorCode.NOT_FOUND,
            )
        
        return APIResponse(
            status=APIStatus.SUCCESS,
            message="Rule set retrieved successfully",
            data={"rule_set": rule_set.model_dump()},
        )
    
    except Exception as e:
        return APIResponse(
            status=APIStatus.ERROR,
            message=f"Failed to retrieve rule set: {str(e)}",
            error_code=APIErrorCode.SERVER_ERROR,
        )


@router.post("/evaluate/{context_id}", response_model=APIResponse)
async def evaluate_rules(
    context_id: str,
    service_factory: ServiceFactory = Depends(get_service_factory),
) -> APIResponse:
    """
    Evaluate rules against a context snapshot.
    
    Args:
        context_id: ID of the context snapshot to evaluate against
        
    Returns:
        APIResponse: Response containing the rule evaluation result
    """
    try:
        # Evaluate rules using the service factory
        result = await service_factory.evaluate_rules_with_context(context_id)
        
        return APIResponse(
            status=APIStatus.SUCCESS,
            message="Rules evaluated successfully",
            data={"evaluation_result": result},
        )
    
    except ValueError as e:
        return APIResponse(
            status=APIStatus.ERROR,
            message=str(e),
            error_code=APIErrorCode.NOT_FOUND,
        )
    
    except RuntimeError as e:
        return APIResponse(
            status=APIStatus.ERROR,
            message=str(e),
            error_code=APIErrorCode.SERVER_ERROR,
        )
    
    except Exception as e:
        return APIResponse(
            status=APIStatus.ERROR,
            message=f"Failed to evaluate rules: {str(e)}",
            error_code=APIErrorCode.SERVER_ERROR,
        ) 