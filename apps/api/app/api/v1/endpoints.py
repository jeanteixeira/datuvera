from fastapi import APIRouter, Depends, HTTPException
from app.core.config import settings
from app.schemas.source import DataSourceCreate, DataSourceRead
from app.db.session import SessionLocal
from app.services.datasource_service import DataSourceService
from app.services.connectors.postgres_connector import PostgreSQLConnector
from fastapi import Body

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
    return DataSourceRead.from_orm(src)


@router.get("/sources")
def list_sources(db=Depends(get_db)):
    svc = DataSourceService(db)
    items = svc.list()
    return [DataSourceRead.from_orm(i) for i in items]


@router.get("/sources/{source_id}")
def get_source(source_id: int, db=Depends(get_db)):
    svc = DataSourceService(db)
    src = svc.get(source_id)
    if not src:
        raise HTTPException(status_code=404, detail="Not found")
    return DataSourceRead.from_orm(src)


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
