import pytest
from app.profiling.postgres import PostgresProfiler
from sqlalchemy import create_engine, text
import os


def get_db_url():
    # Use the main datuvera-db from compose
    return os.environ.get("DATABASE_URL") or "postgresql+psycopg://datuvera:datuvera@datuvera-db:5432/datuvera"


def setup_test_table(engine):
    with engine.begin() as conn:
        conn.execute(text("DROP TABLE IF EXISTS public._test_profile"))
        conn.execute(text("CREATE TABLE public._test_profile (id serial PRIMARY KEY, name text, val integer, active boolean, created_at timestamp)"))
        # insert deterministic rows using generate_series
        conn.execute(text(
            "INSERT INTO public._test_profile (name, val, active, created_at) SELECT 'name_' || (g % 10), (g % 50), ((g % 4)=0), now() - (g % 30) * INTERVAL '1 day' FROM generate_series(1,200) g"
        ))


def test_profile_basic():
    url = get_db_url()
    engine = create_engine(url)
    setup_test_table(engine)
    profiler = PostgresProfiler(url)
    res = profiler.profile_table(source_id=0, schema="public", table="_test_profile")
    assert res["dataset"].row_count == 200
    assert res["dataset"].column_count >= 5
    cols = {c.name: c for c in res["columns"]}
    assert "id" in cols
    assert "name" in cols
    assert cols["name"].distinct_count <= 10
