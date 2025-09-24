from __future__ import annotations
from typing import Optional, List, Dict, Any, Literal
from datetime import datetime
from pydantic import BaseModel, Field

# ---------- Token ----------
class TokenResponse(BaseModel):
    access_token: str
    token_type: Optional[str] = "bearer"
    expires_in: Optional[int] = None
    refresh_token: Optional[str] = None
    scope: Optional[str] = None

# ---------- VKU: список полей (/fields/list) ----------
class FieldListItem(BaseModel):
    id: int
    name: str
    date_created: datetime
    latitude_center: float
    longitude_center: float
    altitude_center: float
    file_path: str
    user_id: int
    plot_count: int

# ---------- Generic (если понадобится /fields с пагинацией) ----------
class FieldItem(BaseModel):
    id: str | int
    name: Optional[str] = None
    area_ha: Optional[float] = Field(default=None, ge=0)
    crop: Optional[str] = None
    org: Optional[str] = None

class FieldsResponse(BaseModel):
    items: List[FieldItem]
    total: int

# ---------- GeoJSON ----------
class GeoJSONGeometry(BaseModel):
    type: Literal[
        "Point", "MultiPoint",
        "LineString", "MultiLineString",
        "Polygon", "MultiPolygon"
    ]
    coordinates: Any

class GeoJSONFeature(BaseModel):
    id: Optional[str | int] = None
    type: Literal["Feature"]
    properties: Dict[str, Any]
    geometry: GeoJSONGeometry

class FeatureCollection(BaseModel):
    type: Literal["FeatureCollection"]
    features: List[GeoJSONFeature]

# ---------- Прочее ----------
class GeometryResponse(BaseModel):
    id: str | int
    geometry: Dict[str, Any]
    crs: Optional[str] = None
