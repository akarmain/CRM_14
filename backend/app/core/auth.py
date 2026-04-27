from __future__ import annotations

from fastapi import Request

from app.core.errors import ForbiddenError, UnauthorizedError
from app.domain.enums import AppRole, Users


ROLE_LABELS: dict[AppRole, str] = {
    AppRole.manager_1: "Менеджер 1",
    AppRole.manager_2: "Менеджер 2",
    AppRole.sales_head: "Руководитель отдела продаж",
    AppRole.analyst: "Аналитик",
}

ROLE_PERMISSIONS: dict[AppRole, dict[str, bool]] = {
    AppRole.manager_1: {
        "can_read_all_leads": False,
        "can_create_leads": True,
        "can_import_leads": True,
        "can_export_leads": False,
        "can_update_any_lead": False,
        "can_delete_leads": False,
        "can_move_forward": True,
        "can_force_stage": False,
        "can_request_return": True,
        "can_review_returns": False,
        "can_view_reports": False,
        "can_view_audit_log": False,
    },
    AppRole.manager_2: {
        "can_read_all_leads": False,
        "can_create_leads": True,
        "can_import_leads": True,
        "can_export_leads": False,
        "can_update_any_lead": False,
        "can_delete_leads": False,
        "can_move_forward": True,
        "can_force_stage": False,
        "can_request_return": True,
        "can_review_returns": False,
        "can_view_reports": False,
        "can_view_audit_log": False,
    },
    AppRole.sales_head: {
        "can_read_all_leads": True,
        "can_create_leads": True,
        "can_import_leads": True,
        "can_export_leads": True,
        "can_update_any_lead": True,
        "can_delete_leads": True,
        "can_move_forward": True,
        "can_force_stage": True,
        "can_request_return": False,
        "can_review_returns": True,
        "can_view_reports": True,
        "can_view_audit_log": True,
    },
    AppRole.analyst: {
        "can_read_all_leads": True,
        "can_create_leads": False,
        "can_import_leads": False,
        "can_export_leads": True,
        "can_update_any_lead": False,
        "can_delete_leads": False,
        "can_move_forward": False,
        "can_force_stage": False,
        "can_request_return": False,
        "can_review_returns": False,
        "can_view_reports": True,
        "can_view_audit_log": False,
    },
}


def build_permissions(role: AppRole) -> dict[str, bool]:
    return ROLE_PERMISSIONS[role]


def get_current_role(request: Request) -> AppRole:
    raw_role = request.session.get("role")
    if raw_role is None:
        raise UnauthorizedError("Role session is missing. Select a role first.")

    try:
        return AppRole(raw_role)
    except ValueError as exc:
        raise UnauthorizedError("Role session is invalid. Select a role again.") from exc


def ensure_permission(role: AppRole, permission: str) -> None:
    if not ROLE_PERMISSIONS[role].get(permission, False):
        raise ForbiddenError("This action is not allowed for the current role.")


def is_manager_role(role: AppRole) -> bool:
    return role in {AppRole.manager_1, AppRole.manager_2}


def to_db_user(role: AppRole) -> Users:
    if role == AppRole.analyst:
        raise ForbiddenError("Analyst role cannot be used as a lead owner or comment author.")
    return Users(role.value)
