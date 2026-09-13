import os
from types import SimpleNamespace
from uuid import uuid4

import pytest
from sqlalchemy import create_engine, text
from sqlalchemy.engine import make_url

from app.quality.engine import run_quality
from app.quality.rules import evaluate_unique, evaluate_value_bound
from app.quality.scoring import check_score, severity_from_percentage, compute_dimension_score, weighted_score
from app.services.connectors.postgres_connector import PostgreSQLConnector


@pytest.mark.parametrize('percentage,score,status', [(0, 100, 'passed'), (2, 98, 'warning'), (5, 95, 'warning'), (10, 90, 'failed')])
def test_score_and_severity(percentage, score, status):
    assert check_score(percentage) == score
    assert severity_from_percentage(percentage) == status


@pytest.mark.parametrize('percentage,score', [(-1, 100), (101, 0)])
def test_score_clamped(percentage, score):
    assert check_score(percentage) == score


def test_compute_dimension_score_empty():
    assert compute_dimension_score([]) is None


def test_dimension_uses_percentage_not_status():
    assert compute_dimension_score([{'failed_percentage': 2, 'status': 'warning'}, {'failed_percentage': 10, 'status': 'failed'}]) == 94


def test_overall_ignores_none():
    assert weighted_score({'completeness': 97, 'uniqueness': None, 'validity': 98}, {}) == 97.5
    assert weighted_score({'completeness': None}, {}) == 0


@pytest.fixture
def quality_db():
    url = make_url(os.environ['DATABASE_URL'])
    engine = create_engine(url)
    schema = '_test_quality_' + uuid4().hex
    with engine.begin() as conn:
        conn.execute(text(f'CREATE SCHEMA "{schema}"'))
    source = SimpleNamespace(id=0, username=url.username, password=url.password, host=url.host,
                             port=url.port or 5432, database=url.database)
    connector = PostgreSQLConnector(source.host, source.port, source.database, source.username, source.password)
    try:
        yield engine, schema, source, connector
    finally:
        with engine.begin() as conn:
            conn.execute(text(f'DROP SCHEMA "{schema}" CASCADE'))
        engine.dispose()


def test_completeness_validity_and_declarative_bounds(quality_db):
    engine, schema, source, connector = quality_db
    with engine.begin() as conn:
        conn.execute(text(f'CREATE TABLE "{schema}".bounds (value numeric)'))
        conn.execute(text(f'INSERT INTO "{schema}".bounds VALUES (NULL), (-1), (0), (10), (11)'))
    result = run_quality(source, schema, 'bounds', connector, [
        {'column': 'value', 'type': 'min_value', 'value': 0},
        {'column': 'value', 'type': 'max_value', 'value': 10},
    ])
    assert result.dimensions == {'completeness': 80, 'uniqueness': None, 'validity': 80}
    assert result.score == 80
    for check in result.checks:
        assert check.failed_count == 1
        assert check.failed_percentage == 20
        assert check.score == 80
        assert check.status == 'failed'


def test_unique_null_and_composite_constraints(quality_db):
    engine, schema, source, connector = quality_db
    with engine.begin() as conn:
        conn.execute(text(f'CREATE TABLE "{schema}".keys (a integer, b integer, email text UNIQUE, UNIQUE (a, b))'))
        conn.execute(text(f"INSERT INTO \"{schema}\".keys VALUES (1,1,NULL), (1,2,NULL), (2,1,'a'), (NULL,1,'b'), (NULL,1,'c')"))
    result = run_quality(source, schema, 'keys', connector)
    checks = [check for check in result.checks if check.rule == 'unique']
    assert len(checks) == 2
    assert all(check.score == 100 and check.failed_count == 0 for check in checks)
    assert any(check.columns == ['a', 'b'] and check.column is None for check in checks)
    assert any(check.column == 'email' for check in checks)
    assert result.dimensions['uniqueness'] == 100


def test_duplicate_groups_count_all_affected_rows(quality_db):
    engine, schema, _, _ = quality_db
    with engine.begin() as conn:
        conn.execute(text(f'CREATE TABLE "{schema}".duplicates (a integer, b integer)'))
        conn.execute(text(f'INSERT INTO "{schema}".duplicates VALUES (1,1), (1,1), (1,2), (NULL,1), (NULL,1)'))
        assert evaluate_unique(conn, schema, 'duplicates', ['a', 'b']) == {'total': 5, 'invalid': 2}
        assert evaluate_unique(conn, schema, 'duplicates', ['a', 'b'], True) == {'total': 5, 'invalid': 4}


def test_composite_primary_key(quality_db):
    engine, schema, source, connector = quality_db
    with engine.begin() as conn:
        conn.execute(text(f'CREATE TABLE "{schema}".keys (a integer, b integer, PRIMARY KEY (a,b))'))
        conn.execute(text(f'INSERT INTO "{schema}".keys VALUES (1,1), (1,2), (2,1)'))
    result = run_quality(source, schema, 'keys', connector)
    checks = [check for check in result.checks if check.rule == 'unique']
    assert len(checks) == 1
    assert checks[0].columns == ['a', 'b']
    assert checks[0].score == 100


def test_missing_demo_columns_are_not_applicable(quality_db, monkeypatch):
    from app.quality import rules
    engine, schema, source, connector = quality_db
    with engine.begin() as conn:
        conn.execute(text(f'CREATE TABLE "{schema}".customers (id integer PRIMARY KEY)'))
        conn.execute(text(f'INSERT INTO "{schema}".customers VALUES (1)'))
    configured = [{'column': 'email', 'type': 'email_format'}, {'column': 'state', 'type': 'allowed_values', 'params': {'values': ['AL']}}]
    result = run_quality(source, schema, 'customers', connector, configured)
    assert result.dimensions['validity'] is None
    assert result.score == 100
    assert all(check.rule not in ['email_format', 'allowed_values'] for check in result.checks)


def test_empty_dataset(quality_db):
    engine, schema, source, connector = quality_db
    with engine.begin() as conn:
        conn.execute(text(f'CREATE TABLE "{schema}".empty (id integer PRIMARY KEY, value numeric)'))
    result = run_quality(source, schema, 'empty', connector, [{'column': 'value', 'type': 'min_value', 'value': 0}])
    assert result.score == 100
    assert all(check.failed_count == 0 and check.score == 100 for check in result.checks)


def test_bound_identifiers_are_quoted_and_values_parameterized(quality_db):
    engine, schema, _, _ = quality_db
    with engine.begin() as conn:
        conn.execute(text(f'CREATE TABLE "{schema}"."odd;table" ("odd\"\"column" numeric)'))
        conn.execute(text(f'INSERT INTO "{schema}"."odd;table" VALUES (1), (2)'))
        assert evaluate_value_bound(conn, schema, 'odd;table', 'odd"column', 1, 'max_value') == {'total': 2, 'invalid': 1}
