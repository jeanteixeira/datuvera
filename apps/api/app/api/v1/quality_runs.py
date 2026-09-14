from fastapi import APIRouter, Depends, HTTPException, Query
from app.api.v1.endpoints import get_db
from app.api.v1.quality_rules import source_or_404
from app.schemas.quality_run import QualityRunSummary, QualityRunDetail
from app.services.quality_run_service import QualityRunService

router = APIRouter(prefix='/sources/{source_id}/quality-runs', tags=['Quality Runs'])


@router.get('', response_model=list[QualityRunSummary])
def list_runs(source_id: int, schema: str = Query(..., min_length=1), table: str = Query(..., min_length=1),
              limit: int = Query(20, ge=1, le=100), offset: int = Query(0, ge=0), db=Depends(get_db)):
    source_or_404(db, source_id)
    return QualityRunService(db).list(source_id, schema, table, limit, offset)


@router.get('/latest', response_model=QualityRunDetail)
def latest_run(source_id: int, schema: str = Query(..., min_length=1), table: str = Query(..., min_length=1), db=Depends(get_db)):
    source_or_404(db, source_id)
    run = QualityRunService(db).latest(source_id, schema, table)
    if run is None:
        raise HTTPException(404, 'Quality run not found')
    return run


@router.get('/{run_id}', response_model=QualityRunDetail)
def get_run(source_id: int, run_id: int, db=Depends(get_db)):
    source_or_404(db, source_id)
    run = QualityRunService(db).get(source_id, run_id)
    if run is None:
        raise HTTPException(404, 'Quality run not found')
    return run
