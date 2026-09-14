from copy import deepcopy
import pytest
from sqlalchemy import select
from app.db.session import SessionLocal
from app.models.quality_run import QualityRun
from app.quality.models import QualityResult
from app.services.quality_run_service import QualityRunService
from test_quality_rules_api import dataset


def history(client, root, schema, **params):
    return client.get(root+'/quality-runs', params={'schema':schema,'table':'customers',**params})


def test_multiple_runs_snapshot_pagination_and_ownership(dataset):
    client,root,schema,other,create=dataset
    assert history(client,root,schema).json()==[]
    assert client.get(root+'/quality-runs/latest',params={'schema':schema,'table':'customers'}).status_code==404
    results=[client.post(root+'/quality',json={'schema':schema,'table':'customers'}) for _ in range(2)]
    assert all(r.status_code==200 for r in results)
    rows=history(client,root,schema).json()
    assert len(rows)==2 and rows[0]['id']>rows[1]['id']
    assert rows[0]['created_at']>=rows[1]['created_at']
    assert 'checks' not in rows[0]
    assert history(client,root,schema,limit=1,offset=1).json()==[rows[1]]
    assert client.get(root+'/quality-runs',params={'schema':schema,'table':'other'}).json()==[]
    assert client.get(root+'/quality-runs',params={'schema':'other','table':'customers'}).json()==[]
    detail=client.get(root+f"/quality-runs/{rows[0]['id']}").json()
    result=results[0].json()
    assert detail['source_id']==int(root.split('/')[-1]) and detail['schema']==schema and detail['table']=='customers'
    assert detail['overall_score']==result['score']
    assert detail['completeness_score']==result['dimensions']['completeness']
    assert detail['uniqueness_score']==result['dimensions']['uniqueness']
    assert detail['validity_score'] is None
    assert detail['checks']==result['checks']
    assert detail['created_at'].endswith('+00:00') or detail['created_at'].endswith('Z')
    assert client.get(root+'/quality-runs/latest',params={'schema':schema,'table':'customers'}).json()==detail
    assert client.get(f"/api/v1/sources/{other}/quality-runs/{detail['id']}").status_code==404
    assert client.get(root+'/quality-runs/2147483647').status_code==404
    assert client.patch(root+f"/quality-runs/{detail['id']}",json={}).status_code==405
    assert client.delete(root+f"/quality-runs/{detail['id']}").status_code==405


@pytest.mark.parametrize('params',[{}, {'schema':'s'}, {'schema':'s','table':'t','limit':0},
 {'schema':'s','table':'t','limit':101}, {'schema':'s','table':'t','offset':-1}, {'schema':'','table':'t'}])
def test_list_validation(dataset,params):
    client,root,*_=dataset
    assert client.get(root+'/quality-runs',params=params).status_code==422


def test_rule_changes_do_not_change_history(dataset):
    client,root,schema,_,create=dataset
    rule=create('email','email_format').json()
    first=client.post(root+'/quality',json={'schema':schema,'table':'customers'}).json()
    old=history(client,root,schema).json()[0]
    old_path=root+f"/quality-runs/{old['id']}"
    snapshot=client.get(old_path).json()
    client.patch(root+f"/quality-rules/{rule['id']}",json={'is_enabled':False})
    second=client.post(root+'/quality',json={'schema':schema,'table':'customers'}).json()
    assert any(c['rule']=='email_format' for c in first['checks'])
    assert not any(c['rule']=='email_format' for c in second['checks'])
    assert client.get(old_path).json()==snapshot
    assert snapshot['checks']==first['checks']
    assert len(history(client,root,schema).json())==2


@pytest.mark.parametrize('failure',['engine','persist'])
def test_failed_execution_does_not_report_success(dataset,monkeypatch,failure):
    client,root,schema,*_=dataset
    def fail(*args,**kwargs): raise RuntimeError('private database password should not leak')
    if failure=='engine': monkeypatch.setattr('app.api.v1.endpoints.run_quality',fail)
    else: monkeypatch.setattr(QualityRunService,'persist',fail)
    response=client.post(root+'/quality',json={'schema':schema,'table':'customers'})
    assert response.status_code==500 and response.json()=={'detail':'Failed to run quality'}
    assert history(client,root,schema).json()==[]


def test_service_rollback_and_controlled_snapshot(dataset,monkeypatch):
    client,root,schema,*_=dataset
    source_id=int(root.split('/')[-1])
    result=QualityResult(dataset={'source_id':source_id,'schema':schema,'table':'customers'},score=0,
                         dimensions={'completeness':None,'uniqueness':None,'validity':None},summary={},checks=[])
    with SessionLocal() as db:
        service=QualityRunService(db)
        run=service.persist(source_id,schema,'customers',result)
        assert run.overall_score==0 and run.completeness_score is None and run.checks==[]
        before=deepcopy(run.checks)
        result.dataset['password']='not part of snapshot'
        result.checks.clear()
        assert run.checks==before
        def fail(): raise RuntimeError('commit failed')
        monkeypatch.setattr(db,'commit',fail)
        with pytest.raises(RuntimeError): service.persist(source_id,schema,'customers',result)
        assert len(db.scalars(select(QualityRun).where(QualityRun.source_id==source_id)).all())==1
