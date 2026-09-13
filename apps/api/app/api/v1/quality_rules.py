from fastapi import APIRouter, Depends, HTTPException, Response, Query
from app.api.v1.endpoints import get_db
from app.schemas.quality_rule import QualityRuleCreate, QualityRulePatch, QualityRuleRead
from app.services.datasource_service import DataSourceService
from app.services.quality_rule_service import QualityRuleService, RuleValidationError

router = APIRouter(prefix='/sources/{source_id}/quality-rules', tags=['Quality Rules'])


def source_or_404(db, source_id):
    source = DataSourceService(db).get(source_id)
    if not source:
        raise HTTPException(404, 'Source not found')
    return source


def rule_or_404(service, source_id, rule_id):
    rule = service.get(source_id, rule_id)
    if not rule:
        raise HTTPException(404, 'Rule not found')
    return rule


@router.get('', response_model=list[QualityRuleRead])
def list_rules(source_id: int, schema: str | None = Query(None), table: str | None = Query(None), db=Depends(get_db)):
    source_or_404(db, source_id)
    return QualityRuleService(db).list(source_id, schema, table)


@router.post('', response_model=QualityRuleRead, status_code=201)
def create_rule(source_id: int, payload: QualityRuleCreate, db=Depends(get_db)):
    source = source_or_404(db, source_id)
    try:
        return QualityRuleService(db).create(source, payload)
    except RuleValidationError as error:
        raise HTTPException(400, str(error)) from None
    except Exception:
        db.rollback()
        raise HTTPException(500, 'Failed to create quality rule') from None


@router.patch('/{rule_id}', response_model=QualityRuleRead)
def patch_rule(source_id: int, rule_id: int, payload: QualityRulePatch, db=Depends(get_db)):
    source = source_or_404(db, source_id)
    service = QualityRuleService(db)
    rule = rule_or_404(service, source_id, rule_id)
    try:
        return service.patch(source, rule, payload)
    except RuleValidationError as error:
        raise HTTPException(400, str(error)) from None
    except Exception:
        db.rollback()
        raise HTTPException(500, 'Failed to update quality rule') from None


@router.delete('/{rule_id}', status_code=204)
def delete_rule(source_id: int, rule_id: int, db=Depends(get_db)):
    source_or_404(db, source_id)
    service = QualityRuleService(db)
    rule = rule_or_404(service, source_id, rule_id)
    service.delete(rule)
    return Response(status_code=204)
