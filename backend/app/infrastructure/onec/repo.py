from __future__ import annotations

import asyncio
import builtins
import json
import time
import zlib
from dataclasses import replace
from datetime import UTC, datetime
from typing import Any

import requests

from app.application.ports import (
    AuditLogRepository,
    CommentRepository,
    LeadRepository,
    ReturnRequestRepository,
    StageEventRepository,
)
from app.core.config import get_settings
from app.core.errors import AppError, ConflictError, LeadNotFoundError
from app.domain.entities import AuditLogEntry, Lead, LeadComment, LeadStageEvent, StageReturnRequest
from app.domain.enums import LeadStage, ReturnRequestStatus, SourcesCode, Users

OWNER_TO_1C: dict[Users, str] = {
    Users.manager_1: "Иванов И.И.",
    Users.manager_2: "Петров П.П.",
    Users.sales_head: "Руководитель ОП",
}
OWNER_FROM_1C: dict[str, Users] = {
    "иванов и.и.": Users.manager_1,
    "петров п.п.": Users.manager_2,
    "руководитель оп": Users.sales_head,
}
SOURCE_TO_1C: dict[SourcesCode, str] = {
    SourcesCode.advertisement: "advertising",
    SourcesCode.website: "website",
    SourcesCode.recommendation: "recommendation",
    SourcesCode.event: "event",
    SourcesCode.other: "other",
}
SOURCE_FROM_1C: dict[str, SourcesCode] = {
    "advertising": SourcesCode.advertisement,
    "advertisement": SourcesCode.advertisement,
    "website": SourcesCode.website,
    "recommendation": SourcesCode.recommendation,
    "event": SourcesCode.event,
    "other": SourcesCode.other,
}


class OneCRepository(
    LeadRepository,
    StageEventRepository,
    CommentRepository,
    ReturnRequestRepository,
    AuditLogRepository,
):
    def __init__(self) -> None:
        self._lock = asyncio.Lock()
        self._settings = get_settings()

        self._created_at_by_lead_id: dict[int, datetime] = {}
        self._known_leads_by_id: dict[int, Lead] = {}

        self._stage_events_by_id: dict[int, LeadStageEvent] = {}
        self._stage_event_ids_by_lead: dict[int, list[int]] = {}
        self._comments_by_id: dict[int, LeadComment] = {}
        self._comments_by_stage_event_id: dict[int, LeadComment] = {}
        self._return_requests_by_id: dict[int, StageReturnRequest] = {}
        self._return_request_ids_by_lead: dict[int, list[int]] = {}
        self._audit_entries_by_id: dict[int, AuditLogEntry] = {}

        self._stage_event_id_seq = 0
        self._comment_id_seq = 0
        self._return_request_id_seq = 0
        self._audit_entry_id_seq = 0

    def _endpoint(self, path: str) -> str:
        base = self._settings.onec_base_url.rstrip("/")
        suffix = path if path.startswith("/") else f"/{path}"
        return f"{base}{suffix}"

    def _safe_int(self, value: Any, fallback_key: str) -> int:
        try:
            parsed = int(value)
            if parsed > 0:
                return parsed
        except (TypeError, ValueError):
            pass
        return zlib.crc32(fallback_key.encode("utf-8")) & 0x7FFFFFFF

    def _parse_dt(self, value: Any) -> datetime:
        if isinstance(value, str) and value:
            trimmed = value.strip()
            try:
                dt = datetime.fromisoformat(trimmed.replace("Z", "+00:00"))
                return dt if dt.tzinfo is not None else dt.replace(tzinfo=UTC)
            except ValueError:
                pass
            try:
                return datetime.strptime(trimmed, "%Y-%m-%d").replace(tzinfo=UTC)
            except ValueError:
                pass
        return datetime.now(UTC)

    def _parse_owner(self, value: Any) -> Users:
        if isinstance(value, str):
            normalized = value.strip().lower()
            if normalized in OWNER_FROM_1C:
                return OWNER_FROM_1C[normalized]
            for enum_value in Users:
                if normalized == enum_value.value:
                    return enum_value
        return Users.manager_1

    def _parse_source(self, value: Any) -> SourcesCode:
        if isinstance(value, str):
            return SOURCE_FROM_1C.get(value.strip().lower(), SourcesCode.other)
        return SourcesCode.other

    def _parse_stage(self, value: Any) -> LeadStage:
        if isinstance(value, str):
            normalized = value.strip().lower()
            for enum_value in LeadStage:
                if normalized == enum_value.value:
                    return enum_value
        return LeadStage.new

    def _to_remote_item(self, lead: Lead) -> dict[str, Any]:
        created_at = self._created_at_by_lead_id.get(lead.id, datetime.now(UTC))
        return {
            "id": lead.id,
            "lead_uid": lead.lead_uid,
            "source": SOURCE_TO_1C.get(lead.source_code, "other"),
            "stage": lead.current_stage.value,
            "owner": OWNER_TO_1C.get(lead.owner, OWNER_TO_1C[Users.manager_1]),
            "created_at": created_at.date().isoformat(),
            "title": lead.title,
            "notes": lead.notes,
        }

    def _sync_from_rows(self, rows: list[dict[str, Any]]) -> list[Lead]:
        parsed: list[Lead] = []
        for row in rows:
            lead_uid = str(row.get("lead_uid", "")).strip()
            if not lead_uid:
                continue
            lead_id = self._safe_int(row.get("id"), fallback_key=lead_uid)
            lead = Lead(
                id=lead_id,
                lead_uid=lead_uid,
                source_code=self._parse_source(row.get("source")),
                current_stage=self._parse_stage(row.get("stage")),
                owner=self._parse_owner(row.get("owner")),
                title=row.get("title"),
                notes=row.get("notes"),
            )
            parsed.append(lead)
            self._known_leads_by_id[lead.id] = lead
            self._created_at_by_lead_id[lead.id] = self._parse_dt(row.get("created_at"))
        return parsed

    async def _fetch_all(self) -> list[Lead]:
        def _request() -> list[Lead]:
            last_error: Exception | None = None
            attempts = max(1, int(self._settings.onec_max_retries))
            backoff = max(0.0, float(self._settings.onec_retry_backoff_seconds))

            for attempt in range(1, attempts + 1):
                try:
                    response = requests.get(
                        self._endpoint("/leads"),
                        timeout=self._settings.onec_timeout_seconds,
                    )
                    if response.status_code >= 400:
                        raise AppError(f"1C returned HTTP {response.status_code}: {response.text[:200]}")

                    payload = response.json()
                    if not isinstance(payload, list):
                        raise AppError("Unexpected 1C payload format for /leads.")
                    rows = [item for item in payload if isinstance(item, dict)]
                    return self._sync_from_rows(rows)
                except (requests.RequestException, json.JSONDecodeError, AppError) as exc:
                    last_error = exc
                    if attempt < attempts:
                        time.sleep(backoff * attempt)

            # Read fallback: keep API responsive on short 1C outages.
            if self._known_leads_by_id:
                items = list(self._known_leads_by_id.values())
                items.sort(key=lambda lead: lead.id)
                return items

            message = str(last_error) if last_error is not None else "unknown 1C error"
            raise AppError(f"1C connection error: {message}")

        return await asyncio.to_thread(_request)

    async def _push_single(self, lead: Lead) -> None:
        payload = [self._to_remote_item(lead)]

        def _request() -> None:
            last_error: Exception | None = None
            attempts = max(1, int(self._settings.onec_max_retries))
            backoff = max(0.0, float(self._settings.onec_retry_backoff_seconds))

            for attempt in range(1, attempts + 1):
                try:
                    response = requests.post(
                        self._endpoint("/leads"),
                        json=payload,
                        timeout=self._settings.onec_timeout_seconds,
                    )
                    if response.status_code >= 400:
                        raise AppError(f"1C returned HTTP {response.status_code}: {response.text[:200]}")

                    try:
                        body = response.json()
                    except json.JSONDecodeError:
                        body = None
                    if isinstance(body, list):
                        for item in body:
                            if isinstance(item, dict) and item.get("error"):
                                message = str(item.get("error"))
                                if "уже существует" in message.lower():
                                    raise ConflictError(message)
                                raise AppError(f"1C rejected lead '{lead.lead_uid}': {message}")
                    return
                except (requests.RequestException, AppError) as exc:
                    last_error = exc
                    if attempt < attempts:
                        time.sleep(backoff * attempt)
            message = str(last_error) if last_error is not None else "unknown 1C write error"
            raise AppError(f"1C write error: {message}")

        await asyncio.to_thread(_request)

    async def _resolve_lead(self, lead_id: int) -> Lead:
        lead = await self.get_by_id(lead_id)
        if lead is None:
            raise LeadNotFoundError(f"Lead with id '{lead_id}' not found.")
        return lead

    async def _ensure_synthetic_stage(self, lead: Lead) -> None:
        async with self._lock:
            ids = self._stage_event_ids_by_lead.get(lead.id, [])
            if ids:
                return
            self._stage_event_id_seq += 1
            created = LeadStageEvent(
                id=self._stage_event_id_seq,
                lead_id=lead.id,
                stage=lead.current_stage,
                entered_at=self._created_at_by_lead_id.get(lead.id, datetime.now(UTC)),
                left_at=None,
                approved=True,
            )
            self._stage_events_by_id[created.id] = created
            self._stage_event_ids_by_lead.setdefault(lead.id, []).append(created.id)

    async def create(self, lead: Lead) -> Lead:
        existing = await self.get_by_uid(lead.lead_uid)
        if existing is not None:
            raise ConflictError(f"lead_uid '{lead.lead_uid}' already exists.")

        lead_id = self._safe_int(lead.id, lead.lead_uid)
        if lead_id == 0:
            lead_id = zlib.crc32(lead.lead_uid.encode("utf-8")) & 0x7FFFFFFF
        created = replace(lead, id=lead_id)
        self._created_at_by_lead_id[created.id] = datetime.now(UTC)
        await self._push_single(created)

        async with self._lock:
            self._known_leads_by_id[created.id] = created
        return created

    async def get_by_uid(self, lead_uid: str) -> Lead | None:
        leads = await self._fetch_all()
        for item in leads:
            if item.lead_uid == lead_uid:
                await self._ensure_synthetic_stage(item)
                return item
        return None

    async def get_by_id(self, lead_id: int) -> Lead | None:
        leads = await self._fetch_all()
        for item in leads:
            if item.id == lead_id:
                await self._ensure_synthetic_stage(item)
                return item
        return None

    async def delete_by_uid(self, lead_uid: str) -> None:
        raise AppError("Deleting leads is not supported by temporary 1C adapter.")

    async def list(
        self,
        owner: Users | None,
        stage: LeadStage | None,
        source_code: SourcesCode | None,
        limit: int,
        offset: int,
    ) -> list[Lead]:
        items = await self._fetch_all()
        if owner is not None:
            items = [lead for lead in items if lead.owner == owner]
        if stage is not None:
            items = [lead for lead in items if lead.current_stage == stage]
        if source_code is not None:
            items = [lead for lead in items if lead.source_code == source_code]
        items.sort(key=lambda lead: lead.id)
        for item in items:
            await self._ensure_synthetic_stage(item)
        return items[offset : offset + limit]

    async def update_stage(self, lead_id: int, new_stage: LeadStage) -> Lead:
        lead = await self._resolve_lead(lead_id)
        updated = replace(lead, current_stage=new_stage)
        await self._push_single(updated)
        async with self._lock:
            self._known_leads_by_id[lead_id] = updated
        return updated

    async def update_details(
        self,
        lead_id: int,
        owner: Users,
        title: str | None,
        notes: str | None,
    ) -> Lead:
        lead = await self._resolve_lead(lead_id)
        updated = replace(lead, owner=owner, title=title, notes=notes)
        await self._push_single(updated)
        async with self._lock:
            self._known_leads_by_id[lead_id] = updated
        return updated

    async def create_stage_event(
        self,
        lead_id: int,
        stage: LeadStage,
        entered_at: datetime,
        approved: bool = True,
    ) -> LeadStageEvent:
        _ = await self._resolve_lead(lead_id)
        async with self._lock:
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
        lead = await self.get_by_id(lead_id)
        if lead is None:
            return []
        await self._ensure_synthetic_stage(lead)
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

    async def create_return_request(self, request: StageReturnRequest) -> StageReturnRequest:
        async with self._lock:
            self._return_request_id_seq += 1
            created = replace(request, id=self._return_request_id_seq)
            self._return_requests_by_id[created.id] = created
            self._return_request_ids_by_lead.setdefault(created.lead_id, []).append(created.id)
            return created

    async def get_return_request_by_id(self, request_id: int) -> StageReturnRequest | None:
        async with self._lock:
            return self._return_requests_by_id.get(request_id)

    async def list_return_requests(
        self,
        *,
        status: ReturnRequestStatus | None,
        lead_id: int | None,
    ) -> list[StageReturnRequest]:
        async with self._lock:
            items = list(self._return_requests_by_id.values())
            if status is not None:
                items = [item for item in items if item.status == status]
            if lead_id is not None:
                items = [item for item in items if item.lead_id == lead_id]
            items.sort(key=lambda item: (item.requested_at, item.id), reverse=True)
            return items

    async def list_return_requests_by_lead(self, lead_id: int) -> list[StageReturnRequest]:
        async with self._lock:
            request_ids = self._return_request_ids_by_lead.get(lead_id, [])
            items = [self._return_requests_by_id[request_id] for request_id in request_ids]
            items.sort(key=lambda item: (item.requested_at, item.id), reverse=True)
            return items

    async def update_review(
        self,
        request_id: int,
        *,
        status: ReturnRequestStatus,
        reviewed_by: Users,
        review_comment: str,
        reviewed_at: datetime,
    ) -> StageReturnRequest:
        async with self._lock:
            request = self._return_requests_by_id.get(request_id)
            if request is None:
                raise LeadNotFoundError(f"Return request '{request_id}' not found.")
            updated = replace(
                request,
                status=status,
                reviewed_by=reviewed_by,
                review_comment=review_comment,
                reviewed_at=reviewed_at,
            )
            self._return_requests_by_id[request_id] = updated
            return updated

    async def create_audit_entry(self, entry: AuditLogEntry) -> AuditLogEntry:
        async with self._lock:
            self._audit_entry_id_seq += 1
            created = replace(entry, id=self._audit_entry_id_seq)
            self._audit_entries_by_id[created.id] = created
            return created

    async def list_audit_entries(
        self,
        *,
        lead_id: int | None,
        limit: int,
        offset: int,
    ) -> list[AuditLogEntry]:
        async with self._lock:
            items = list(self._audit_entries_by_id.values())
            if lead_id is not None:
                items = [item for item in items if item.lead_id == lead_id]
            items.sort(key=lambda item: (item.created_at, item.id), reverse=True)
            return items[offset : offset + limit]
