from __future__ import annotations

from collections import defaultdict
from datetime import UTC, date, datetime

from fastapi import APIRouter, Depends, Query, Request

from app.application.ports import LeadRepository, StageEventRepository
from app.core.auth import ensure_permission, get_current_role
from app.core.deps import get_lead_repository, get_stage_event_repository
from app.domain.enums import LeadStage, SourcesCode, Users
from app.interface.api.schemas import (
    ConversionResponse,
    FunnelCountResponse,
    ReportsSummaryResponse,
    StageDurationResponse,
)
from app.interface.api.v1.helpers import collect_leads, within_date_range

router = APIRouter()


@router.get("/reports/summary", response_model=ReportsSummaryResponse)
async def get_reports_summary(
    request: Request,
    owner: Users | None = Query(default=None),
    source_code: SourcesCode | None = Query(default=None),
    date_from: date | None = Query(default=None),
    date_to: date | None = Query(default=None),
    lead_repo: LeadRepository = Depends(get_lead_repository),
    stage_repo: StageEventRepository = Depends(get_stage_event_repository),
) -> ReportsSummaryResponse:
    role = get_current_role(request)
    ensure_permission(role, "can_view_reports")

    leads = await collect_leads(
        lead_repo,
        owner=owner,
        stage=None,
        source_code=source_code,
    )

    current_stage_counts: dict[LeadStage, int] = defaultdict(int)
    reached_stage_counts: dict[LeadStage, int] = defaultdict(int)
    duration_accumulator: dict[LeadStage, list[float]] = defaultdict(list)

    now = datetime.now(UTC)
    kept = 0
    for lead in leads:
        events = await stage_repo.list_by_lead(lead.id)
        created_candidates = [event.entered_at for event in events if event.stage == LeadStage.new]
        created_at = min(created_candidates) if created_candidates else None
        if not within_date_range(created_at, date_from=date_from, date_to=date_to):
            continue

        kept += 1
        current_stage_counts[lead.current_stage] += 1
        seen_stages = {event.stage for event in events}
        for stage in seen_stages:
            reached_stage_counts[stage] += 1
        for event in events:
            duration = ((event.left_at or now) - event.entered_at).total_seconds()
            duration_accumulator[event.stage].append(duration)

    counts = [
        FunnelCountResponse(stage=stage, count=current_stage_counts.get(stage, 0))
        for stage in LeadStage
    ]
    conversions = []
    for from_stage, to_stage in (
        (LeadStage.new, LeadStage.qualified),
        (LeadStage.qualified, LeadStage.proposal),
        (LeadStage.proposal, LeadStage.won),
        (LeadStage.proposal, LeadStage.lost),
    ):
        from_count = reached_stage_counts.get(from_stage, 0)
        to_count = reached_stage_counts.get(to_stage, 0)
        rate = round((to_count / from_count) * 100, 2) if from_count else 0.0
        conversions.append(
            ConversionResponse(
                from_stage=from_stage,
                to_stage=to_stage,
                from_count=from_count,
                to_count=to_count,
                rate=rate,
            )
        )

    average_stage_durations = []
    for stage in LeadStage:
        durations = duration_accumulator.get(stage, [])
        average_seconds = round(sum(durations) / len(durations), 2) if durations else 0.0
        average_stage_durations.append(
            StageDurationResponse(
                stage=stage,
                average_seconds=average_seconds,
                average_hours=round(average_seconds / 3600, 2) if average_seconds else 0.0,
            )
        )

    return ReportsSummaryResponse(
        total_leads=kept,
        counts=counts,
        conversions=conversions,
        average_stage_durations=average_stage_durations,
    )
