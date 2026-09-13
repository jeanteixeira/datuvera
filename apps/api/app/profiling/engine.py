from typing import Dict, Any
from sqlalchemy.engine import URL
from app.profiling.postgres import PostgresProfiler
from app.models.datasource import DataSource


def profile_table_from_source(source: DataSource, schema: str, table: str) -> Dict[str, Any]:
    url = URL.create("postgresql+psycopg", username=source.username, password=source.password, host=source.host, port=source.port, database=source.database)
    profiler = PostgresProfiler(url)
    return profiler.profile_table(source.id, schema, table)
