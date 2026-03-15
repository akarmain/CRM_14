from app.application.dtos import LeadStageCommentInfo, LeadStageInfo, LeadWithStageInfo
from app.application.ports import CommentRepository, LeadRepository, StageEventRepository
from app.core.errors import LeadNotFoundError
from app.domain.entities import LeadComment


class GetLeadUseCase:
    def __init__(
        self,
        lead_repository: LeadRepository,
        stage_repository: StageEventRepository,
        comment_repository: CommentRepository,
    ):
        self._lead_repository = lead_repository
        self._stage_repository = stage_repository
        self._comment_repository = comment_repository

    async def execute(self, lead_uid: str) -> LeadWithStageInfo:
        lead = await self._lead_repository.get_by_uid(lead_uid)
        if lead is None:
            raise LeadNotFoundError(f"Lead with uid '{lead_uid}' not found.")

        events = await self._stage_repository.list_by_lead(lead.id)
        stage_info: list[LeadStageInfo] = []
        for event in events:
            comment: LeadComment | None = await self._comment_repository.get_by_stage_event_id(
                event.id
            )
            comment_payload: list[LeadStageCommentInfo] = []
            if comment is not None:
                comment_payload = [LeadStageCommentInfo(author=comment.author, comment=comment.comment)]

            stage_info.append(
                LeadStageInfo(
                    stage=event.stage,
                    entered_at=event.entered_at,
                    left_at=event.left_at,
                    approved=event.approved,
                    comment=comment_payload,
                )
            )

        return LeadWithStageInfo(lead=lead, stage_info=stage_info)
