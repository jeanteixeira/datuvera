from typing import List, Optional
from sqlalchemy.orm import Session
from app.models.datasource import DataSource


class DataSourceService:
    def __init__(self, db: Session):
        self.db = db

    def create(self, obj_in: dict) -> DataSource:
        src = DataSource(**obj_in)
        self.db.add(src)
        self.db.commit()
        self.db.refresh(src)
        return src

    def list(self) -> List[DataSource]:
        return self.db.query(DataSource).all()

    def get(self, id: int) -> Optional[DataSource]:
        return self.db.query(DataSource).filter(DataSource.id == id).first()
