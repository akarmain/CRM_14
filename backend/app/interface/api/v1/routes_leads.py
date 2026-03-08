from fastapi import APIRouter, Depends, Query, status

from app.application.use_cases.create_lead import CreateLeadUseCase
from app.application.use_cases.get_lead import GetLeadUseCase
from app.application.use_cases.list_leads import ListLeadsUseCase
from app.application.use_cases.list_stages import ListStagesUseCase
from app.application.use_cases.move_stage import MoveStageUseCase
from app.core.deps import (
    get_create_lead_use_case,
    get_get_lead_use_case,
    get_list_leads_use_case,
    get_list_stages_use_case,
    get_move_stage_use_case,
)
from app.domain.enums import LeadStage, SourcesCode, Users
from app.interface.api.schemas import (
    LeadCreateRequest,
    LeadResponse,
    MoveStageRequest,
    MoveStageResponse,
    NewLeadRequest,
    StageCommentResponse,
    StageEventResponse,
)

router = APIRouter()


@router.post("/leads", response_model=LeadResponse, status_code=status.HTTP_201_CREATED)
async def create_lead(
    payload: LeadCreateRequest,
    use_case: CreateLeadUseCase = Depends(get_create_lead_use_case),
) -> LeadResponse:
    lead = await use_case.execute(
        source_code=payload.source_code,
        owner=payload.owner,
        title=payload.title,
        notes=payload.notes,
        lead_uid=payload.lead_uid,
    )
    return LeadResponse.model_validate(lead)


@router.post("/new-lead", response_model=LeadResponse, status_code=status.HTTP_201_CREATED)
async def create_new_lead(
    payload: NewLeadRequest,
    use_case: CreateLeadUseCase = Depends(get_create_lead_use_case),
) -> LeadResponse:
    lead = await use_case.execute(
        source_code=SourcesCode.other,
        owner=payload.owner,
        title=payload.title,
        notes=payload.notes,
        lead_uid=None,
    )
    return LeadResponse.model_validate(lead)


@router.get("/leads/{lead_uid}", response_model=LeadResponse)
async def get_lead(
    lead_uid: str,
    use_case: GetLeadUseCase = Depends(get_get_lead_use_case),
) -> LeadResponse:
    lead = await use_case.execute(lead_uid)
    return LeadResponse.model_validate(lead)


@router.get("/leads", response_model=list[LeadResponse])
async def list_leads(
    owner: Users | None = Query(default=None),
    stage: LeadStage | None = Query(default=None),
    source_code: SourcesCode | None = Query(default=None),
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    use_case: ListLeadsUseCase = Depends(get_list_leads_use_case),
) -> list[LeadResponse]:
    leads = await use_case.execute(
        owner=owner,
        stage=stage,
        source_code=source_code,
        limit=limit,
        offset=offset,
    )
    return [LeadResponse.model_validate(item) for item in leads]


@router.post("/leads/{lead_uid}/stage", response_model=MoveStageResponse)
async def move_stage(
    lead_uid: str,
    payload: MoveStageRequest,
    use_case: MoveStageUseCase = Depends(get_move_stage_use_case),
) -> MoveStageResponse:
    result = await use_case.execute(
        lead_uid=lead_uid,
        stage=payload.stage,
        author=payload.author,
        comment=payload.comment,
    )

    comment_payload = None
    if result.comment is not None:
        comment_payload = StageCommentResponse.model_validate(result.comment)

    return MoveStageResponse(
        lead=LeadResponse.model_validate(result.lead),
        stage_event=StageEventResponse(
            id=result.stage_event.id,
            stage=result.stage_event.stage,
            entered_at=result.stage_event.entered_at,
            left_at=result.stage_event.left_at,
            approved=result.stage_event.approved,
            comment=comment_payload,
        ),
    )


@router.get("/leads/{lead_uid}/stages", response_model=list[StageEventResponse])
async def list_stages(
    lead_uid: str,
    use_case: ListStagesUseCase = Depends(get_list_stages_use_case),
) -> list[StageEventResponse]:
    stages = await use_case.execute(lead_uid)
    response: list[StageEventResponse] = []
    for item in stages:
        comment_payload = None
        if item.comment is not None:
            comment_payload = StageCommentResponse.model_validate(item.comment)

        response.append(
            StageEventResponse(
                id=item.stage_event.id,
                stage=item.stage_event.stage,
                entered_at=item.stage_event.entered_at,
                left_at=item.stage_event.left_at,
                approved=item.stage_event.approved,
                comment=comment_payload,
            )
        )

    return response
