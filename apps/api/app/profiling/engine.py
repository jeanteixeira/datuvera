from typing import Dict, Any
from app.profiling.postgres import PostgresProfiler
from app.models.datasource import DataSource


def profile_table_from_source(source: DataSource, schema: str, table: str) -> Dict[str, Any]:
    url = f"postgresql://{source.username}:{source.password}@{source.host}:{source.port}/{source.database}"
    profiler = PostgresProfiler(url)
    return profiler.profile_table(source.id, schema, table)
