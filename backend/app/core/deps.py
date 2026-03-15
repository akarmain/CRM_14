from functools import lru_cache

from app.application.ports import CommentRepository, LeadRepository, StageEventRepository
from app.application.use_cases.create_lead import CreateLeadUseCase
from app.application.use_cases.delete_lead import DeleteLeadUseCase
from app.application.use_cases.get_lead import GetLeadUseCase
from app.application.use_cases.list_leads import ListLeadsUseCase
from app.application.use_cases.list_stages import ListStagesUseCase
from app.application.use_cases.move_stage import MoveStageUseCase
from app.core.config import get_settings
from app.infrastructure.memo.repo import MemoRepositories
from app.infrastructure.onec.repo_stub import OneCRepositoryStub


@lru_cache
def _get_memo_repo() -> MemoRepositories:
    return MemoRepositories()


@lru_cache
def _get_onec_repo() -> OneCRepositoryStub:
    return OneCRepositoryStub()


def _resolve_repos() -> tuple[LeadRepository, StageEventRepository, CommentRepository]:
    settings = get_settings()
    if settings.storage_mode == "memo":
        memo_repo = _get_memo_repo()
        return memo_repo, memo_repo, memo_repo

    onec_repo = _get_onec_repo()
    return onec_repo, onec_repo, onec_repo


def get_lead_repository() -> LeadRepository:
    lead_repo, _, _ = _resolve_repos()
    return lead_repo


def get_stage_event_repository() -> StageEventRepository:
    _, stage_repo, _ = _resolve_repos()
    return stage_repo


def get_comment_repository() -> CommentRepository:
    _, _, comment_repo = _resolve_repos()
    return comment_repo


def get_create_lead_use_case() -> CreateLeadUseCase:
    return CreateLeadUseCase(get_lead_repository(), get_stage_event_repository())


def get_get_lead_use_case() -> GetLeadUseCase:
    return GetLeadUseCase(
        get_lead_repository(),
        get_stage_event_repository(),
        get_comment_repository(),
    )

def get_delete_lead_use_case() -> DeleteLeadUseCase:
    return DeleteLeadUseCase(get_lead_repository())


def get_list_leads_use_case() -> ListLeadsUseCase:
    return ListLeadsUseCase(
        get_lead_repository(),
        get_stage_event_repository(),
        get_comment_repository(),
    )


def get_move_stage_use_case() -> MoveStageUseCase:
    return MoveStageUseCase(
        get_lead_repository(),
        get_stage_event_repository(),
        get_comment_repository(),
    )


def get_list_stages_use_case() -> ListStagesUseCase:
    return ListStagesUseCase(
        get_lead_repository(),
        get_stage_event_repository(),
        get_comment_repository(),
    )


def reset_container() -> None:
    get_settings.cache_clear()
    _get_memo_repo.cache_clear()
    _get_onec_repo.cache_clear()
