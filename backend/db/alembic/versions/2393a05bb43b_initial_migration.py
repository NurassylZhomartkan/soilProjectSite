"""initial migration

Revision ID: 2393a05bb43b
Revises: 
Create Date: 2025-09-24 09:29:26.391340
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from geoalchemy2 import types as geo_types

# revision identifiers, used by Alembic.
revision: str = '2393a05bb43b'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Ensure PostGIS is enabled
    op.execute("CREATE EXTENSION IF NOT EXISTS postgis;")

    # Create 'sites' table
    op.create_table(
        'sites',
        sa.Column('site_id', sa.UUID(), nullable=False),
        sa.Column('code', sa.Text(), nullable=True),
        sa.Column('name', sa.Text(), nullable=False),
        sa.Column('source', sa.Enum('kazhydromet', 'uni', 'manual', 'era5_land', 'amsr2', name='source_type'), nullable=False),
        sa.Column('bounds', geo_types.Geometry(geometry_type='POLYGON', srid=4326), nullable=False),
        sa.PrimaryKeyConstraint('site_id'),
        sa.UniqueConstraint('code')
    )

    op.execute("""
        DO $$
        BEGIN
            IF NOT EXISTS (
                SELECT 1 FROM pg_class c
                JOIN pg_namespace n ON n.oid = c.relnamespace
                WHERE c.relname = 'idx_sites_bounds'
                  AND n.nspname = 'public'
            ) THEN
                CREATE INDEX idx_sites_bounds ON sites USING gist (bounds);
            END IF;
        END
        $$;
    """)

    # Create 'stations' table
    op.create_table(
        'stations',
        sa.Column('station_id', sa.UUID(), nullable=False),
        sa.Column('code', sa.Text(), nullable=True),
        sa.Column('name', sa.Text(), nullable=False),
        sa.Column('source', sa.Enum('kazhydromet', 'uni', 'manual', 'era5_land', 'amsr2', name='source_type'), nullable=False),
        sa.Column('lat', sa.Float(), nullable=False),
        sa.Column('lon', sa.Float(), nullable=False),
        sa.Column('alt_m', sa.Float(), nullable=True),
        sa.Column('geom', geo_types.Geometry(geometry_type='POINT', srid=4326), nullable=True),
        sa.PrimaryKeyConstraint('station_id'),
        sa.UniqueConstraint('code')
    )

    op.execute("""
        DO $$
        BEGIN
            IF NOT EXISTS (
                SELECT 1 FROM pg_class c
                JOIN pg_namespace n ON n.oid = c.relnamespace
                WHERE c.relname = 'idx_stations_geom'
                  AND n.nspname = 'public'
            ) THEN
                CREATE INDEX idx_stations_geom ON stations USING gist (geom);
            END IF;
        END
        $$;
    """)

    op.create_index('idx_stations_source', 'stations', ['source'], unique=False)

    # Create 'soil_points' table
    op.create_table(
        'soil_points',
        sa.Column('soil_point_id', sa.UUID(), nullable=False),
        sa.Column('code', sa.Text(), nullable=True),
        sa.Column('name', sa.Text(), nullable=True),
        sa.Column('lat', sa.Float(), nullable=False),
        sa.Column('lon', sa.Float(), nullable=False),
        sa.Column('station_id', sa.UUID(), nullable=True),
        sa.Column('geom', geo_types.Geometry(geometry_type='POINT', srid=4326), nullable=True),
        sa.ForeignKeyConstraint(['station_id'], ['stations.station_id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('soil_point_id'),
        sa.UniqueConstraint('code')
    )

    op.execute("""
        DO $$
        BEGIN
            IF NOT EXISTS (
                SELECT 1 FROM pg_class c
                JOIN pg_namespace n ON n.oid = c.relnamespace
                WHERE c.relname = 'idx_soil_points_geom'
                  AND n.nspname = 'public'
            ) THEN
                CREATE INDEX idx_soil_points_geom ON soil_points USING gist (geom);
            END IF;
        END
        $$;
    """)


def downgrade() -> None:
    op.drop_table('soil_points')
    op.drop_table('stations')
    op.drop_table('sites')
    op.execute("DROP TYPE IF EXISTS source_type CASCADE;")
