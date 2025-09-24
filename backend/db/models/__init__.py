# backend/db/models/__init__.py
from .base import Base
from .tables import (
    Station, SoilPoint, Site, SitePoint,
    MeteoDaily, SoilDecadalManual, SoilDecadalExternal,
    SiteMeasurementsDecadal, HTCAnnual
)

__all__ = [
    "Base",
    "Station", "SoilPoint", "Site", "SitePoint",
    "MeteoDaily", "SoilDecadalManual", "SoilDecadalExternal",
    "SiteMeasurementsDecadal", "HTCAnnual",
]
