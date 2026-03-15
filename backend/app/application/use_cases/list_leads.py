from app.application.dtos import LeadStageCommentInfo, LeadStageInfo, LeadWithStageInfo
from app.application.ports import CommentRepository, LeadRepository, StageEventRepository
from app.domain.entities import LeadComment
from app.domain.enums import LeadStage, SourcesCode, Users


class ListLeadsUseCase:
    def __init__(
        self,
        lead_repository: LeadRepository,
        stage_repository: StageEventRepository,
        comment_repository: CommentRepository,
    ):
        self._lead_repository = lead_repository
        self._stage_repository = stage_repository
        self._comment_repository = comment_repository

    async def execute(
        self,
        owner: Users | None,
        stage: LeadStage | None,
        source_code: SourcesCode | None,
        limit: int,
        offset: int,
    ) -> list[LeadWithStageInfo]:
        leads = await self._lead_repository.list(
            owner=owner,
            stage=stage,
            source_code=source_code,
            limit=limit,
            offset=offset,
        )

        result: list[LeadWithStageInfo] = []
        for lead in leads:
            events = await self._stage_repository.list_by_lead(lead.id)
            stage_info: list[LeadStageInfo] = []
            for event in events:
                comment: LeadComment | None = await self._comment_repository.get_by_stage_event_id(
                    event.id
                )
                comment_payload: list[LeadStageCommentInfo] = []
                if comment is not None:
                    comment_payload = [
                        LeadStageCommentInfo(author=comment.author, comment=comment.comment)
                    ]

                stage_info.append(
                    LeadStageInfo(
                        stage=event.stage,
                        entered_at=event.entered_at,
                        left_at=event.left_at,
                        approved=event.approved,
                        comment=comment_payload,
                    )
                )
            result.append(LeadWithStageInfo(lead=lead, stage_info=stage_info))

        return result
