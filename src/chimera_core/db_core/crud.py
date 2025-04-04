"""
CRUD operations for database models.

This module provides functions for interacting with the database models,
including creating, reading, updating, and deleting records.
"""
import datetime
import uuid
from datetime import timedelta
from typing import Any, Dict, List, Optional, Type, TypeVar, Generic, Union, cast, Sequence

import structlog
from sqlalchemy import func, select, delete, desc, or_, text, update
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import Session as SQLModelSession, select

from src.chimera_core.db_core.models import SettingOrm, SnapshotLogOrm, RuleSetOrm, RuleOrm, ContextSnapshotOrm, DiagnosticItemOrm, FileDataOrm
from src.chimera_core.exceptions import DatabaseError, NotFoundError
from src.schemas.context import ContextSnapshot, FileData, DiagnosticItem
from src.schemas.context_schemas import (
    SnapshotLogCreate,
    ContextSnapshotCreate, 
    FileDataCreate, 
    DiagnosticItemCreate
)
from src.schemas.rule_schemas import RuleSetCreate, RuleCreate
from src.schemas.settings_schemas import SettingsCreate, SettingsUpdate

logger = structlog.get_logger(__name__)

T = TypeVar("T")

# Type alias for session
DBSession = Union[AsyncSession, SQLModelSession]


# Settings Operations
async def get_setting(
    session: Union[AsyncSession, SQLModelSession], key: str
) -> Optional[SettingOrm]:
    """
    Get a setting by key.

    Args:
        session: Database session
        key: Setting key

    Returns:
        Optional[SettingOrm]: The setting if found
    """
    try:
        is_async = isinstance(session, AsyncSession)
        
        # Create the select statement
        statement = select(SettingOrm).where(SettingOrm.key == key)
        
        if is_async:
            # For AsyncSession, use await session.execute()
            result = await session.execute(statement)
            return result.scalar_one_or_none()
        else:
            # For SQLModelSession, use session.exec()
            result = session.exec(statement)
            return result.first()
    except SQLAlchemyError as e:
        logger.error("Error getting setting", key=key, error=str(e))
        raise DatabaseError(f"Error getting setting {key}: {str(e)}") from e


async def get_settings(session: Union[AsyncSession, SQLModelSession]) -> List[SettingOrm]:
    """
    Get all settings.

    Args:
        session: Database session

    Returns:
        List[SettingOrm]: List of all settings
    """
    try:
        statement = select(SettingOrm)
        
        is_async = isinstance(session, AsyncSession)
        
        if is_async:
            # For AsyncSession
            result = await session.execute(statement)
            return result.scalars().all()
        else:
            # For SQLModelSession
            result = session.exec(statement)
            return result.all()
    except SQLAlchemyError as e:
        logger.error("Error getting settings", error=str(e))
        raise DatabaseError(f"Error getting settings: {str(e)}") from e


async def create_or_update_setting(
    session: Union[AsyncSession, SQLModelSession], key: str, value: str, description: Optional[str] = None
) -> SettingOrm:
    """
    Create or update a setting.

    Args:
        session: Database session
        key: Setting key
        value: Setting value
        description: Setting description

    Returns:
        SettingOrm: The created or updated setting
    """
    try:
        # Check if the setting exists
        existing = await get_setting(session, key)
        
        if existing:
            # Update the existing setting
            existing.value = value
            if description is not None:
                existing.description = description
            existing.updated_at = datetime.datetime.now()
            session.add(existing)
            return existing
        else:
            # Create a new setting
            new_setting = SettingOrm(
                key=key,
                value=value,
                description=description
            )
            session.add(new_setting)
            return new_setting
    except SQLAlchemyError as e:
        logger.error("Error saving setting", key=key, error=str(e))
        raise DatabaseError(f"Error saving setting {key}: {str(e)}") from e


# Snapshot Log Operations
async def create_snapshot_log(
    session: Union[AsyncSession, SQLModelSession],
    snapshot_id: str,
    operation: str,
    user_id: Optional[str] = None,
    workspace_id: Optional[str] = None,
    metadata: Optional[Dict[str, Any]] = None,
) -> SnapshotLogOrm:
    """
    Create a snapshot log entry.

    Args:
        session: Database session
        snapshot_id: ID of the snapshot
        operation: Operation performed (e.g., "create", "update")
        user_id: ID of the user (optional)
        workspace_id: ID of the workspace (optional)
        metadata: Additional metadata (optional)

    Returns:
        SnapshotLogOrm: The created log entry
    """
    try:
        log_entry = SnapshotLogOrm(
            snapshot_id=snapshot_id,
            operation=operation,
            user_id=user_id,
            workspace_id=workspace_id,
            meta_data=metadata or {},
        )
        session.add(log_entry)
        return log_entry
    except SQLAlchemyError as e:
        logger.error("Error creating snapshot log", snapshot_id=snapshot_id, error=str(e))
        raise DatabaseError(f"Error creating snapshot log: {str(e)}") from e


async def get_snapshot_logs(
    session: Union[AsyncSession, SQLModelSession],
    snapshot_id: Optional[str] = None,
    limit: int = 100,
    offset: int = 0,
) -> List[SnapshotLogOrm]:
    """
    Get snapshot logs, optionally filtered by snapshot ID.

    Args:
        session: Database session
        snapshot_id: Filter by snapshot ID (optional)
        limit: Maximum number of logs to return
        offset: Offset for pagination

    Returns:
        List[SnapshotLogOrm]: List of snapshot logs
    """
    try:
        is_async = isinstance(session, AsyncSession)
        query = select(SnapshotLogOrm).order_by(SnapshotLogOrm.timestamp.desc())
        
        if snapshot_id:
            query = query.where(SnapshotLogOrm.snapshot_id == snapshot_id)
        
        query = query.limit(limit).offset(offset)
        
        if is_async:
            result = await session.execute(query)
            return result.scalars().all()
        else:
            result = session.exec(query)
            return result.all()
    except SQLAlchemyError as e:
        logger.error("Error getting snapshot logs", error=str(e))
        raise DatabaseError(f"Error getting snapshot logs: {str(e)}") from e


# Rule Set Operations
async def get_rule_set(
    session: Union[AsyncSession, SQLModelSession], rule_set_id: str
) -> Optional[RuleSetOrm]:
    """
    Get a rule set by ID.

    Args:
        session: Database session
        rule_set_id: Rule set ID

    Returns:
        Optional[RuleSetOrm]: The rule set if found
    """
    try:
        is_async = isinstance(session, AsyncSession)
        query = select(RuleSetOrm).where(RuleSetOrm.id == rule_set_id)
        
        if is_async:
            result = await session.execute(query)
            return result.scalar_one_or_none()
        else:
            result = session.exec(query)
            return result.first()
    except SQLAlchemyError as e:
        logger.error("Error getting rule set", rule_set_id=rule_set_id, error=str(e))
        raise DatabaseError(f"Error getting rule set {rule_set_id}: {str(e)}") from e


async def get_rule_sets(session: Union[AsyncSession, SQLModelSession]) -> List[RuleSetOrm]:
    """
    Get all rule sets.

    Args:
        session: Database session

    Returns:
        List[RuleSetOrm]: All rule sets
    """
    try:
        is_async = isinstance(session, AsyncSession)
        query = select(RuleSetOrm)
        
        if is_async:
            result = await session.execute(query)
            return result.scalars().all()
        else:
            result = session.exec(query)
            return result.all()
    except SQLAlchemyError as e:
        logger.error("Error getting all rule sets", error=str(e))
        raise DatabaseError(f"Error getting all rule sets: {str(e)}") from e


async def create_or_update_rule_set(
    session: Union[AsyncSession, SQLModelSession],
    rule_set_id: str,
    name: str,
    description: Optional[str] = None,
    enabled: bool = True,
) -> RuleSetOrm:
    """
    Create or update a rule set.

    Args:
        session: Database session
        rule_set_id: Rule set ID
        name: Rule set name
        description: Rule set description
        enabled: Whether the rule set is enabled

    Returns:
        RuleSetOrm: The created or updated rule set
    """
    try:
        # Check if the rule set exists
        existing = await get_rule_set(session, rule_set_id)
        
        if existing:
            # Update the existing rule set
            existing.name = name
            existing.description = description
            existing.enabled = enabled
            existing.updated_at = datetime.datetime.now()
            session.add(existing)
            return existing
        else:
            # Create a new rule set
            new_rule_set = RuleSetOrm(
                id=rule_set_id,
                name=name,
                description=description,
                enabled=enabled,
            )
            session.add(new_rule_set)
            return new_rule_set
    except SQLAlchemyError as e:
        logger.error("Error saving rule set", rule_set_id=rule_set_id, error=str(e))
        raise DatabaseError(f"Error saving rule set {rule_set_id}: {str(e)}") from e


# Rule Operations
async def get_rule(
    session: Union[AsyncSession, SQLModelSession], rule_id: str
) -> Optional[RuleOrm]:
    """
    Get a rule by ID.

    Args:
        session: Database session
        rule_id: Rule ID

    Returns:
        Optional[RuleOrm]: The rule if found
    """
    try:
        is_async = isinstance(session, AsyncSession)
        query = select(RuleOrm).where(RuleOrm.id == rule_id)
        
        if is_async:
            result = await session.execute(query)
            return result.scalar_one_or_none()
        else:
            result = session.exec(query)
            return result.first()
    except SQLAlchemyError as e:
        logger.error("Error getting rule", rule_id=rule_id, error=str(e))
        raise DatabaseError(f"Error getting rule {rule_id}: {str(e)}") from e


async def get_rules(
    session: Union[AsyncSession, SQLModelSession], rule_set_id: Optional[str] = None
) -> List[RuleOrm]:
    """
    Get all rules, optionally filtered by rule set ID.

    Args:
        session: Database session
        rule_set_id: Filter by rule set ID (optional)

    Returns:
        List[RuleOrm]: All matching rules
    """
    try:
        is_async = isinstance(session, AsyncSession)
        query = select(RuleOrm).order_by(RuleOrm.priority.desc())
        
        if rule_set_id:
            query = query.where(RuleOrm.rule_set_id == rule_set_id)
        
        if is_async:
            result = await session.execute(query)
            return result.scalars().all()
        else:
            result = session.exec(query)
            return result.all()
    except SQLAlchemyError as e:
        logger.error("Error getting rules", rule_set_id=rule_set_id, error=str(e))
        raise DatabaseError(f"Error getting rules: {str(e)}") from e


async def create_or_update_rule(
    session: Union[AsyncSession, SQLModelSession],
    rule_id: str,
    rule_set_id: str,
    name: str,
    condition: str,
    actions: List[Dict[str, Any]],
    description: Optional[str] = None,
    enabled: bool = True,
    priority: int = 0,
) -> RuleOrm:
    """
    Create or update a rule.

    Args:
        session: Database session
        rule_id: Rule ID
        rule_set_id: Rule set ID
        name: Rule name
        condition: Rule condition
        actions: Rule actions
        description: Rule description
        enabled: Whether the rule is enabled
        priority: Rule priority

    Returns:
        RuleOrm: The created or updated rule
    """
    try:
        # Check if the rule set exists
        rule_set = await get_rule_set(session, rule_set_id)
        if not rule_set:
            raise NotFoundError(f"Rule set {rule_set_id} not found")
        
        # Check if the rule exists
        existing = await get_rule(session, rule_id)
        
        if existing:
            # Update the existing rule
            existing.rule_set_id = rule_set_id
            existing.name = name
            existing.description = description
            existing.condition = condition
            existing.actions = actions
            existing.enabled = enabled
            existing.priority = priority
            existing.updated_at = datetime.datetime.now()
            session.add(existing)
            return existing
        else:
            # Create a new rule
            new_rule = RuleOrm(
                id=rule_id,
                rule_set_id=rule_set_id,
                name=name,
                description=description,
                condition=condition,
                actions=actions,
                enabled=enabled,
                priority=priority,
            )
            session.add(new_rule)
            return new_rule
    except NotFoundError:
        raise
    except SQLAlchemyError as e:
        logger.error("Error saving rule", rule_id=rule_id, error=str(e))
        raise DatabaseError(f"Error saving rule {rule_id}: {str(e)}") from e


# Context Snapshot Operations
async def create_context_snapshot(
    session: DBSession,
    snapshot: ContextSnapshot,
) -> ContextSnapshotOrm:
    """
    Create a new context snapshot in the database.
    
    Args:
        session: Database session
        snapshot: The context snapshot data
        
    Returns:
        ContextSnapshotOrm: The created snapshot
    """
    try:
        # Generate ID if not provided
        snapshot_id = str(uuid.uuid4())
        
        # Calculate size
        snapshot_size = len(snapshot.model_dump_json())
        
        # Create the snapshot record
        snapshot_orm = ContextSnapshotOrm(
            id=snapshot_id,
            timestamp=snapshot.timestamp,
            workspace_root=snapshot.workspace_root,
            active_file=snapshot.active_file,
            meta_data=snapshot.metadata,
            size_bytes=snapshot_size,
        )
        
        session.add(snapshot_orm)
        
        # Create file records
        for file_data in snapshot.files:
            file_orm = FileDataOrm(
                id=str(uuid.uuid4()),
                snapshot_id=snapshot_id,
                path=file_data.path,
                language=file_data.language,
                size_bytes=file_data.size_bytes,
                last_modified=file_data.last_modified,
                is_open=file_data.is_open,
                is_dirty=file_data.is_dirty,
                has_content=file_data.content is not None,
                # Optionally store content if needed
                # content=file_data.content,
            )
            session.add(file_orm)
        
        # Create diagnostic records
        for diag in snapshot.diagnostics:
            diag_orm = DiagnosticItemOrm(
                id=str(uuid.uuid4()),
                snapshot_id=snapshot_id,
                file_path=diag.file_path,
                message=diag.message,
                severity=diag.severity,
                line=diag.line,
                column=diag.column,
                source=diag.source,
                code=diag.code,
            )
            session.add(diag_orm)
        
        return snapshot_orm
    
    except SQLAlchemyError as e:
        logger.error("Error creating context snapshot", error=str(e))
        raise DatabaseError(f"Error creating context snapshot: {str(e)}") from e


async def get_context_snapshot(
    session: DBSession,
    snapshot_id: str,
    include_files: bool = True,
    include_diagnostics: bool = True,
) -> Optional[ContextSnapshotOrm]:
    """
    Get a context snapshot by ID.
    
    Args:
        session: Database session
        snapshot_id: ID of the snapshot
        include_files: Whether to include file data
        include_diagnostics: Whether to include diagnostic data
        
    Returns:
        Optional[ContextSnapshotOrm]: The snapshot if found, None otherwise
    """
    try:
        statement = select(ContextSnapshotOrm).where(ContextSnapshotOrm.id == snapshot_id)
        
        if isinstance(session, AsyncSession):
            result = await session.execute(statement)
            snapshot = result.scalar_one_or_none()
        else:
            result = session.exec(statement)
            snapshot = result.first()
        
        if snapshot and include_files:
            # Eagerly load files if requested
            file_statement = select(FileDataOrm).where(FileDataOrm.snapshot_id == snapshot_id)
            
            if isinstance(session, AsyncSession):
                file_result = await session.execute(file_statement)
                snapshot.files = file_result.scalars().all()
            else:
                file_result = session.exec(file_statement)
                snapshot.files = file_result.all()
        
        if snapshot and include_diagnostics:
            # Eagerly load diagnostics if requested
            diag_statement = select(DiagnosticItemOrm).where(DiagnosticItemOrm.snapshot_id == snapshot_id)
            
            if isinstance(session, AsyncSession):
                diag_result = await session.execute(diag_statement)
                snapshot.diagnostics = diag_result.scalars().all()
            else:
                diag_result = session.exec(diag_statement)
                snapshot.diagnostics = diag_result.all()
        
        return snapshot
    
    except SQLAlchemyError as e:
        logger.error("Error getting context snapshot", snapshot_id=snapshot_id, error=str(e))
        raise DatabaseError(f"Error getting context snapshot: {str(e)}") from e


async def get_recent_context_snapshots(
    session: DBSession,
    limit: int = 20,
    include_files: bool = False,
    include_diagnostics: bool = False,
) -> List[ContextSnapshotOrm]:
    """
    Get recent context snapshots.
    
    Args:
        session: Database session
        limit: Maximum number of snapshots to return
        include_files: Whether to include file data
        include_diagnostics: Whether to include diagnostic data
        
    Returns:
        List[ContextSnapshotOrm]: List of recent snapshots
    """
    try:
        statement = (
            select(ContextSnapshotOrm)
            .order_by(desc(ContextSnapshotOrm.timestamp))
            .limit(limit)
        )
        
        if isinstance(session, AsyncSession):
            result = await session.execute(statement)
            snapshots = result.scalars().all()
        else:
            result = session.exec(statement)
            snapshots = result.all()
        
        # Optionally load related data
        if snapshots and (include_files or include_diagnostics):
            for snapshot in snapshots:
                if include_files:
                    file_statement = select(FileDataOrm).where(FileDataOrm.snapshot_id == snapshot.id)
                    
                    if isinstance(session, AsyncSession):
                        file_result = await session.execute(file_statement)
                        snapshot.files = file_result.scalars().all()
                    else:
                        file_result = session.exec(file_statement)
                        snapshot.files = file_result.all()
                
                if include_diagnostics:
                    diag_statement = select(DiagnosticItemOrm).where(DiagnosticItemOrm.snapshot_id == snapshot.id)
                    
                    if isinstance(session, AsyncSession):
                        diag_result = await session.execute(diag_statement)
                        snapshot.diagnostics = diag_result.scalars().all()
                    else:
                        diag_result = session.exec(diag_statement)
                        snapshot.diagnostics = diag_result.all()
        
        return list(snapshots)
    
    except SQLAlchemyError as e:
        logger.error("Error getting recent context snapshots", error=str(e))
        raise DatabaseError(f"Error getting recent context snapshots: {str(e)}") from e


async def delete_context_snapshot(
    session: DBSession,
    snapshot_id: str,
) -> bool:
    """
    Delete a context snapshot.
    
    Args:
        session: Database session
        snapshot_id: ID of the snapshot to delete
        
    Returns:
        bool: True if snapshot was deleted, False if not found
    """
    try:
        # SQLModel/SQLAlchemy should cascade delete related records
        statement = delete(ContextSnapshotOrm).where(ContextSnapshotOrm.id == snapshot_id)
        
        if isinstance(session, AsyncSession):
            result = await session.execute(statement)
            deleted = result.rowcount > 0
        else:
            result = session.exec(statement)
            deleted = result.rowcount > 0
        
        return deleted
    
    except SQLAlchemyError as e:
        logger.error("Error deleting context snapshot", snapshot_id=snapshot_id, error=str(e))
        raise DatabaseError(f"Error deleting context snapshot: {str(e)}") from e


async def delete_old_context_snapshots(
    session: DBSession,
    days_old: int = 7,
) -> int:
    """
    Delete context snapshots older than the specified number of days.
    
    Args:
        session: Database session
        days_old: Delete snapshots older than this many days
        
    Returns:
        int: Number of snapshots deleted
    """
    try:
        cutoff_date = datetime.utcnow() - timedelta(days=days_old)
        statement = delete(ContextSnapshotOrm).where(ContextSnapshotOrm.timestamp < cutoff_date)
        
        if isinstance(session, AsyncSession):
            result = await session.execute(statement)
            deleted_count = result.rowcount
        else:
            result = session.exec(statement)
            deleted_count = result.rowcount
        
        return deleted_count if deleted_count is not None else 0
    
    except SQLAlchemyError as e:
        logger.error("Error deleting old context snapshots", days_old=days_old, error=str(e))
        raise DatabaseError(f"Error deleting old context snapshots: {str(e)}") from e


async def convert_snapshot_to_schema(
    snapshot_orm: ContextSnapshotOrm,
) -> ContextSnapshot:
    """
    Convert an ORM snapshot to a schema snapshot.
    
    Args:
        snapshot_orm: The ORM snapshot
        
    Returns:
        ContextSnapshot: The schema snapshot
    """
    # Convert files
    files = []
    for file_orm in getattr(snapshot_orm, "files", []):
        file_data = FileData(
            path=file_orm.path,
            language=file_orm.language,
            size_bytes=file_orm.size_bytes,
            last_modified=file_orm.last_modified,
            is_open=file_orm.is_open,
            is_dirty=file_orm.is_dirty,
            content=file_orm.content,
        )
        files.append(file_data)
    
    # Convert diagnostics
    diagnostics = []
    for diag_orm in getattr(snapshot_orm, "diagnostics", []):
        diagnostic = DiagnosticItem(
            file_path=diag_orm.file_path,
            message=diag_orm.message,
            severity=diag_orm.severity,
            line=diag_orm.line,
            column=diag_orm.column,
            source=diag_orm.source,
            code=diag_orm.code,
        )
        diagnostics.append(diagnostic)
    
    # Create the snapshot
    return ContextSnapshot(
        timestamp=snapshot_orm.timestamp,
        workspace_root=snapshot_orm.workspace_root,
        active_file=snapshot_orm.active_file,
        files=files,
        diagnostics=diagnostics,
        metadata=snapshot_orm.meta_data or {},
    )


# --- Generic CRUD Operations ---

async def get[ModelType](db: AsyncSession, model_id: uuid.UUID, model_class: Type[ModelType]) -> Optional[ModelType]:
    """Get a single model instance by ID."""
    result = await db.execute(select(model_class).filter(model_class.id == model_id))
    return result.scalars().first()

async def get_all[ModelType](db: AsyncSession, model_class: Type[ModelType], skip: int = 0, limit: int = 100) -> Sequence[ModelType]:
    """Get multiple model instances with pagination."""
    result = await db.execute(select(model_class).offset(skip).limit(limit))
    return result.scalars().all()

async def create[ModelType, CreateSchemaType](db: AsyncSession, obj_in: CreateSchemaType, model_class: Type[ModelType]) -> ModelType:
    """Create a new model instance."""
    db_obj = model_class(**obj_in.model_dump())
    db.add(db_obj)
    await db.commit()
    await db.refresh(db_obj)
    return db_obj

# --- SnapshotLog CRUD ---

async def create_snapshot_log(db: AsyncSession, log_in: SnapshotLogCreate) -> SnapshotLogOrm:
    log_dict = log_in.model_dump(exclude_unset=True)
    # We don't create the nested snapshot here, it will be linked later
    log_dict.pop('context_snapshot', None)
    db_log = SnapshotLogOrm(**log_dict)
    db.add(db_log)
    await db.commit()
    await db.refresh(db_log)
    return db_log

async def get_snapshot_log(db: AsyncSession, log_id: uuid.UUID) -> Optional[SnapshotLogOrm]:
    return await get(db, log_id, SnapshotLogOrm)

async def get_snapshot_logs(db: AsyncSession, skip: int = 0, limit: int = 100) -> Sequence[SnapshotLogOrm]:
    return await get_all(db, SnapshotLogOrm, skip=skip, limit=limit)

# --- ContextSnapshot CRUD ---

async def create_context_snapshot(db: AsyncSession, snapshot_in: ContextSnapshotCreate, log_id: uuid.UUID) -> ContextSnapshotOrm:
    snapshot_dict = snapshot_in.model_dump(exclude={'files', 'diagnostics'})
    snapshot_dict['log_id'] = log_id
    db_snapshot = ContextSnapshotOrm(**snapshot_dict)
    db.add(db_snapshot)
    # We need the snapshot ID before creating nested files/diagnostics
    await db.flush() 
    await db.refresh(db_snapshot)

    # Create related files
    if snapshot_in.files:
        for file_in in snapshot_in.files:
            await create_file_data(db, file_in, snapshot_id=db_snapshot.id)
            
    # Create related diagnostics
    if snapshot_in.diagnostics:
        for diag_in in snapshot_in.diagnostics:
            await create_diagnostic_item(db, diag_in, snapshot_id=db_snapshot.id)
            
    await db.commit()
    await db.refresh(db_snapshot) # Refresh again to load relationships
    return db_snapshot

async def get_context_snapshot(db: AsyncSession, snapshot_id: uuid.UUID) -> Optional[ContextSnapshotOrm]:
    # Potentially use joinedload or selectinload for relationships if needed frequently
    result = await db.execute(
        select(ContextSnapshotOrm)
        .options(relationship('files'), relationship('diagnostics'))
        .filter(ContextSnapshotOrm.id == snapshot_id)
    )
    return result.scalars().first()

async def get_context_snapshots(db: AsyncSession, skip: int = 0, limit: int = 100) -> Sequence[ContextSnapshotOrm]:
    return await get_all(db, ContextSnapshotOrm, skip=skip, limit=limit)


# --- FileData CRUD ---

async def create_file_data(db: AsyncSession, file_in: FileDataCreate, snapshot_id: uuid.UUID) -> FileDataOrm:
    db_file = FileDataOrm(**file_in.model_dump(), snapshot_id=snapshot_id)
    db.add(db_file)
    # Commit happens at the end of create_context_snapshot
    return db_file

# --- DiagnosticItem CRUD ---

async def create_diagnostic_item(db: AsyncSession, diag_in: DiagnosticItemCreate, snapshot_id: uuid.UUID) -> DiagnosticItemOrm:
    db_diag = DiagnosticItemOrm(**diag_in.model_dump(), snapshot_id=snapshot_id)
    db.add(db_diag)
    # Commit happens at the end of create_context_snapshot
    return db_diag

# --- RuleSet CRUD ---

async def create_rule_set(db: AsyncSession, ruleset_in: RuleSetCreate) -> RuleSetOrm:
    return await create(db, ruleset_in, RuleSetOrm)

async def get_rule_set(db: AsyncSession, ruleset_id: uuid.UUID) -> Optional[RuleSetOrm]:
    return await get(db, ruleset_id, RuleSetOrm)

async def get_rule_set_by_name(db: AsyncSession, name: str) -> Optional[RuleSetOrm]:
    result = await db.execute(select(RuleSetOrm).filter(RuleSetOrm.name == name))
    return result.scalars().first()

async def get_rule_sets(db: AsyncSession, skip: int = 0, limit: int = 100) -> Sequence[RuleSetOrm]:
    return await get_all(db, RuleSetOrm, skip=skip, limit=limit)

# --- Rule CRUD ---

async def create_rule(db: AsyncSession, rule_in: RuleCreate, rule_set_id: uuid.UUID) -> RuleOrm:
    db_rule = RuleOrm(**rule_in.model_dump(), rule_set_id=rule_set_id)
    db.add(db_rule)
    await db.commit()
    await db.refresh(db_rule)
    return db_rule

async def get_rule(db: AsyncSession, rule_id: uuid.UUID) -> Optional[RuleOrm]:
    return await get(db, rule_id, RuleOrm)

async def get_rules_by_ruleset(db: AsyncSession, rule_set_id: uuid.UUID, skip: int = 0, limit: int = 1000) -> Sequence[RuleOrm]:
    result = await db.execute(
        select(RuleOrm)
        .filter(RuleOrm.rule_set_id == rule_set_id)
        .offset(skip)
        .limit(limit)
    )
    return result.scalars().all()

# --- Settings CRUD ---

async def get_setting(db: AsyncSession, key: str) -> Optional[SettingOrm]:
    result = await db.execute(select(SettingOrm).filter(SettingOrm.key == key))
    return result.scalars().first()

async def get_settings(db: AsyncSession, skip: int = 0, limit: int = 100) -> Sequence[SettingOrm]:
    return await get_all(db, SettingOrm, skip=skip, limit=limit)

async def create_setting(db: AsyncSession, setting_in: SettingsCreate) -> SettingOrm:
    return await create(db, setting_in, SettingOrm)

async def update_setting(db: AsyncSession, key: str, setting_in: SettingsUpdate) -> Optional[SettingOrm]:
    db_setting = await get_setting(db, key)
    if db_setting:
        update_data = setting_in.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(db_setting, field, value)
        await db.commit()
        await db.refresh(db_setting)
    return db_setting

async def delete_setting(db: AsyncSession, key: str) -> bool:
    db_setting = await get_setting(db, key)
    if db_setting:
        await db.delete(db_setting)
        await db.commit()
        return True
    return False 