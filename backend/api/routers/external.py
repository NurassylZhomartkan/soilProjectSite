from fastapi import APIRouter, Depends, Query, Form, HTTPException
from ..deps import get_api_client, get_user_token
from ..client import ExternalAPIClient
from ..schemas import (
    TokenResponse,
    FieldsResponse,
    GeometryResponse,
    FieldListItem,
    FeatureCollection,
)

router = APIRouter(prefix="/external", tags=["external"])

# -------- AUTH (form-data) --------
@router.post("/login", response_model=TokenResponse)
async def login(
    username: str = Form(...),
    password: str = Form(...),
    grant_type: str = Form("password"),
    api: ExternalAPIClient = Depends(get_api_client),
):
    """
    Принимаем x-www-form-urlencoded (Form), проксируем POST /login во внешний API.
    Валидируем ответ: некоторые API возвращают 200 с текстом ошибки.
    """
    async with api.session():
        raw = await api.login(username=username, password=password, grant_type=grant_type)

    if not isinstance(raw, dict) or "access_token" not in raw:
        msg = raw.get("message") if isinstance(raw, dict) else str(raw)
        raise HTTPException(status_code=401, detail={"error": "Login failed", "upstream": msg, "raw": raw})

    return raw

# -------- GENERIC (на будущее) --------
@router.get("/fields", response_model=FieldsResponse, include_in_schema=False)
async def list_fields(
    page: int = Query(1, ge=1),
    limit: int = Query(100, ge=1, le=500),
    api: ExternalAPIClient = Depends(get_api_client),
    token: str | None = Depends(get_user_token),
):
    async with api.session():
        data = await api.get_fields(page=page, limit=limit, user_token=token)
    return data

@router.get("/fields/{field_id}/geometry", response_model=GeometryResponse, include_in_schema=False)
async def get_field_geometry(
    field_id: str,
    api: ExternalAPIClient = Depends(get_api_client),
    token: str | None = Depends(get_user_token),
):
    async with api.session():
        data = await api.get_field_geometry(field_id, user_token=token)
    return data

# -------- VKU specific --------
@router.get("/fields/list", response_model=list[FieldListItem])
async def list_fields_raw(
    api: ExternalAPIClient = Depends(get_api_client),
    token: str | None = Depends(get_user_token),
):
    async with api.session():
        data = await api.get_fields_list(user_token=token)
    return data

@router.get("/field/get/{field_id}", response_model=FeatureCollection)
async def get_field(
    field_id: int,
    api: ExternalAPIClient = Depends(get_api_client),
    token: str | None = Depends(get_user_token),
):
    async with api.session():
        data = await api.get_field(field_id, user_token=token)
    return data
