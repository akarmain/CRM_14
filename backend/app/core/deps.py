from __future__ import annotations

from collections.abc import AsyncIterator
from functools import lru_cache

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.application.ports import (
    AuditLogRepository,
    CommentRepository,
    LeadRepository,
    ReturnRequestRepository,
    StageEventRepository,
)
from app.application.use_cases.create_lead import CreateLeadUseCase
from app.application.use_cases.delete_lead import DeleteLeadUseCase
from app.application.use_cases.export_leads import ExportLeadsUseCase
from app.application.use_cases.get_lead import GetLeadUseCase
from app.application.use_cases.list_leads import ListLeadsUseCase
from app.application.use_cases.list_stages import ListStagesUseCase
from app.application.use_cases.move_stage import MoveStageUseCase
from app.application.use_cases.update_lead import UpdateLeadUseCase
from app.core.config import get_settings
from app.infrastructure.memo.repo import MemoRepositories
from app.infrastructure.onec.repo_stub import OneCRepositoryStub
from app.infrastructure.sql.db import DatabaseManager
from app.infrastructure.sql.repo import PostgresRepositories


@lru_cache
def _get_memo_repo() -> MemoRepositories:
    return MemoRepositories()


@lru_cache
def _get_onec_repo() -> OneCRepositoryStub:
    return OneCRepositoryStub()


@lru_cache
def _get_db_manager() -> DatabaseManager:
    return DatabaseManager(get_settings().database_url)


async def get_db_session() -> AsyncIterator[AsyncSession | None]:
    settings = get_settings()
    if settings.storage_mode != "postgres":
        yield None
        return

    async with _get_db_manager().session() as session:
        yield session


def _get_non_sql_repo():
    settings = get_settings()
    if settings.storage_mode == "memo":
        return _get_memo_repo()
    return _get_onec_repo()


def _resolve_repo_bundle(db_session: AsyncSession | None) -> MemoRepositories | OneCRepositoryStub | PostgresRepositories:
    settings = get_settings()
    if settings.storage_mode == "postgres":
        if db_session is None:
            raise RuntimeError("Async DB session is required for postgres storage.")
        return PostgresRepositories(db_session)
    return _get_non_sql_repo()


def get_lead_repository(db_session: AsyncSession | None = Depends(get_db_session)) -> LeadRepository:
    return _resolve_repo_bundle(db_session)


def get_stage_event_repository(
    db_session: AsyncSession | None = Depends(get_db_session),
) -> StageEventRepository:
    return _resolve_repo_bundle(db_session)


def get_comment_repository(
    db_session: AsyncSession | None = Depends(get_db_session),
) -> CommentRepository:
    return _resolve_repo_bundle(db_session)


def get_return_request_repository(
    db_session: AsyncSession | None = Depends(get_db_session),
) -> ReturnRequestRepository:
    return _resolve_repo_bundle(db_session)


def get_audit_log_repository(
    db_session: AsyncSession | None = Depends(get_db_session),
) -> AuditLogRepository:
    return _resolve_repo_bundle(db_session)


def get_create_lead_use_case(
    lead_repo: LeadRepository = Depends(get_lead_repository),
    stage_repo: StageEventRepository = Depends(get_stage_event_repository),
) -> CreateLeadUseCase:
    return CreateLeadUseCase(lead_repo, stage_repo)


def get_get_lead_use_case(
    lead_repo: LeadRepository = Depends(get_lead_repository),
    stage_repo: StageEventRepository = Depends(get_stage_event_repository),
    comment_repo: CommentRepository = Depends(get_comment_repository),
) -> GetLeadUseCase:
    return GetLeadUseCase(lead_repo, stage_repo, comment_repo)


def get_delete_lead_use_case(
    lead_repo: LeadRepository = Depends(get_lead_repository),
) -> DeleteLeadUseCase:
    return DeleteLeadUseCase(lead_repo)


def get_list_leads_use_case(
    lead_repo: LeadRepository = Depends(get_lead_repository),
    stage_repo: StageEventRepository = Depends(get_stage_event_repository),
    comment_repo: CommentRepository = Depends(get_comment_repository),
) -> ListLeadsUseCase:
    return ListLeadsUseCase(lead_repo, stage_repo, comment_repo)


def get_export_leads_use_case(
    lead_repo: LeadRepository = Depends(get_lead_repository),
    stage_repo: StageEventRepository = Depends(get_stage_event_repository),
) -> ExportLeadsUseCase:
    return ExportLeadsUseCase(lead_repo, stage_repo)


def get_move_stage_use_case(
    lead_repo: LeadRepository = Depends(get_lead_repository),
    stage_repo: StageEventRepository = Depends(get_stage_event_repository),
    comment_repo: CommentRepository = Depends(get_comment_repository),
) -> MoveStageUseCase:
    return MoveStageUseCase(lead_repo, stage_repo, comment_repo)


def get_list_stages_use_case(
    lead_repo: LeadRepository = Depends(get_lead_repository),
    stage_repo: StageEventRepository = Depends(get_stage_event_repository),
    comment_repo: CommentRepository = Depends(get_comment_repository),
) -> ListStagesUseCase:
    return ListStagesUseCase(lead_repo, stage_repo, comment_repo)


def get_update_lead_use_case(
    lead_repo: LeadRepository = Depends(get_lead_repository),
) -> UpdateLeadUseCase:
    return UpdateLeadUseCase(lead_repo)


def reset_container() -> None:
    get_settings.cache_clear()
    _get_memo_repo.cache_clear()
    _get_onec_repo.cache_clear()
    _get_db_manager.cache_clear()
