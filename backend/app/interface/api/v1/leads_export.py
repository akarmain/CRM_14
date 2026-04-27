from __future__ import annotations

import csv
from collections import defaultdict
from datetime import UTC, datetime
from io import BytesIO, StringIO

from xlsxwriter import Workbook

from app.application.dtos import LeadExportRow
from app.domain.entities import LeadStageEvent
from app.domain.enums import LeadStage, Users

EXPORT_COLUMNS: tuple[str, ...] = (
    "lead_uid",
    "title",
    "notes",
    "owner",
    "stage",
    "entered_at",
    "source_code",
)

STAGE_ORDER: tuple[LeadStage, ...] = (
    LeadStage.new,
    LeadStage.qualified,
    LeadStage.proposal,
    LeadStage.won,
    LeadStage.lost,
)

ACTIVE_STAGES: set[LeadStage] = {LeadStage.new, LeadStage.qualified, LeadStage.proposal}


def render_leads_csv(rows: list[LeadExportRow]) -> bytes:
    stream = StringIO()
    writer = csv.writer(stream, delimiter=";", lineterminator="\n")
    writer.writerow(EXPORT_COLUMNS)
    for row in rows:
        writer.writerow(_row_to_values(row))
    return stream.getvalue().encode("utf-8-sig")


def render_leads_xlsx(
    rows: list[LeadExportRow],
    *,
    stage_events_by_lead_uid: dict[str, list[LeadStageEvent]],
    export_time_utc: datetime,
    owner_filter: Users | None,
) -> bytes:
    metrics = _build_metrics(
        rows=rows,
        stage_events_by_lead_uid=stage_events_by_lead_uid,
        export_time_utc=export_time_utc,
    )

    out = BytesIO()
    with Workbook(out, {"in_memory": True}) as workbook:
        analytics_sheet = workbook.add_worksheet("Аналитика")
        data_sheet = workbook.add_worksheet("Данные")
        analytics_sheet.activate()

        header_fmt = workbook.add_format({"bold": True, "bg_color": "#D9E1F2", "border": 1})
        section_fmt = workbook.add_format({"bold": True, "font_size": 12})
        text_fmt = workbook.add_format({"border": 1})
        int_fmt = workbook.add_format({"num_format": "0", "border": 1})
        pct_fmt = workbook.add_format({"num_format": "0.00%", "border": 1})
        days_fmt = workbook.add_format({"num_format": "0.00", "border": 1})
        datetime_fmt = workbook.add_format({"num_format": "yyyy-mm-dd hh:mm:ss", "border": 1})

        _write_data_sheet(data_sheet, rows, header_fmt, text_fmt, datetime_fmt)
        _write_analytics_sheet(
            sheet=analytics_sheet,
            workbook=workbook,
            metrics=metrics,
            owner_filter=owner_filter,
            export_time_utc=export_time_utc,
            section_fmt=section_fmt,
            header_fmt=header_fmt,
            text_fmt=text_fmt,
            int_fmt=int_fmt,
            pct_fmt=pct_fmt,
            days_fmt=days_fmt,
            datetime_fmt=datetime_fmt,
        )

    return out.getvalue()


def _write_data_sheet(data_sheet, rows, header_fmt, text_fmt, datetime_fmt) -> None:
    data_sheet.write_row(0, 0, EXPORT_COLUMNS, header_fmt)

    for index, row in enumerate(rows, start=1):
        data_sheet.write_string(index, 0, row.lead_uid, text_fmt)
        data_sheet.write_string(index, 1, row.title or "", text_fmt)
        data_sheet.write_string(index, 2, row.notes or "", text_fmt)
        data_sheet.write_string(index, 3, row.owner.value, text_fmt)
        data_sheet.write_string(index, 4, row.stage.value, text_fmt)
        if row.entered_at is None:
            data_sheet.write_blank(index, 5, None, text_fmt)
        else:
            naive_dt = row.entered_at.astimezone(UTC).replace(tzinfo=None)
            data_sheet.write_datetime(index, 5, naive_dt, datetime_fmt)
        data_sheet.write_string(index, 6, row.source_code.value, text_fmt)

    last_row = max(len(rows), 1)
    data_sheet.autofilter(0, 0, last_row, len(EXPORT_COLUMNS) - 1)
    data_sheet.freeze_panes(1, 0)
    data_sheet.set_column(0, 0, 18)
    data_sheet.set_column(1, 2, 24)
    data_sheet.set_column(3, 4, 16)
    data_sheet.set_column(5, 5, 22)
    data_sheet.set_column(6, 6, 16)


def _write_analytics_sheet(
    *,
    sheet,
    workbook: Workbook,
    metrics: dict,
    owner_filter: Users | None,
    export_time_utc: datetime,
    section_fmt,
    header_fmt,
    text_fmt,
    int_fmt,
    pct_fmt,
    days_fmt,
    datetime_fmt,
) -> None:
    sheet.set_column(0, 0, 42)
    sheet.set_column(1, 1, 18)
    sheet.set_column(3, 7, 18)
    sheet.set_column(9, 14, 14)

    sheet.write(0, 0, "Параметры отчёта", section_fmt)
    sheet.write(1, 0, "Сформирован (UTC)", text_fmt)
    sheet.write_datetime(1, 1, export_time_utc.replace(tzinfo=None), datetime_fmt)
    sheet.write(2, 0, "Фильтр owner", text_fmt)
    sheet.write(2, 1, owner_filter.value if owner_filter else "all", text_fmt)

    summary_row = 5
    sheet.write(summary_row, 0, "Метрики", section_fmt)
    summary_metrics = [
        ("Количество лидов всего", metrics["n_total"], int_fmt),
        ("Лидов на стадии new", metrics["stage_counts"][LeadStage.new], int_fmt),
        ("Лидов на стадии qualified", metrics["stage_counts"][LeadStage.qualified], int_fmt),
        ("Лидов на стадии proposal", metrics["stage_counts"][LeadStage.proposal], int_fmt),
        ("Лидов на стадии won", metrics["stage_counts"][LeadStage.won], int_fmt),
        ("Лидов на стадии lost", metrics["stage_counts"][LeadStage.lost], int_fmt),
        ("Конверсия new → qualified", metrics["conv_new_to_qualified"], pct_fmt),
        ("Конверсия qualified → proposal", metrics["conv_qualified_to_proposal"], pct_fmt),
        ("Конверсия proposal → won", metrics["conv_proposal_to_won"], pct_fmt),
        ("Общая конверсия в won", metrics["conv_total_to_won"], pct_fmt),
        ("Доля lost", metrics["lost_share"], pct_fmt),
        ("Неподтверждённые переходы", metrics["unapproved_count"], int_fmt),
        ("Зависшие лиды (>3 дней)", metrics["stuck_count"], int_fmt),
    ]
    sheet.write_row(summary_row + 1, 0, ["Метрика", "Значение"], header_fmt)
    for idx, (label, value, value_fmt) in enumerate(summary_metrics, start=summary_row + 2):
        sheet.write(idx, 0, label, text_fmt)
        if value_fmt is pct_fmt:
            sheet.write_number(idx, 1, float(value), value_fmt)
        else:
            sheet.write_number(idx, 1, float(value), value_fmt)

    stage_table_start = summary_row + 2
    for offset, stage in enumerate(STAGE_ORDER):
        row_idx = stage_table_start + offset
        sheet.write(row_idx, 3, stage.value, text_fmt)
        sheet.write_number(row_idx, 4, metrics["stage_counts"][stage], int_fmt)

    sheet.write(summary_row, 3, "Воронка (данные)", section_fmt)
    sheet.write_row(summary_row + 1, 3, ["Стадия", "Лидов"], header_fmt)

    sheet.write(0, 6, "Средняя длительность стадий (дни)", section_fmt)
    sheet.write_row(1, 6, ["Стадия", "Дни"], header_fmt)
    for offset, stage in enumerate(STAGE_ORDER):
        row_idx = 2 + offset
        sheet.write(row_idx, 6, stage.value, text_fmt)
        sheet.write_number(row_idx, 7, metrics["avg_duration_by_stage"][stage], days_fmt)

    source_rows = metrics["source_conversion_rows"]
    source_start_row = 20
    sheet.write(source_start_row, 0, "Конверсия по источникам", section_fmt)
    sheet.write_row(source_start_row + 1, 0, ["Источник", "Всего", "Won", "% Won"], header_fmt)
    for offset, item in enumerate(source_rows, start=source_start_row + 2):
        sheet.write(offset, 0, item["source"], text_fmt)
        sheet.write_number(offset, 1, item["total"], int_fmt)
        sheet.write_number(offset, 2, item["won"], int_fmt)
        sheet.write_number(offset, 3, item["rate"], pct_fmt)

    owner_rows = metrics["owner_rows"]
    owner_start_col = 5
    owner_start_row = 20
    sheet.write(owner_start_row, owner_start_col, "Лиды по менеджерам", section_fmt)
    sheet.write_row(owner_start_row + 1, owner_start_col, ["Менеджер", "Всего лидов"], header_fmt)
    for offset, item in enumerate(owner_rows, start=owner_start_row + 2):
        sheet.write(offset, owner_start_col, item["owner"], text_fmt)
        sheet.write_number(offset, owner_start_col + 1, item["total"], int_fmt)

    avg_owner_rows = metrics["avg_duration_by_owner_rows"]
    avg_owner_start_col = 8
    avg_owner_start_row = 20
    sheet.write(avg_owner_start_row, avg_owner_start_col, "Средняя длительность по менеджеру (дни)", section_fmt)
    sheet.write_row(avg_owner_start_row + 1, avg_owner_start_col, ["Менеджер", "Дни"], header_fmt)
    for offset, item in enumerate(avg_owner_rows, start=avg_owner_start_row + 2):
        sheet.write(offset, avg_owner_start_col, item["owner"], text_fmt)
        sheet.write_number(offset, avg_owner_start_col + 1, item["days"], days_fmt)

    active_rows = metrics["active_load_rows"]
    active_start_col = 11
    active_start_row = 20
    sheet.write(active_start_row, active_start_col, "Нагрузка менеджеров (активные лиды)", section_fmt)
    sheet.write_row(
        active_start_row + 1,
        active_start_col,
        ["Менеджер", "new", "qualified", "proposal", "Активных"],
        header_fmt,
    )
    for offset, item in enumerate(active_rows, start=active_start_row + 2):
        sheet.write(offset, active_start_col, item["owner"], text_fmt)
        sheet.write_number(offset, active_start_col + 1, item["new"], int_fmt)
        sheet.write_number(offset, active_start_col + 2, item["qualified"], int_fmt)
        sheet.write_number(offset, active_start_col + 3, item["proposal"], int_fmt)
        sheet.write_number(offset, active_start_col + 4, item["active_total"], int_fmt)

    _insert_charts(
        sheet=sheet,
        workbook=workbook,
        stage_table_start=stage_table_start,
        source_start_row=source_start_row,
        source_len=len(source_rows),
        active_start_row=active_start_row,
        active_len=len(active_rows),
    )


def _insert_charts(*, sheet, workbook: Workbook, stage_table_start: int, source_start_row: int, source_len: int, active_start_row: int, active_len: int) -> None:
    funnel_chart = workbook.add_chart({"type": "bar"})
    funnel_chart.add_series(
        {
            "name": "Воронка продаж",
            "categories": ["Аналитика", stage_table_start, 3, stage_table_start + len(STAGE_ORDER) - 1, 3],
            "values": ["Аналитика", stage_table_start, 4, stage_table_start + len(STAGE_ORDER) - 1, 4],
            "data_labels": {"value": True},
        }
    )
    funnel_chart.set_title({"name": "Воронка продаж"})
    funnel_chart.set_x_axis({"name": "Количество лидов"})
    funnel_chart.set_y_axis({"name": "Стадия"})
    sheet.insert_chart("A30", funnel_chart, {"x_scale": 1.2, "y_scale": 1.2})

    duration_chart = workbook.add_chart({"type": "column"})
    duration_chart.add_series(
        {
            "name": "Средняя длительность стадии",
            "categories": ["Аналитика", 2, 6, 2 + len(STAGE_ORDER) - 1, 6],
            "values": ["Аналитика", 2, 7, 2 + len(STAGE_ORDER) - 1, 7],
            "data_labels": {"value": True},
        }
    )
    duration_chart.set_title({"name": "Средняя длительность стадий"})
    duration_chart.set_x_axis({"name": "Стадия"})
    duration_chart.set_y_axis({"name": "Дни"})
    sheet.insert_chart("H30", duration_chart, {"x_scale": 1.2, "y_scale": 1.2})

    source_chart = workbook.add_chart({"type": "column"})
    source_chart.add_series(
        {
            "name": "% won по источникам",
            "categories": ["Аналитика", source_start_row + 2, 0, source_start_row + 1 + source_len, 0],
            "values": ["Аналитика", source_start_row + 2, 3, source_start_row + 1 + source_len, 3],
            "data_labels": {"value": True, "num_format": "0.00%"},
        }
    )
    source_chart.set_title({"name": "Конверсия по источникам"})
    source_chart.set_x_axis({"name": "Источник"})
    source_chart.set_y_axis({"name": "% won", "num_format": "0.00%"})
    sheet.insert_chart("A48", source_chart, {"x_scale": 1.2, "y_scale": 1.2})

    active_chart = workbook.add_chart({"type": "column", "subtype": "stacked"})
    for col, stage_name in ((12, "new"), (13, "qualified"), (14, "proposal")):
        active_chart.add_series(
            {
                "name": stage_name,
                "categories": ["Аналитика", active_start_row + 2, 11, active_start_row + 1 + active_len, 11],
                "values": ["Аналитика", active_start_row + 2, col, active_start_row + 1 + active_len, col],
            }
        )
    active_chart.set_title({"name": "Нагрузка по менеджерам"})
    active_chart.set_x_axis({"name": "Менеджер"})
    active_chart.set_y_axis({"name": "Активные лиды"})
    sheet.insert_chart("H48", active_chart, {"x_scale": 1.2, "y_scale": 1.2})


def _build_metrics(
    *,
    rows: list[LeadExportRow],
    stage_events_by_lead_uid: dict[str, list[LeadStageEvent]],
    export_time_utc: datetime,
) -> dict:
    stage_counts: dict[LeadStage, int] = {stage: 0 for stage in STAGE_ORDER}
    source_totals: dict[str, int] = defaultdict(int)
    source_won: dict[str, int] = defaultdict(int)
    owner_totals: dict[str, int] = defaultdict(int)
    active_by_owner: dict[str, dict[LeadStage, int]] = defaultdict(lambda: {LeadStage.new: 0, LeadStage.qualified: 0, LeadStage.proposal: 0})

    duration_by_stage: dict[LeadStage, list[float]] = defaultdict(list)
    duration_by_owner: dict[str, list[float]] = defaultdict(list)

    unapproved_count = 0
    stuck_count = 0

    for row in rows:
        stage_counts[row.stage] = stage_counts.get(row.stage, 0) + 1
        source_key = row.source_code.value
        owner_key = row.owner.value
        source_totals[source_key] += 1
        owner_totals[owner_key] += 1

        if row.stage == LeadStage.won:
            source_won[source_key] += 1
        if row.stage in ACTIVE_STAGES:
            active_by_owner[owner_key][row.stage] += 1
            if row.entered_at is not None and (export_time_utc - row.entered_at).total_seconds() > 3 * 86400:
                stuck_count += 1

        events = stage_events_by_lead_uid.get(row.lead_uid, [])
        for event in events:
            if not event.approved:
                unapproved_count += 1
            if event.left_at is None:
                continue
            duration_days = (event.left_at - event.entered_at).total_seconds() / 86400
            duration_by_stage[event.stage].append(duration_days)
            duration_by_owner[owner_key].append(duration_days)

    n_total = len(rows)

    source_conversion_rows = []
    for source in sorted(source_totals):
        total = source_totals[source]
        won = source_won.get(source, 0)
        source_conversion_rows.append(
            {
                "source": source,
                "total": total,
                "won": won,
                "rate": _safe_ratio(won, total),
            }
        )
    if not source_conversion_rows:
        source_conversion_rows = [{"source": "—", "total": 0, "won": 0, "rate": 0.0}]

    owner_rows = [{"owner": owner, "total": total} for owner, total in sorted(owner_totals.items())]
    if not owner_rows:
        owner_rows = [{"owner": "—", "total": 0}]

    avg_duration_by_owner_rows = []
    for owner in sorted(owner_totals):
        avg_duration_by_owner_rows.append(
            {
                "owner": owner,
                "days": _average(duration_by_owner[owner]),
            }
        )
    if not avg_duration_by_owner_rows:
        avg_duration_by_owner_rows = [{"owner": "—", "days": 0.0}]

    active_load_rows = []
    for owner in sorted(set(owner_totals) | set(active_by_owner)):
        new_count = active_by_owner[owner][LeadStage.new]
        qualified_count = active_by_owner[owner][LeadStage.qualified]
        proposal_count = active_by_owner[owner][LeadStage.proposal]
        active_load_rows.append(
            {
                "owner": owner,
                "new": new_count,
                "qualified": qualified_count,
                "proposal": proposal_count,
                "active_total": new_count + qualified_count + proposal_count,
            }
        )
    if not active_load_rows:
        active_load_rows = [{"owner": "—", "new": 0, "qualified": 0, "proposal": 0, "active_total": 0}]

    return {
        "n_total": n_total,
        "stage_counts": stage_counts,
        "conv_new_to_qualified": _safe_ratio(stage_counts[LeadStage.qualified], stage_counts[LeadStage.new]),
        "conv_qualified_to_proposal": _safe_ratio(stage_counts[LeadStage.proposal], stage_counts[LeadStage.qualified]),
        "conv_proposal_to_won": _safe_ratio(stage_counts[LeadStage.won], stage_counts[LeadStage.proposal]),
        "conv_total_to_won": _safe_ratio(stage_counts[LeadStage.won], n_total),
        "lost_share": _safe_ratio(stage_counts[LeadStage.lost], n_total),
        "avg_duration_by_stage": {stage: _average(duration_by_stage[stage]) for stage in STAGE_ORDER},
        "avg_duration_by_owner_rows": avg_duration_by_owner_rows,
        "unapproved_count": unapproved_count,
        "stuck_count": stuck_count,
        "source_conversion_rows": source_conversion_rows,
        "owner_rows": owner_rows,
        "active_load_rows": active_load_rows,
    }


def _safe_ratio(numerator: int | float, denominator: int | float) -> float:
    if denominator == 0:
        return 0.0
    return float(numerator) / float(denominator)


def _average(values: list[float]) -> float:
    if not values:
        return 0.0
    return sum(values) / len(values)


def _row_to_values(row: LeadExportRow) -> list[str]:
    entered_at = row.entered_at.isoformat() if row.entered_at is not None else ""
    return [
        row.lead_uid,
        row.title or "",
        row.notes or "",
        str(row.owner),
        str(row.stage),
        entered_at,
        str(row.source_code),
    ]
