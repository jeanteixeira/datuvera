from sqlalchemy import create_engine, inspect, text
from sqlalchemy.exc import SQLAlchemyError
from typing import List, Dict, Any


class PostgreSQLConnector:
    def __init__(self, host: str, port: int, database: str, username: str, password: str, connect_timeout: int = 5):
        self.host = host
        self.port = port
        self.database = database
        self.username = username
        self.password = password
        self.connect_timeout = connect_timeout

    def _build_url(self) -> str:
        # Ensure SQLAlchemy uses the psycopg (v3) driver instead of trying psycopg2
        return f"postgresql+psycopg://{self.username}:{self.password}@{self.host}:{self.port}/{self.database}"

    def test_connection(self) -> Dict[str, Any]:
        try:
            engine = create_engine(self._build_url(), connect_args={"connect_timeout": self.connect_timeout})
            with engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            return {"success": True, "message": "Connection successful"}
        except SQLAlchemyError as e:
            return {"success": False, "message": str(e)}

    def list_schemas(self) -> List[str]:
        engine = create_engine(self._build_url())
        inspector = inspect(engine)
        schemas = [s for s in inspector.get_schema_names() if s not in ("pg_catalog", "information_schema")]
        return schemas

    def list_tables(self, schema: str) -> List[Dict[str, Any]]:
        engine = create_engine(self._build_url())
        inspector = inspect(engine)
        tables = inspector.get_table_names(schema=schema)
        result = [{"name": t, "schema": schema} for t in tables]
        return result
