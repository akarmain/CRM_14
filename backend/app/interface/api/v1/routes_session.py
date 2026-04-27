from fastapi import APIRouter, Request, Response, status

from app.core.auth import ROLE_LABELS, build_permissions, get_current_role
from app.interface.api.schemas import SessionMeResponse, SessionRoleRequest

router = APIRouter()


@router.post("/session/role", response_model=SessionMeResponse, status_code=status.HTTP_200_OK)
async def set_session_role(payload: SessionRoleRequest, request: Request) -> SessionMeResponse:
    request.session["role"] = payload.role.value
    return SessionMeResponse(
        role=payload.role,
        role_label=ROLE_LABELS[payload.role],
        permissions=build_permissions(payload.role),
    )


@router.get("/session/me", response_model=SessionMeResponse)
async def get_session_me(request: Request) -> SessionMeResponse:
    role = get_current_role(request)
    return SessionMeResponse(
        role=role,
        role_label=ROLE_LABELS[role],
        permissions=build_permissions(role),
    )


@router.delete("/session/role", status_code=status.HTTP_204_NO_CONTENT)
async def clear_session_role(request: Request) -> Response:
    request.session.clear()
    return Response(status_code=status.HTTP_204_NO_CONTENT)
