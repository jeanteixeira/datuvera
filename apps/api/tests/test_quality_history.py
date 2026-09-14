from datetime import datetime, timedelta, timezone
from sqlalchemy import event
from app.db.session import SessionLocal
from app.models.quality_run import QualityRun
from test_quality_runs import dataset


def test_history_limits_order_and_no_checks_query(dataset):
    client, root, schema, *_ = dataset
    source_id = int(root.split('/')[-1])
    start = datetime.now(timezone.utc)
    with SessionLocal() as db:
        db.add_all([QualityRun(source_id=source_id, schema_name=schema, table_name='customers',
                               overall_score=40+i, completeness_score=40+i, uniqueness_score=100,
                               validity_score=None, checks=[], created_at=start+timedelta(seconds=i))
                    for i in range(50)])
        db.commit()
        engine = db.get_bind()
        statements = []
        def capture(conn, cursor, statement, parameters, context, executemany):
            if 'from quality_runs' in statement.lower(): statements.append(statement.lower())
        event.listen(engine, 'before_cursor_execute', capture)
        try:
            for limit in [10, 20, 50]:
                response = client.get(root+'/quality-runs', params={'schema':schema,'table':'customers','limit':limit})
                assert response.status_code == 200
                rows = response.json()
                assert len(rows) == limit
                assert rows[0]['overall_score'] == 89
                assert rows[-1]['overall_score'] == 90-limit
                assert all('checks' not in row and row['validity_score'] is None for row in rows)
            assert len(statements) == 3
            assert all('quality_runs.checks' not in sql and 'limit' in sql and 'offset' in sql for sql in statements)
        finally:
            event.remove(engine, 'before_cursor_execute', capture)
