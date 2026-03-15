from __future__ import annotations

import asyncio
import builtins
from dataclasses import replace
from datetime import datetime

from app.application.ports import CommentRepository, LeadRepository, StageEventRepository
from app.core.errors import ConflictError, LeadNotFoundError
from app.domain.entities import Lead, LeadComment, LeadStageEvent
from app.domain.enums import LeadStage, SourcesCode, Users


class MemoRepositories(LeadRepository, StageEventRepository, CommentRepository):
    def __init__(self) -> None:
        self._lock = asyncio.Lock()

        self._leads_by_id: dict[int, Lead] = {}
        self._lead_uid_to_id: dict[str, int] = {}

        self._stage_events_by_id: dict[int, LeadStageEvent] = {}
        self._stage_event_ids_by_lead: dict[int, list[int]] = {}

        self._comments_by_id: dict[int, LeadComment] = {}
        self._comments_by_stage_event_id: dict[int, LeadComment] = {}

        self._lead_id_seq = 0
        self._stage_event_id_seq = 0
        self._comment_id_seq = 0

    async def create(self, lead: Lead) -> Lead:
        async with self._lock:
            if lead.lead_uid in self._lead_uid_to_id:
                raise ConflictError(f"lead_uid '{lead.lead_uid}' already exists.")

            self._lead_id_seq += 1
            created = replace(lead, id=self._lead_id_seq)
            self._leads_by_id[created.id] = created
            self._lead_uid_to_id[created.lead_uid] = created.id
            self._stage_event_ids_by_lead.setdefault(created.id, [])
            return created

    async def get_by_uid(self, lead_uid: str) -> Lead | None:
        async with self._lock:
            lead_id = self._lead_uid_to_id.get(lead_uid)
            if lead_id is None:
                return None
            return self._leads_by_id.get(lead_id)

    async def delete_by_uid(self, lead_uid: str) -> None:
        async with self._lock:
            lead_id = self._lead_uid_to_id.pop(lead_uid, None)
            if lead_id is None:
                return

            self._leads_by_id.pop(lead_id, None)

            stage_event_ids = self._stage_event_ids_by_lead.pop(lead_id, [])
            for event_id in stage_event_ids:
                self._stage_events_by_id.pop(event_id, None)
                comment = self._comments_by_stage_event_id.pop(event_id, None)
                if comment is not None:
                    self._comments_by_id.pop(comment.id, None)

    async def list(
        self,
        owner: Users | None,
        stage: LeadStage | None,
        source_code: SourcesCode | None,
        limit: int,
        offset: int,
    ) -> list[Lead]:
        async with self._lock:
            items = list(self._leads_by_id.values())

            if owner is not None:
                items = [lead for lead in items if lead.owner == owner]
            if stage is not None:
                items = [lead for lead in items if lead.current_stage == stage]
            if source_code is not None:
                items = [lead for lead in items if lead.source_code == source_code]

            items.sort(key=lambda lead: lead.id)
            return items[offset : offset + limit]

    async def update_stage(self, lead_id: int, new_stage: LeadStage) -> Lead:
        async with self._lock:
            lead = self._leads_by_id.get(lead_id)
            if lead is None:
                raise LeadNotFoundError(f"Lead with id '{lead_id}' not found.")

            updated = replace(lead, current_stage=new_stage)
            self._leads_by_id[lead_id] = updated
            return updated

    async def create_stage_event(
        self,
        lead_id: int,
        stage: LeadStage,
        entered_at: datetime,
        approved: bool = True,
    ) -> LeadStageEvent:
        async with self._lock:
            if lead_id not in self._leads_by_id:
                raise LeadNotFoundError(f"Lead with id '{lead_id}' not found.")

            for event_id in self._stage_event_ids_by_lead.get(lead_id, []):
                event = self._stage_events_by_id[event_id]
                if event.stage == stage and event.entered_at == entered_at:
                    raise ConflictError(
                        "Stage event uniqueness violated for (lead_id, stage, entered_at)."
                    )

            self._stage_event_id_seq += 1
            created = LeadStageEvent(
                id=self._stage_event_id_seq,
                lead_id=lead_id,
                stage=stage,
                entered_at=entered_at,
                left_at=None,
                approved=approved,
            )
            self._stage_events_by_id[created.id] = created
            self._stage_event_ids_by_lead.setdefault(lead_id, []).append(created.id)
            return created

    async def close_open_event(self, lead_id: int, left_at: datetime) -> LeadStageEvent | None:
        async with self._lock:
            event_ids = self._stage_event_ids_by_lead.get(lead_id, [])
            open_events = [
                self._stage_events_by_id[event_id]
                for event_id in event_ids
                if self._stage_events_by_id[event_id].left_at is None
            ]
            if not open_events:
                return None

            latest = max(open_events, key=lambda event: (event.entered_at, event.id))
            updated = replace(latest, left_at=left_at)
            self._stage_events_by_id[updated.id] = updated
            return updated

    async def list_by_lead(self, lead_id: int) -> builtins.list[LeadStageEvent]:
        async with self._lock:
            event_ids = self._stage_event_ids_by_lead.get(lead_id, [])
            events = [self._stage_events_by_id[event_id] for event_id in event_ids]
            events.sort(key=lambda event: (event.entered_at, event.id))
            return events

    async def create_comment(
        self,
        stage_event_id: int,
        author: Users,
        comment: str | None,
        created_at: datetime,
    ) -> LeadComment:
        async with self._lock:
            if stage_event_id not in self._stage_events_by_id:
                raise LeadNotFoundError(f"Stage event '{stage_event_id}' not found.")

            if stage_event_id in self._comments_by_stage_event_id:
                raise ConflictError(
                    f"Comment already exists for stage_event_id '{stage_event_id}'."
                )

            self._comment_id_seq += 1
            created = LeadComment(
                id=self._comment_id_seq,
                stage_event_id=stage_event_id,
                author=author,
                comment=comment,
                created_at=created_at,
            )
            self._comments_by_id[created.id] = created
            self._comments_by_stage_event_id[stage_event_id] = created
            return created

    async def get_by_stage_event_id(self, stage_event_id: int) -> LeadComment | None:
        async with self._lock:
            return self._comments_by_stage_event_id.get(stage_event_id)
