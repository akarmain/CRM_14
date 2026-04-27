import zipfile
from io import BytesIO
from xml.etree import ElementTree as ET

import pytest
from httpx import ASGITransport, AsyncClient

from app.core.config import get_settings
from app.core.deps import reset_container
from app.main import create_app


async def login_as(client: AsyncClient, role: str) -> None:
    response = await client.post("/api/v1/session/role", json={"role": role})
    assert response.status_code == 200


_NS_MAIN = "http://schemas.openxmlformats.org/spreadsheetml/2006/main"
_NS_REL = "http://schemas.openxmlformats.org/officeDocument/2006/relationships"
_NS_PKG_REL = "http://schemas.openxmlformats.org/package/2006/relationships"


def _xlsx_sheet_path(zf: zipfile.ZipFile, sheet_name: str) -> str:
    workbook = ET.fromstring(zf.read("xl/workbook.xml"))
    rels = ET.fromstring(zf.read("xl/_rels/workbook.xml.rels"))
    rel_by_id = {item.attrib["Id"]: item.attrib["Target"] for item in rels.findall(f".//{{{_NS_PKG_REL}}}Relationship")}
    for sheet in workbook.findall(f".//{{{_NS_MAIN}}}sheet"):
        if sheet.attrib.get("name") == sheet_name:
            rel_id = sheet.attrib.get(f"{{{_NS_REL}}}id")
            target = rel_by_id[rel_id]
            return f"xl/{target}"
    raise AssertionError(f"Sheet '{sheet_name}' not found")


def _xlsx_shared_strings(zf: zipfile.ZipFile) -> list[str]:
    if "xl/sharedStrings.xml" not in zf.namelist():
        return []
    root = ET.fromstring(zf.read("xl/sharedStrings.xml"))
    values: list[str] = []
    for si in root.findall(f".//{{{_NS_MAIN}}}si"):
        chunks = []
        for t in si.findall(f".//{{{_NS_MAIN}}}t"):
            chunks.append(t.text or "")
        values.append("".join(chunks))
    return values


def _xlsx_row_values(zf: zipfile.ZipFile, sheet_path: str, row_number: int) -> list[str]:
    root = ET.fromstring(zf.read(sheet_path))
    shared_strings = _xlsx_shared_strings(zf)
    row = root.find(f".//{{{_NS_MAIN}}}row[@r='{row_number}']")
    if row is None:
        return []
    values: list[str] = []
    for cell in row.findall(f"{{{_NS_MAIN}}}c"):
        cell_type = cell.attrib.get("t")
        value_node = cell.find(f"{{{_NS_MAIN}}}v")
        if value_node is None:
            values.append("")
            continue
        raw = value_node.text or ""
        if cell_type == "s":
            values.append(shared_strings[int(raw)] if raw else "")
        else:
            values.append(raw)
    return values


@pytest.mark.anyio
async def test_manager_scope_and_return_request_flow(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("STORAGE_MODE", "memo")
    monkeypatch.setenv("SESSION_SECRET", "test-secret")
    get_settings.cache_clear()
    reset_container()

    app = create_app()

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        await login_as(client, "sales_head")
        foreign_resp = await client.post(
            "/api/v1/leads",
            json={
                "source_code": "website",
                "owner": "manager_2",
                "title": "Foreign lead",
                "notes": "owned by manager 2",
            },
        )
        assert foreign_resp.status_code == 201
        foreign_lead = foreign_resp.json()

        await login_as(client, "manager_1")
        own_resp = await client.post(
            "/api/v1/leads",
            json={
                "source_code": "event",
                "title": "Own lead",
                "notes": "owned by manager 1",
            },
        )
        assert own_resp.status_code == 201
        own_lead = own_resp.json()
        assert own_lead["owner"] == "manager_1"

        list_resp = await client.get("/api/v1/leads")
        assert list_resp.status_code == 200
        listed_uids = {item["lead_uid"] for item in list_resp.json()}
        assert own_lead["lead_uid"] in listed_uids
        assert foreign_lead["lead_uid"] not in listed_uids

        foreign_get = await client.get(f"/api/v1/leads/{foreign_lead['lead_uid']}")
        assert foreign_get.status_code == 403

        patch_resp = await client.patch(
            f"/api/v1/leads/{own_lead['lead_uid']}",
            json={"title": "Should fail"},
        )
        assert patch_resp.status_code == 403

        move_resp = await client.post(
            f"/api/v1/leads/{own_lead['lead_uid']}/stage",
            json={"stage": "qualified", "comment": "Qualified"},
        )
        assert move_resp.status_code == 200
        assert move_resp.json()["lead"]["current_stage"] == "qualified"

        invalid_back_resp = await client.post(
            f"/api/v1/leads/{own_lead['lead_uid']}/stage",
            json={"stage": "new", "comment": "Back"},
        )
        assert invalid_back_resp.status_code == 400

        return_request_resp = await client.post(
            f"/api/v1/leads/{own_lead['lead_uid']}/return-requests",
            json={"comment": "Need to go back"},
        )
        assert return_request_resp.status_code == 200
        request_payload = return_request_resp.json()
        assert request_payload["from_stage"] == "qualified"
        assert request_payload["to_stage"] == "new"
        assert request_payload["status"] == "pending"

        await login_as(client, "sales_head")
        approve_resp = await client.post(
            f"/api/v1/return-requests/{request_payload['id']}/approve",
            json={"review_comment": "Approved"},
        )
        assert approve_resp.status_code == 200
        assert approve_resp.json()["status"] == "approved"

        detail_resp = await client.get(f"/api/v1/leads/{own_lead['lead_uid']}")
        assert detail_resp.status_code == 200
        detail = detail_resp.json()
        assert detail["current_stage"] == "new"
        assert len(detail["return_requests"]) == 1
        assert any(entry["action_type"] == "return_request_approved" for entry in detail["audit_entries"])


@pytest.mark.anyio
async def test_analyst_is_read_only_but_can_view_reports_and_export(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("STORAGE_MODE", "memo")
    monkeypatch.setenv("SESSION_SECRET", "test-secret")
    get_settings.cache_clear()
    reset_container()

    app = create_app()

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        await login_as(client, "sales_head")
        response = await client.post(
            "/api/v1/leads",
            json={
                "source_code": "website",
                "owner": "manager_1",
                "title": "Report lead",
                "notes": "for analytics",
            },
        )
        assert response.status_code == 201

        await login_as(client, "analyst")
        list_resp = await client.get("/api/v1/leads")
        assert list_resp.status_code == 200
        assert len(list_resp.json()) == 1

        create_resp = await client.post(
            "/api/v1/leads",
            json={"source_code": "website", "title": "Nope", "notes": "Denied"},
        )
        assert create_resp.status_code == 403

        reports_resp = await client.get("/api/v1/reports/summary")
        assert reports_resp.status_code == 200
        reports = reports_resp.json()
        assert reports["total_leads"] == 1
        assert any(item["stage"] == "new" and item["count"] == 1 for item in reports["counts"])

        export_resp = await client.get("/api/v1/leads/export?file_type=csv")
        assert export_resp.status_code == 200
        assert "lead_uid;title;notes;owner;stage;entered_at;source_code" in export_resp.text


@pytest.mark.anyio
async def test_xlsx_export_contains_analytics_and_data_sheets(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("STORAGE_MODE", "memo")
    monkeypatch.setenv("SESSION_SECRET", "test-secret")
    get_settings.cache_clear()
    reset_container()

    app = create_app()

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        await login_as(client, "sales_head")
        for owner in ("manager_1", "manager_2"):
            create_resp = await client.post(
                "/api/v1/leads",
                json={
                    "source_code": "website",
                    "owner": owner,
                    "title": f"Lead {owner}",
                    "notes": "export",
                },
            )
            assert create_resp.status_code == 201

        await login_as(client, "analyst")
        export_resp = await client.get("/api/v1/leads/export?file_type=xlsx&owner=manager_1")
        assert export_resp.status_code == 200

        with zipfile.ZipFile(BytesIO(export_resp.content), "r") as zf:
            workbook = ET.fromstring(zf.read("xl/workbook.xml"))
            sheet_names = [sheet.attrib["name"] for sheet in workbook.findall(f".//{{{_NS_MAIN}}}sheet")]
            assert sheet_names == ["Аналитика", "Данные"]

            analytics_sheet_path = _xlsx_sheet_path(zf, "Аналитика")
            data_sheet_path = _xlsx_sheet_path(zf, "Данные")
            assert analytics_sheet_path.endswith("sheet1.xml")
            assert data_sheet_path.endswith("sheet2.xml")

            headers = _xlsx_row_values(zf, data_sheet_path, 1)
            assert headers == ["lead_uid", "title", "notes", "owner", "stage", "entered_at", "source_code"]

            first_data_row = _xlsx_row_values(zf, data_sheet_path, 2)
            assert first_data_row[3] == "manager_1"

            second_data_row = _xlsx_row_values(zf, data_sheet_path, 3)
            assert second_data_row == []

            chart_files = [name for name in zf.namelist() if name.startswith("xl/charts/chart")]
            assert len(chart_files) == 4


@pytest.mark.anyio
async def test_sales_head_can_force_closed_lead_transition(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("STORAGE_MODE", "memo")
    monkeypatch.setenv("SESSION_SECRET", "test-secret")
    get_settings.cache_clear()
    reset_container()

    app = create_app()

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        await login_as(client, "sales_head")
        create_resp = await client.post(
            "/api/v1/leads",
            json={
                "source_code": "event",
                "owner": "manager_1",
                "title": "Conference lead",
                "notes": "Needs manual reopening",
            },
        )
        assert create_resp.status_code == 201
        lead_uid = create_resp.json()["lead_uid"]

        to_won_resp = await client.post(
            f"/api/v1/leads/{lead_uid}/stage",
            json={"stage": "won", "comment": "Closed"},
        )
        assert to_won_resp.status_code == 200

        reopen_resp = await client.post(
            f"/api/v1/leads/{lead_uid}/stage",
            json={"stage": "proposal", "comment": "Reopened by sales head"},
        )
        assert reopen_resp.status_code == 200
        assert reopen_resp.json()["lead"]["current_stage"] == "proposal"
