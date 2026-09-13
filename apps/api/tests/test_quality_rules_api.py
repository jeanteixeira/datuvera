import os
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from pydantic import ValidationError
from sqlalchemy import create_engine, text
from sqlalchemy.engine import make_url
from sqlalchemy.sql.sqltypes import Integer, String

from app.main import app
from app.schemas.quality_rule import QualityRuleCreate
from app.services.quality_rule_service import validate_column, RuleValidationError


@pytest.mark.parametrize('rule,parameters', [
    ('not_null', {'extra': 1}), ('unique', {'value': 1}), ('email_format', {'regex': 'anything'}),
    ('allowed_values', {}), ('allowed_values', {'values': []}), ('allowed_values', {'values': [{}]}),
    ('allowed_values', {'values': [None]}), ('allowed_values', {'values': ['AL'], 'extra': 1}),
    ('min_value', {}), ('max_value', {}), ('min_value', {'value': True}),
    ('max_value', {'value': '10'}), ('min_value', {'value': float('inf')}), ('sql', {}),
])
def test_invalid_parameters(rule, parameters):
    with pytest.raises(ValidationError):
        QualityRuleCreate.model_validate({'schema':'public','table':'customers','column':'email','rule':rule,'parameters':parameters})


@pytest.mark.parametrize('rule,parameters', [('not_null', {}), ('unique', {}), ('email_format', {}),
                                            ('allowed_values', {'values': ['AL', 'PE']}), ('min_value', {'value':0}), ('max_value', {'value':100})])
def test_valid_parameters(rule, parameters):
    result = QualityRuleCreate.model_validate({'schema':'public','table':'customers','column':'email','rule':rule,'parameters':parameters})
    assert result.parameters == parameters


@pytest.mark.parametrize('dtype,rule,parameters', [(Integer(), 'email_format', {}), (String(), 'min_value', {'value':0}),
                                                 (Integer(), 'allowed_values', {'values':['AL']})])
def test_incompatible_column(dtype, rule, parameters):
    with pytest.raises(RuleValidationError):
        validate_column({'type':dtype}, rule, parameters)


@pytest.fixture
def dataset():
    client = TestClient(app)
    url = make_url(os.environ['DATABASE_URL'])
    engine = create_engine(url)
    schema = '_test_rules_' + uuid4().hex
    with engine.begin() as conn:
        conn.execute(text(f'CREATE SCHEMA "{schema}"'))
        conn.execute(text(f'CREATE TABLE "{schema}".customers (id integer PRIMARY KEY, email text, state text, value numeric)'))
        conn.execute(text(f"INSERT INTO \"{schema}\".customers VALUES (1,NULL,'AL',NULL), (2,'bad','AL',-1), (3,'a@example.com','XX',0), (4,'b@example.com','AL',10), (5,'c@example.com','AL',11)"))
    payload = {'name':'rules-test','host':url.host,'port':url.port or 5432,'database':url.database,
               'username':url.username,'password':url.password,'type':'postgresql'}
    source_a = client.post('/api/v1/sources', json=payload).json()['id']
    source_b = client.post('/api/v1/sources', json=payload).json()['id']
    root = f'/api/v1/sources/{source_a}'
    def create(column, rule, parameters=None, **extra):
        return client.post(root+'/quality-rules', json={'schema':schema,'table':'customers','column':column,
                                                      'rule':rule,'parameters':parameters or {}, **extra})
    try:
        yield client, root, schema, source_b, create
    finally:
        for rule in client.get(root+'/quality-rules').json():
            client.delete(root+f"/quality-rules/{rule['id']}")
        with engine.begin() as conn:
            conn.execute(text(f'DROP SCHEMA "{schema}" CASCADE'))
        engine.dispose()


def test_crud_ownership_and_parameters(dataset):
    client, root, schema, source_b, create = dataset
    response = create('value', 'min_value', {'value':0})
    assert response.status_code == 201
    rule = response.json()
    assert rule['schema']==schema and rule['table']=='customers' and rule['column']=='value'
    assert rule['rule']=='min_value' and rule['is_enabled'] is True
    assert rule['created_at'] and rule['updated_at']
    path = root+f"/quality-rules/{rule['id']}"
    assert client.get(root+'/quality-rules', params={'schema':schema,'table':'customers'}).json()==[rule]
    assert client.get(root+'/quality-rules', params={'table':'other'}).json()==[]
    assert client.patch(path, json={'parameters':{'value':10}}).json()['parameters']=={'value':10}
    assert client.patch(path, json={'is_enabled':False}).json()['is_enabled'] is False
    assert client.patch(path, json={'is_enabled':True}).json()['is_enabled'] is True
    assert client.patch(path, json={'parameters':{}}).status_code==400
    assert client.patch(path, json={'is_enabled':None}).status_code==422
    assert client.patch(path, json={'rule':'unique'}).status_code==422
    other=f'/api/v1/sources/{source_b}/quality-rules/{rule["id"]}'
    assert client.patch(other, json={'is_enabled':False}).status_code==404
    assert client.delete(other).status_code==404
    assert client.delete(path).status_code==204
    assert client.get(root+'/quality-rules').json()==[]


@pytest.mark.parametrize('column,rule,params,status', [('missing','not_null',{},400), ('email','min_value',{'value':0},400),
                                                     ('id','email_format',{},400), ('state','allowed_values',{'values':[1]},400)])
def test_invalid_dataset_column(dataset, column, rule, params, status):
    assert dataset[-1](column,rule,params).status_code==status


def test_nonexistent_source_schema_table(dataset):
    client, root, schema, _, _ = dataset
    payload={'schema':'missing_schema','table':'customers','column':'email','rule':'not_null','parameters':{}}
    assert client.post(root+'/quality-rules',json=payload).status_code==400
    payload['schema']=schema; payload['table']='missing_table'
    assert client.post(root+'/quality-rules',json=payload).status_code==400
    assert client.post('/api/v1/sources/2147483647/quality-rules',json=payload).status_code==404


def test_configured_rules_influence_quality_and_disable(dataset):
    client, root, schema, _, create = dataset
    payload={'schema':schema,'table':'customers'}
    before=client.post(root+'/quality',json=payload).json()
    assert before['dimensions']['validity'] is None
    email=create('email','email_format').json()
    after=client.post(root+'/quality',json=payload).json()
    assert after['dimensions']['validity']==80
    assert after['score']!=before['score']
    check=next(c for c in after['checks'] if c['rule']=='email_format')
    assert check['failed_count']==1 and check['score']==80
    client.patch(root+f"/quality-rules/{email['id']}",json={'is_enabled':False})
    disabled=client.post(root+'/quality',json=payload).json()
    assert disabled==before
    assert len(client.get(root+'/quality-rules').json())==1
    client.patch(root+f"/quality-rules/{email['id']}",json={'is_enabled':True})
    assert client.post(root+'/quality',json=payload).json()==after


@pytest.mark.parametrize('column,rule,params,failed_count,dimension', [
    ('state','allowed_values',{'values':['AL']},1,'validity'), ('value','min_value',{'value':0},1,'validity'),
    ('value','max_value',{'value':10},1,'validity'), ('state','unique',{},4,'uniqueness')])
def test_configured_rule_execution(dataset,column,rule,params,failed_count,dimension):
    client, root, schema, _, create=dataset
    assert create(column,rule,params).status_code==201
    result=client.post(root+'/quality',json={'schema':schema,'table':'customers'}).json()
    check=next(c for c in result['checks'] if c['rule']==rule and c['column']==column)
    assert check['failed_count']==failed_count
    assert check['score']==100-failed_count/5*100
    assert result['dimensions'][dimension] is not None


def test_deduplication_and_initially_disabled(dataset):
    client, root, schema, _, create=dataset
    payload={'schema':schema,'table':'customers'}
    before=client.post(root+'/quality',json=payload).json()
    for column,rule in [('id','unique'), ('email','not_null')]:
        assert create(column,rule).status_code==201
    create('email','email_format',is_enabled=False)
    assert client.post(root+'/quality',json=payload).json()==before
    create('email','email_format'); create('email','email_format')
    after=client.post(root+'/quality',json=payload).json()
    assert sum(c['rule']=='email_format' for c in after['checks'])==1


def test_allowed_value_is_parameterized(dataset):
    client, root, schema, _, create=dataset
    assert create('state','allowed_values',{'values':["AL'); DROP TABLE customers; --"]}).status_code==201
    result=client.post(root+'/quality',json={'schema':schema,'table':'customers'})
    assert result.status_code==200
    assert next(c for c in result.json()['checks'] if c['rule']=='allowed_values')['failed_count']==5
