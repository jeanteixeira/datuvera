from typing import List, Dict, Any, Optional
from sqlalchemy import create_engine, inspect, text
from sqlalchemy.engine import Engine
from datetime import datetime
from app.profiling.models import DatasetProfile, ColumnProfile, ColumnTopValue


class PostgresProfiler:
    def __init__(self, url: str, connect_args: Optional[dict] = None):
        # ensure we use the psycopg (psycopg3) driver if available
        if url.startswith("postgresql://"):
            url = url.replace("postgresql://", "postgresql+psycopg://", 1)
        self.engine: Engine = create_engine(url, connect_args=connect_args or {})
        self.inspector = inspect(self.engine)

    def _quote_ident(self, *names: str) -> str:
        preparer = self.engine.dialect.identifier_preparer
        return ".".join(preparer.quote(n) for n in names)

    def table_exists(self, schema: str, table: str) -> bool:
        inspector = inspect(self.engine)
        try:
            if table in inspector.get_table_names(schema=schema):
                return True
        except Exception:
            pass

        # fallback: query information_schema in a safe, parameterized way
        with self.engine.connect() as conn:
            res = conn.execute(text("SELECT EXISTS (SELECT 1 FROM information_schema.tables WHERE table_schema = :schema AND table_name = :table)"), {"schema": schema, "table": table}).scalar()
            return bool(res)

    def profile_table(self, source_id: int, schema: str, table: str) -> Dict[str, Any]:
        # validate
        if not self.table_exists(schema, table):
            raise ValueError("Table not found")

        q_table = self._quote_ident(schema, table)

        with self.engine.connect() as conn:
            # dataset level
            row_count = conn.execute(text(f"SELECT COUNT(*) FROM {q_table}")).scalar() or 0
            inspector = inspect(self.engine)
            columns_info = inspector.get_columns(table, schema=schema)
            column_count = len(columns_info)

            # estimated size using pg_total_relation_size
            try:
                # Use format('%I.%I', schema, table) to safely compose an identifier
                # and cast to regclass. Pass schema/table as parameters to avoid
                # direct string interpolation.
                # cast parameters to text so PostgreSQL can determine their type
                size_q = text("SELECT pg_total_relation_size(format('%I.%I', CAST(:schema AS text), CAST(:table AS text))::regclass)")
                estimated_size = conn.execute(size_q, {"schema": schema, "table": table}).scalar()
            except Exception:
                estimated_size = None

            generated_at = datetime.utcnow()

            dataset = DatasetProfile(
                source_id=source_id,
                schema=schema,
                table=table,
                row_count=int(row_count),
                column_count=column_count,
                estimated_size_bytes=estimated_size,
                generated_at=generated_at,
            )

            columns = []
            for col in columns_info:
                name = col["name"]
                dtype = str(col.get("type"))
                nullable = col.get("nullable", True)

                q_col = self._quote_ident(name)
                # basic stats: null_count, distinct_count
                agg_sql = f"SELECT COUNT(*) as total, SUM(CASE WHEN {q_col} IS NULL THEN 1 ELSE 0 END) as nulls, COUNT(DISTINCT {q_col}) as distincts FROM {q_table}"
                agg = conn.execute(text(agg_sql)).mappings().first()
                total = int(agg["total"] or 0)
                nulls = int(agg["nulls"] or 0)
                distincts = int(agg["distincts"] or 0)

                null_pct = (nulls / total * 100) if total else 0.0
                distinct_pct = (distincts / total * 100) if total else 0.0

                col_profile = ColumnProfile(
                    name=name,
                    data_type=dtype,
                    nullable=nullable,
                    null_count=nulls,
                    null_percentage=round(null_pct, 4),
                    distinct_count=distincts,
                    distinct_percentage=round(distinct_pct, 4),
                )

                # type-specific
                lower_dtype = dtype.lower()
                try:
                    if any(t in lower_dtype for t in ("int", "numeric", "decimal", "real", "double")):
                        stats = conn.execute(text(f"SELECT MIN({q_col}) as min, MAX({q_col}) as max, AVG({q_col}) as mean FROM {q_table}")).mappings().first()
                        col_profile.min = stats["min"]
                        col_profile.max = stats["max"]
                        col_profile.mean = float(stats["mean"]) if stats["mean"] is not None else None
                    elif any(t in lower_dtype for t in ("char", "text", "varchar")):
                        stats = conn.execute(text(f"SELECT MIN(LENGTH({q_col})) as min_length, MAX(LENGTH({q_col})) as max_length, AVG(LENGTH({q_col})) as avg_length FROM {q_table}" )).mappings().first()
                        col_profile.min_length = int(stats["min_length"]) if stats["min_length"] is not None else None
                        col_profile.max_length = int(stats["max_length"]) if stats["max_length"] is not None else None
                        col_profile.avg_length = float(stats["avg_length"]) if stats["avg_length"] is not None else None
                    elif any(t in lower_dtype for t in ("date", "timestamp")):
                        stats = conn.execute(text(f"SELECT MIN({q_col}) as min, MAX({q_col}) as max FROM {q_table}")).mappings().first()
                        col_profile.min = stats["min"]
                        col_profile.max = stats["max"]
                    elif "bool" in lower_dtype:
                        stats = conn.execute(text(f"SELECT SUM(CASE WHEN {q_col} THEN 1 ELSE 0 END) as true_count, SUM(CASE WHEN {q_col} = FALSE THEN 1 ELSE 0 END) as false_count FROM {q_table}")).mappings().first()
                        col_profile.true_count = int(stats["true_count"] or 0)
                        col_profile.false_count = int(stats["false_count"] or 0)
                except Exception:
                    # non-fatal; leave type-specific metrics empty
                    pass

                # top values
                try:
                    top_q = text(f"SELECT {q_col} as val, COUNT(*) as cnt FROM {q_table} GROUP BY {q_col} ORDER BY cnt DESC NULLS LAST LIMIT 5")
                    top_rows = conn.execute(top_q).mappings().all()
                    tops = []
                    for r in top_rows:
                        tops.append(ColumnTopValue(value=r["val"], count=int(r["cnt"])))
                    col_profile.top_values = tops
                except Exception:
                    col_profile.top_values = []

                columns.append(col_profile)

            return {
                "dataset": dataset,
                "columns": columns,
            }
