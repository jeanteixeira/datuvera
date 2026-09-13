from app.services.quality_rule_service import QualityRuleService
from app.ai.config import get_ai_provider
from app.ai.models import AIInsightRequest, AIInsightResult
from app.ai.engine import generate_insights
from app.ai.providers.base import AIProviderError
from fastapi import APIRouter, Depends, HTTPException
from app.core.config import settings
from app.schemas.source import DataSourceCreate, DataSourceRead
from app.db.session import SessionLocal
from app.services.datasource_service import DataSourceService
from app.services.connectors.postgres_connector import PostgreSQLConnector
from fastapi import Body
from app.profiling.engine import profile_table_from_source
from app.profiling.models import ProfileResponse
from app.quality.engine import run_quality
from app.services.connectors.postgres_connector import PostgreSQLConnector as Connector

router = APIRouter()


@router.get("/info")
def info():
    return {
        "name": settings.APP_NAME,
        "version": settings.VERSION,
        "description": settings.DESCRIPTION,
    }


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.post("/sources/test")
def test_connection(payload: DataSourceCreate = Body(...)):
    connector = PostgreSQLConnector(payload.host, payload.port, payload.database, payload.username, payload.password)
    res = connector.test_connection()
    if not res.get("success"):
        raise HTTPException(status_code=400, detail={"message": "Connection failed", "error": res.get("message")})
    return res


@router.post("/sources")
def create_source(payload: DataSourceCreate, db=Depends(get_db)):
    svc = DataSourceService(db)
    src = svc.create(payload.dict())
    # Use Pydantic v2 model_validate with from_attributes=True
    return DataSourceRead.model_validate(src)


@router.get("/sources")
def list_sources(db=Depends(get_db)):
    svc = DataSourceService(db)
    items = svc.list()
    return [DataSourceRead.model_validate(i) for i in items]


@router.get("/sources/{source_id}")
def get_source(source_id: int, db=Depends(get_db)):
    svc = DataSourceService(db)
    src = svc.get(source_id)
    if not src:
        raise HTTPException(status_code=404, detail="Not found")
    return DataSourceRead.model_validate(src)


@router.post("/sources/{source_id}/test")
def test_saved_source(source_id: int, db=Depends(get_db)):
    svc = DataSourceService(db)
    src = svc.get(source_id)
    if not src:
        raise HTTPException(status_code=404, detail="Not found")
    connector = PostgreSQLConnector(src.host, src.port, src.database, src.username, src.password)
    res = connector.test_connection()
    if not res.get("success"):
        raise HTTPException(status_code=400, detail={"message": "Connection failed", "error": res.get("message")})
    return res


@router.get("/sources/{source_id}/schemas")
def list_schemas(source_id: int, db=Depends(get_db)):
    svc = DataSourceService(db)
    src = svc.get(source_id)
    if not src:
        raise HTTPException(status_code=404, detail="Not found")
    connector = PostgreSQLConnector(src.host, src.port, src.database, src.username, src.password)
    try:
        schemas = connector.list_schemas()
        return schemas
    except Exception:
        raise HTTPException(status_code=500, detail="Failed to list schemas")


@router.get("/sources/{source_id}/schemas/{schema}/tables")
def list_tables(source_id: int, schema: str, db=Depends(get_db)):
    svc = DataSourceService(db)
    src = svc.get(source_id)
    if not src:
        raise HTTPException(status_code=404, detail="Not found")
    connector = PostgreSQLConnector(src.host, src.port, src.database, src.username, src.password)
    try:
        tables = connector.list_tables(schema)
        return tables
    except Exception:
        raise HTTPException(status_code=500, detail="Failed to list tables")



@router.post("/sources/{source_id}/profile", response_model=ProfileResponse)
def run_profile(source_id: int, payload: dict = Body(...), db=Depends(get_db)):
    svc = DataSourceService(db)
    src = svc.get(source_id)
    if not src:
        raise HTTPException(status_code=404, detail="Not found")
    schema = payload.get("schema")
    table = payload.get("table")
    if not schema or not table:
        raise HTTPException(status_code=400, detail="schema and table are required")
    try:
        res = profile_table_from_source(src, schema, table)
        return res
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail="Failed to profile table")


@router.post("/sources/{source_id}/quality")
def run_quality_endpoint(source_id: int, payload: dict = Body(...), db=Depends(get_db)):
    svc = DataSourceService(db)
    src = svc.get(source_id)
    if not src:
        raise HTTPException(status_code=404, detail="Not found")
    schema = payload.get("schema")
    table = payload.get("table")
    if not schema or not table:
        raise HTTPException(status_code=400, detail="schema and table are required")
    try:
        connector = Connector(src.host, src.port, src.database, src.username, src.password)
        res = run_quality(src, schema, table, connector, QualityRuleService(db).effective(source_id, schema, table))
        return res.dict()
    except Exception as e:
        raise HTTPException(status_code=500, detail="Failed to run quality")


@router.get("/ai/status")
def get_ai_status():
    from app.ai.config import ai_status
    return ai_status()


@router.post("/sources/{source_id}/insights", response_model=AIInsightResult)
def run_insights(source_id: int, payload: AIInsightRequest, db=Depends(get_db), provider=Depends(get_ai_provider)):
    if provider is None:
        raise HTTPException(status_code=503, detail="AI Insights is not configured.")
    source = DataSourceService(db).get(source_id)
    if not source:
        raise HTTPException(status_code=404, detail="Not found")
    try:
        profile = profile_table_from_source(source, payload.schema_name, payload.table)
        connector = Connector(source.host, source.port, source.database, source.username, source.password)
        quality = run_quality(source, payload.schema_name, payload.table, connector,
                              QualityRuleService(db).effective(source_id, payload.schema_name, payload.table))
    except ValueError:
        raise HTTPException(status_code=404, detail="Table not found") from None
    except Exception:
        raise HTTPException(status_code=500, detail="Failed to prepare dataset insights") from None
    try:
        return generate_insights(profile, quality, provider)
    except AIProviderError:
        raise HTTPException(status_code=502, detail="AI provider failed to generate valid insights.") from None
