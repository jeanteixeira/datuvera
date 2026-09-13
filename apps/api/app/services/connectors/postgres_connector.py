from sqlalchemy import create_engine, inspect, text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.engine import URL
from typing import List, Dict, Any


class PostgreSQLConnector:
    def __init__(self, host: str, port: int, database: str, username: str, password: str, connect_timeout: int = 5):
        self.host = host
        self.port = port
        self.database = database
        self.username = username
        self.password = password
        self.connect_timeout = connect_timeout

    def _build_url(self) -> URL:
        # Ensure SQLAlchemy uses the psycopg (v3) driver instead of trying psycopg2
        return URL.create("postgresql+psycopg", username=self.username, password=self.password, host=self.host, port=self.port, database=self.database)

    def test_connection(self) -> Dict[str, Any]:
        try:
            engine = create_engine(self._build_url(), connect_args={"connect_timeout": self.connect_timeout})
            with engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            return {"success": True, "message": "Connection successful"}
        except SQLAlchemyError as e:
            return {"success": False, "message": "Connection failed"}

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

    def get_primary_key_columns(self, schema: str, table: str) -> List[str]:
        engine = create_engine(self._build_url())
        inspector = inspect(engine)
        # SQLAlchemy inspector uses get_pk_constraint
        pk = inspector.get_pk_constraint(table, schema=schema)
        return pk.get('constrained_columns', []) if pk else []

    def get_unique_constraints(self, schema: str, table: str) -> List[Dict[str, Any]]:
        engine = create_engine(self._build_url())
        inspector = inspect(engine)
        return inspector.get_unique_constraints(table, schema)

    @property
    def engine(self):
        return create_engine(self._build_url())
