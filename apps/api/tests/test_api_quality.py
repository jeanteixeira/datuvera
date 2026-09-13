from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_quality_endpoint_demo_source():
    # Assumes demo source exists in DB and has id 3 (previous setup used 3). Instead,
    # create a source via API pointing to demo DB and run quality.
    payload = {
        "name": "demo-src-quality",
        "type": "postgresql",
        "host": "datuvera-demo-db",
        "port": 5432,
        "database": "demo",
        "username": "demo",
        "password": "demo",
    }
    r = client.post('/api/v1/sources', json=payload)
    assert r.status_code == 200
    src = r.json()
    src_id = src['id']
    for column, rule, params in [('email', 'email_format', {}), ('state', 'allowed_values', {'values': ['AL','PE','BA','SP','RJ']})]:
        created = client.post(f'/api/v1/sources/{src_id}/quality-rules', json={'schema':'public','table':'customers','column':column,'rule':rule,'parameters':params})
        assert created.status_code == 201

    pr = client.post(f'/api/v1/sources/{src_id}/quality', json={'schema':'public','table':'customers'})
    assert pr.status_code == 200
    q = pr.json()
    assert 'score' in q
    assert 'dimensions' in q
    assert 'checks' in q

    assert 0 <= q['score'] <= 100
    again = client.post(f'/api/v1/sources/{src_id}/quality', json={'schema': 'public', 'table': 'customers'})
    assert again.json() == q
    products = client.post(f'/api/v1/sources/{src_id}/quality', json={'schema': 'public', 'table': 'products'})
    assert products.status_code == 200
    assert products.json()['dimensions']['validity'] is None
    assert products.json()['score'] == 100

    for check in q['checks']:
        assert check['score'] == 100 - check['failed_percentage']
        assert set(['column', 'rule', 'status', 'passed', 'failed_count', 'failed_percentage', 'score', 'message']).issubset(check)
    assert q['dimensions']['completeness'] == 99.33
    assert q['dimensions']['uniqueness'] == 100
    assert q['dimensions']['validity'] == 98
    assert q['score'] == 99.11
