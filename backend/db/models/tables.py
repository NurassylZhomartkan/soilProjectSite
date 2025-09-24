# backend/db/models/tables.py
from __future__ import annotations
import uuid, datetime
from sqlalchemy import (
    Column, Text, Float, Integer, BigInteger, Date,
    ForeignKey, UniqueConstraint, Index, Enum as SAEnum
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship, Mapped, mapped_column
from geoalchemy2 import Geometry

from .base import Base

# ===== ENUM =====
SourceType = SAEnum('kazhydromet','uni','manual','era5_land','amsr2', name='source_type')
DepthCode  = SAEnum('0-20','0-50','0-100', name='depth_code')
VariableCode = SAEnum(
    'soil_moisture','air_temp','air_temp_max','air_temp_min',
    'relative_humidity','precipitation', name='variable_code'
)

# ===== MODELS =====

class Station(Base):
    __tablename__ = "stations"
    station_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True)
    code: Mapped[str | None] = mapped_column(Text, unique=True)
    name: Mapped[str] = mapped_column(Text, nullable=False)
    source = mapped_column(SourceType, nullable=False, default='kazhydromet')
    lat: Mapped[float] = mapped_column(Float, nullable=False)
    lon: Mapped[float] = mapped_column(Float, nullable=False)
    alt_m: Mapped[float | None] = mapped_column(Float)
    geom = mapped_column(Geometry(geometry_type='POINT', srid=4326))
    meteo_daily: Mapped[list["MeteoDaily"]] = relationship("MeteoDaily", back_populates="station")

Index("idx_stations_geom", Station.geom, postgresql_using="gist")
Index("idx_stations_source", Station.__table__.c.source)


class SoilPoint(Base):
    __tablename__ = "soil_points"
    soil_point_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True)
    code: Mapped[str | None] = mapped_column(Text, unique=True)
    name: Mapped[str | None] = mapped_column(Text)
    lat: Mapped[float] = mapped_column(Float, nullable=False)
    lon: Mapped[float] = mapped_column(Float, nullable=False)
    station_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("stations.station_id", ondelete="SET NULL"))
    geom = mapped_column(Geometry(geometry_type='POINT', srid=4326))

    station: Mapped["Station | None"] = relationship("Station")
    manual_records: Mapped[list["SoilDecadalManual"]] = relationship("SoilDecadalManual", back_populates="soil_point")

Index("idx_soil_points_geom", SoilPoint.geom, postgresql_using="gist")
Index("idx_soil_points_station", SoilPoint.__table__.c.station_id)


class Site(Base):
    __tablename__ = "sites"
    site_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True)
    code: Mapped[str | None] = mapped_column(Text, unique=True)
    name: Mapped[str] = mapped_column(Text, nullable=False)
    source = mapped_column(SourceType, nullable=False, default='uni')
    bounds = mapped_column(Geometry(geometry_type='POLYGON', srid=4326), nullable=False)

    points: Mapped[list["SitePoint"]] = relationship("SitePoint", back_populates="site", cascade="all, delete-orphan")

Index("idx_sites_bounds", Site.__table__.c.bounds, postgresql_using="gist")


class SitePoint(Base):
    __tablename__ = "site_points"
    site_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("sites.site_id", ondelete="CASCADE"), primary_key=True)
    soil_point_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("soil_points.soil_point_id", ondelete="CASCADE"), primary_key=True)

    site: Mapped["Site"] = relationship("Site", back_populates="points")
    soil_point: Mapped["SoilPoint"] = relationship("SoilPoint")


class MeteoDaily(Base):
    __tablename__ = "meteo_daily"
    meteo_id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    station_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("stations.station_id", ondelete="CASCADE"), nullable=False)
    date: Mapped[datetime.date] = mapped_column("date", Date, nullable=False)
    air_temp_avg_c: Mapped[float | None] = mapped_column(Float)
    air_temp_max_c: Mapped[float | None] = mapped_column(Float)
    air_temp_min_c: Mapped[float | None] = mapped_column(Float)
    rel_humidity: Mapped[float | None] = mapped_column(Float)
    precipitation_mm: Mapped[float | None] = mapped_column(Float)
    source = mapped_column(SourceType, nullable=False, default='kazhydromet')

    station: Mapped["Station"] = relationship("Station", back_populates="meteo_daily")

    __table_args__ = (
        UniqueConstraint("station_id", "date", name="uq_meteo_daily"),
        Index("idx_meteo_daily_station_date", "station_id", "date"),
        Index("idx_meteo_daily_source", "source"),
        Index("idx_meteo_daily_date", "date"),
    )


class SoilDecadalManual(Base):
    __tablename__ = "soil_decadal_manual"
    rec_id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    soil_point_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("soil_points.soil_point_id", ondelete="CASCADE"), nullable=False)
    year: Mapped[int] = mapped_column(Integer, nullable=False)
    month: Mapped[int] = mapped_column(Integer, nullable=False)
    decade: Mapped[int] = mapped_column(Integer, nullable=False)
    depth = mapped_column(DepthCode, nullable=False)
    value_mm: Mapped[float] = mapped_column(Float, nullable=False)
    value_frac: Mapped[float | None] = mapped_column(Float)
    quality_flag: Mapped[str | None] = mapped_column(Text)
    source = mapped_column(SourceType, nullable=False, default='kazhydromet')

    soil_point: Mapped["SoilPoint"] = relationship("SoilPoint", back_populates="manual_records")

    __table_args__ = (
        UniqueConstraint("soil_point_id", "year", "month", "decade", "depth", name="uq_soil_decadal_manual"),
        Index("idx_soil_decadal_manual_point", "soil_point_id"),
        Index("idx_soil_decadal_manual_ymd", "year", "month", "decade"),
    )


class SoilDecadalExternal(Base):
    __tablename__ = "soil_decadal_external"
    rec_id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    soil_point_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("soil_points.soil_point_id", ondelete="CASCADE"), nullable=False)
    year: Mapped[int] = mapped_column(Integer, nullable=False)
    month: Mapped[int] = mapped_column(Integer, nullable=False)
    decade: Mapped[int] = mapped_column(Integer, nullable=False)
    depth = mapped_column(DepthCode, nullable=False)
    variable = mapped_column(VariableCode, nullable=False, default='soil_moisture')
    value: Mapped[float] = mapped_column(Float, nullable=False)
    units: Mapped[str | None] = mapped_column(Text)
    source = mapped_column(SourceType, nullable=False)

    __table_args__ = (
        UniqueConstraint("soil_point_id", "year", "month", "decade", "depth", "variable", "source", name="uq_soil_decadal_external"),
        Index("idx_soil_decadal_external_point", "soil_point_id"),
        Index("idx_soil_decadal_external_ymd", "year", "month", "decade"),
        Index("idx_soil_decadal_external_src", "source"),
    )


class SiteMeasurementsDecadal(Base):
    __tablename__ = "site_measurements_decadal"
    rec_id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    site_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("sites.site_id", ondelete="CASCADE"), nullable=False)
    soil_point_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("soil_points.soil_point_id", ondelete="SET NULL"))
    year: Mapped[int] = mapped_column(Integer, nullable=False)
    month: Mapped[int] = mapped_column(Integer, nullable=False)
    decade: Mapped[int] = mapped_column(Integer, nullable=False)
    depth = mapped_column(DepthCode, nullable=False)
    value_mm: Mapped[float] = mapped_column(Float, nullable=False)
    source = mapped_column(SourceType, nullable=False, default='uni')

    __table_args__ = (
        UniqueConstraint("site_id", "soil_point_id", "year", "month", "decade", "depth", name="uq_site_measurements_decadal"),
        Index("idx_site_meas_dec_site", "site_id"),
        Index("idx_site_meas_dec_ymd", "year", "month", "decade"),
    )


class HTCAnnual(Base):
    __tablename__ = "htc_annual"
    rec_id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    station_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("stations.station_id", ondelete="CASCADE"), nullable=False)
    year: Mapped[int] = mapped_column(Integer, nullable=False)
    htc_value: Mapped[float] = mapped_column(Float, nullable=False)
    method: Mapped[str] = mapped_column(Text, nullable=False, default='Selianinov')
    period_note: Mapped[str | None] = mapped_column(Text)

    __table_args__ = (
        UniqueConstraint("station_id", "year", "method", "period_note", name="uq_htc_annual_expr"),
    )
