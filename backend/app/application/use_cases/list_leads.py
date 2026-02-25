from app.application.ports import LeadRepository
from app.domain.entities import Lead
from app.domain.enums import LeadStage, SourcesCode, Users


class ListLeadsUseCase:
    def __init__(self, lead_repository: LeadRepository):
        self._lead_repository = lead_repository

    async def execute(
        self,
        owner: Users | None,
        stage: LeadStage | None,
        source_code: SourcesCode | None,
        limit: int,
        offset: int,
    ) -> list[Lead]:
        return await self._lead_repository.list(
            owner=owner,
            stage=stage,
            source_code=source_code,
            limit=limit,
            offset=offset,
        )
