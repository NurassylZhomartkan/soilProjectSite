import sys
import os
from logging.config import fileConfig

from sqlalchemy import engine_from_config, pool
from alembic import context

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../..")))

from backend.db.models import Base
import backend.db.models.tables

config = context.config
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata

from alembic.autogenerate import renderers
from sqlalchemy.dialects import postgresql as psql
from geoalchemy2 import types as geo_types

@renderers.dispatch_for(geo_types.Geometry)
def _render_geometry(type_, autogen_context):
    autogen_context.imports.add("from geoalchemy2 import types as geo_types")
    return f"geo_types.Geometry(geometry_type={type_.geometry_type!r}, srid={type_.srid})"

@renderers.dispatch_for(psql.UUID)
def _render_uuid(type_, autogen_context):
    autogen_context.imports.add("from sqlalchemy.dialects import postgresql as psql")
    return "psql.UUID(as_uuid=True)"

VIEWS = set()

def include_object(obj, name, type_, reflected, compare_to):
    if type_ == "table" and name in VIEWS:
        return False
    return True

def run_migrations_offline():
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,
        compare_server_default=True,
        include_object=include_object,
    )
    with context.begin_transaction():
        context.run_migrations()

def run_migrations_online():
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            compare_type=True,
            compare_server_default=True,
            include_object=include_object,
        )
        with context.begin_transaction():
            context.run_migrations()

if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
